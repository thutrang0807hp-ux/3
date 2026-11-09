"""Browser image adapters for user-owned chat sessions; one send, isolated jobs, configurable image slots, no automatic replay.

Uses Playwright and isolated storage_state, not API keys or fingerprint modification.
Login and generation must be verified on the user's actual service UI.
"""
import asyncio,base64,hashlib,importlib.util,io,json,os,re,shutil,time,uuid
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import HTTPException
from fastapi.responses import FileResponse
from PIL import Image
from .account_pool import AccountPool
from .admission import guarded_submission
from .image_slots import ImageSlots
from .batch_images import BatchImages
from .request_ledger import NO_RESULT,RequestConflict

SITES={
 'chatgpt':{'name':'ChatGPT Chat','url':'https://chatgpt.com/','editor':'#prompt-textarea,textarea[data-id="root"],textarea[placeholder*="Message"]','send':'button[data-testid="send-button"],button[aria-label="Send prompt"],button[aria-label="Send message"]','images':'[data-message-author-role="assistant"] img[alt*="generated" i],[data-message-author-role="assistant"] img[alt*="created" i],[data-message-author-role="assistant"] img[alt*="Image" i]','domains':['chatgpt.com','openai.com','oaiusercontent.com']},
 'grok':{'name':'Grok Chat','url':'https://grok.com/','editor':'textarea[placeholder],div[contenteditable="true"][role="textbox"]','send':'button[aria-label="Submit"],button[aria-label="Send message"],button[type="submit"]','images':'[data-testid="message-bubble-bot"] img,[data-role="assistant"] img,img[alt*="generated" i]','domains':['grok.com','x.ai','x.com','twimg.com']},
 'meta':{'name':'Meta AI','url':'https://www.meta.ai/','editor':'div[contenteditable="true"][role="textbox"],textarea[placeholder]','send':'button[aria-label="Send message"],div[role="button"][aria-label="Send"],button[type="submit"]','images':'[data-testid="assistant-message"] img,img[alt*="generated" i],img[alt*="Imagine" i]','domains':['meta.ai','fbcdn.net','facebook.com']},
}

def browser_options(headless=False):
 options={'headless':headless}
 executable=os.environ.get('SCENEFORGE_BROWSER') or (shutil.which('chromium')if os.name!='nt'else None)
 if executable:options['executable_path']=executable
 # Playwright installed Chromium is the fallback; never download during a job.
 return options

def allowed(url,site):
 host=urlsplit(url).hostname or''
 return urlsplit(url).scheme=='https'and any(host==d or host.endswith('.'+d)for d in site['domains'])

def browser_runtime():
 installed=bool(importlib.util.find_spec('playwright'))
 executable=os.environ.get('SCENEFORGE_BROWSER')or shutil.which('chromium')or shutil.which('chrome')
 roots=[Path(os.environ['PLAYWRIGHT_BROWSERS_PATH'])]if os.environ.get('PLAYWRIGHT_BROWSERS_PATH')not in (None,'0')else[Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.cache')))/'ms-playwright']
 candidates=[Path(executable)]if executable else[]
 for root in roots:
  for pattern in ('chromium-*/chrome-linux/chrome','chromium-*/chrome-linux64/chrome','chromium-*/chrome-win/chrome.exe','chromium-*/chrome-win64/chrome.exe','chromium_headless_shell-*/chrome-linux/headless_shell','chromium_headless_shell-*/chrome-linux64/chrome-headless-shell'):
   candidates.extend(root.glob(pattern))
 ready=installed and any(p.is_file()for p in candidates)
 return {'playwright_installed':installed,'browser_installed':ready}

class WebImageRejected(Exception):
 def __init__(self,reason):
  self.reason=reason
  super().__init__(reason)

def filtered_state(state,site):
 # Keep only the chat service's own session, not Google/Facebook SSO sessions or CDN cookies.
 host=urlsplit(site['url']).hostname.removeprefix('www.')
 def belongs(domain):return domain.lstrip('.')==host or domain.lstrip('.').endswith('.'+host)
 return {'cookies':[c for c in state.get('cookies',[])if belongs(c.get('domain',''))],
         'origins':[o for o in state.get('origins',[])if allowed(o.get('origin',''),{'domains':[host]})]}

def conversation_url(url,site):
 parsed=urlsplit(url);host=urlsplit(site['url']).hostname
 if parsed.scheme!='https'or parsed.hostname!=host or parsed.username or parsed.password:return None
 if parsed.path in ('','/'):return None
 if re.search(r'/(?:auth|login|signin)(?:/|$)',parsed.path,re.I):return None
 return parsed._replace(query='',fragment='').geturl()[:2048]

class WebImages:
 def __init__(self,vault,data,ledger,runner=None,sites=None):
  self.vault,self.ledger=vault,ledger;self.data=Path(data);self.root=Path(data)/'web-image-results';self.root.mkdir(exist_ok=True,mode=0o700)
  self.sites=sites or SITES;self.runner=runner or self.generate;self.tasks={};self.locks={};self.assignments={};self.logins={};self.total=asyncio.Semaphore(4);self.image_slots={source:ImageSlots(vault,source)for source in self.sites}
  for account in vault.rows('accounts'):
   if account.get('service')in self.sites:
    key='web-image-session:'+account['id'];stored=vault.secret(key)
    if stored:
     clean=filtered_state(stored,self.sites[account['service']])
     if clean!=stored:vault.set_secret(key,clean)
 def source(self,name):
  if name not in self.sites:raise HTTPException(400,'Nguồn chat không hợp lệ.')
  return self.sites[name]
 def status(self,source):
  site=self.source(source);pool=AccountPool(self.vault,source);choice=pool.status()
  return {'adapter':True,'configured':choice['available'],'installed':bool(importlib.util.find_spec('playwright')),**browser_runtime(),'source':source,'service_url':site['url'],'selection':choice,'accounts':pool.rows(),'per_account':self.image_slots[source].limit(),'max_concurrency':4,**self.image_slots[source].status(),'generation_verified':any(a.get('generation_verified')for a in pool.rows()),'automatic_retry':False,'browser_required':True,'reason':'Đăng nhập trên trang dịch vụ bằng trình duyệt riêng; chưa chứng nhận UI dịch vụ thật.'}
 async def new_browser(self,headless=False):
  from playwright.async_api import async_playwright
  pw=await async_playwright().start()
  try:browser=await pw.chromium.launch(**browser_options(headless))
  except Exception:
   await pw.stop();raise HTTPException(409,'Chưa mở được Chromium. Cài trình duyệt qua local_engine/install-chat-browser.bat; không gửi yêu cầu tạo ảnh.')from None
  return pw,browser
 async def login(self,source,name,account_id=None):
  site=self.source(source)
  if not isinstance(name,str)or not 1<=len(name.strip())<=80:raise HTTPException(400,'Nhập tên tài khoản để phân biệt.')
  if len(self.logins)>=5:raise HTTPException(409,'Đóng hoặc lưu cửa sổ đăng nhập đang mở trước.')
  from .browser_profiles import profiles
  manager=profiles(self.vault,self.data);entry=manager.reserve(source,account_id)
  if account_id in self.assignments.values():raise HTTPException(409,'Đợi tác vụ hiện tại trước khi mở profile.')
  stored=self.vault.secret('web-image-session:'+account_id)if account_id else None
  pw,browser=await manager.browser(entry,filtered_state(stored,site)if stored else None);context=await browser.new_context();page=await context.new_page()
  try:await page.goto(site['url'],wait_until='domcontentloaded',timeout=60000)
  except Exception:await browser.close();await pw.stop();raise HTTPException(502,'Chưa mở được trang đăng nhập. Chưa gửi prompt.')from None
  lid=str(uuid.uuid4());self.logins[lid]={'source':source,'name':name.strip(),'pw':pw,'browser':browser,'context':context,'page':page,'at':time.time(),'profile_entry':entry,'account_id':account_id};return {'login_id':lid,'message':'Đăng nhập trong cửa sổ vừa mở, rồi bấm Lưu phiên. Không nhập mật khẩu vào SceneForge.'}
 async def authenticated(self,page,context,site):
  if not allowed(page.url,site):return False
  editor=page.locator(site['editor']).first
  if not await editor.is_visible():return False
  if await page.get_by_role('button',name=re.compile(r'^(Log in|Sign in|Đăng nhập)$',re.I)).count():return False
  cookies=await context.cookies();return any(re.search(r'session|auth|sso|c_user|abra',c['name'],re.I)for c in cookies)
 async def page_rejection(self,page,context,site):
  parsed=urlsplit(page.url)
  login=page.get_by_role('button',name=re.compile(r'^(Log in|Sign in|Đăng nhập)$',re.I))
  if re.search(r'/(?:auth/login|login|signin)(?:/|$)',parsed.path,re.I):return 'auth'
  for i in range(await login.count()):
   if await login.nth(i).is_visible():return 'auth'
  alerts=page.locator('[role="alert"],[data-testid="rate-limit-message"]')
  for i in range(await alerts.count()):
   if not await alerts.nth(i).is_visible():continue
   text=await alerts.nth(i).inner_text()
   if re.search(r"(?:reached|exceeded).{0,60}(?:image|generation|usage).{0,30}limit|(?:image|generation|usage).{0,30}limit.{0,30}(?:reached|exceeded)|hết (?:lượt|hạn mức)|đã đạt giới hạn",text,re.I):return 'quota'
  return None
 def reject_account(self,aid,reason):
  with self.vault.lock:
   row=self.row(aid)
   row.update(state={'auth':'expired','quota':'exhausted'}.get(reason,'verification'),last_error={'auth':'Cần đăng nhập lại','quota':'Dịch vụ báo hết lượt','verification':'Cần kiểm tra giao diện/phiên'}[reason],checked_at=time.time())
   if reason!='quota':row['session_verified']=False
   self.vault.put('accounts',row)
 async def require_session(self,page,context,site):
  reason=await self.page_rejection(page,context,site)
  if reason:raise WebImageRejected(reason)
  if not await self.authenticated(page,context,site):raise WebImageRejected('verification')
 def trace(self,rid,page,site):
  url=conversation_url(page.url,site)
  if url and self.ledger.metadata(rid).get('conversation_url')!=url:self.ledger.set_metadata(rid,{'conversation_url':url})
 async def save_login(self,lid):
  entry=self.logins.get(lid)
  if not entry:raise HTTPException(404,'Cửa sổ đăng nhập đã đóng.')
  site=self.source(entry['source'])
  if not await self.authenticated(entry['page'],entry['context'],site):raise HTTPException(409,'Chưa xác nhận được phiên đăng nhập và ô chat. Hoàn tất đăng nhập trong cửa sổ dịch vụ trước.')
  aid=entry.get('account_id')or str(uuid.uuid4());rows=AccountPool(self.vault,entry['source']).rows();state=await entry['context'].storage_state()
  self.vault.set_secret('web-image-session:'+aid,filtered_state(state,site))
  previous=next((r for r in rows if r['id']==aid),{})
  row={**previous,'id':aid,'service':entry['source'],'name':entry['name'],'enabled':True,'state':'ready','active':previous.get('active',not rows),'priority':previous.get('priority',len(rows)),'session_verified':True,'generation_verified':previous.get('generation_verified',False),'checked_at':time.time(),'credit':previous.get('credit'),'successes':previous.get('successes',0),'failures':previous.get('failures',0)}
  self.vault.put('accounts',row)
  if entry.get('profile_entry'):
   from .browser_profiles import profiles
   profiles(self.vault,self.data).bind(entry['profile_entry'],aid)
  await self.close_login(lid);return {'id':aid,'saved':True,'generation_verified':False}
 async def close_login(self,lid):
  entry=self.logins.pop(lid,None)
  if entry:
   await entry['browser'].close();await entry['pw'].stop()
   if entry.get('profile_entry'):
    from .browser_profiles import profiles
    await profiles(self.vault,self.data).discard(entry['profile_entry'])
 def row(self,aid):
  row=next((r for r in self.vault.rows('accounts')if r['id']==aid and r.get('service')in self.sites),None)
  if not row:raise HTTPException(404,'Không có tài khoản chat tạo ảnh.')
  return row
 async def check(self,aid):
  if aid in self.assignments.values():raise HTTPException(409,'Đợi tác vụ ảnh hoàn tất trước khi kiểm tra lại phiên.')
  row=self.row(aid);site=self.source(row['service']);state=self.vault.secret('web-image-session:'+aid)
  if not state:raise HTTPException(409,'Chưa có phiên được lưu.')
  from .browser_profiles import profiles
  manager=profiles(self.vault,self.data);entry=manager.reserve(row['service'],aid)
  pw,browser=await manager.browser(entry,filtered_state(state,site))
  try:
   context=await browser.new_context(storage_state=filtered_state(state,site));page=await context.new_page();await page.goto(site['url'],wait_until='domcontentloaded',timeout=60000)
   await self.require_session(page,context,site)
   updated=filtered_state(await context.storage_state(),site)
   if aid in self.assignments.values() or self.vault.secret('web-image-session:'+aid)!=state:raise HTTPException(409,'Phiên đang được công việc khác dùng hoặc đã đổi; giữ phiên mới nhất.')
   self.vault.set_secret('web-image-session:'+aid,updated);row=self.row(aid);row.update(session_verified=True,state='exhausted'if row['state']=='exhausted'else'ready',checked_at=time.time());self.vault.put('accounts',row);return {'ok':True,'generation_verified':bool(row.get('generation_verified'))}
  except WebImageRejected as e:
   self.reject_account(aid,e.reason);raise HTTPException(409,'Phiên cần đăng nhập/xác minh hoặc dịch vụ đã báo hết lượt; chưa gửi prompt.')from None
  finally:await browser.close();await pw.stop()
 def remove(self,aid):
  self.row(aid)
  if aid in self.assignments.values():raise HTTPException(409,'Tài khoản còn việc đã nhận; đợi đối soát trước khi gỡ.')
  self.vault.delete_secret('web-image-session:'+aid);self.vault.delete('accounts',aid)
 @staticmethod
 def valid_id(rid):
  if not isinstance(rid,str)or not re.fullmatch(r'webimage-[a-f0-9-]{36}',rid):raise HTTPException(400,'Mã lượt tạo ảnh không hợp lệ.')
  try:uuid.UUID(rid[9:])
  except ValueError:raise HTTPException(400,'Mã lượt tạo ảnh không hợp lệ.')
 def lookup(self,rid):
  self.valid_id(rid)
  with self.ledger.connect()as db:row=db.execute('SELECT state,result FROM request WHERE id=?',(rid,)).fetchone()
  if not row:raise HTTPException(404,'Không tìm thấy lượt đã gửi trong kho hiện tại; không tự gửi lại.')
  return {**self.ledger.receipt(rid),'state':row[0],'result':json.loads(row[1])if row[0]=='done'else None,'automatic_retry':False,'conversation_url':self.ledger.metadata(rid).get('conversation_url'),'error_code':self.ledger.metadata(rid).get('error_code')}
 @guarded_submission
 async def submit(self,body):
  rid=body.get('request_id');self.valid_id(rid);source=body.get('source');self.source(source)
  prompt=body.get('prompt');refs=body.get('references',[])
  if body.get('confirm_send')is not True:raise HTTPException(409,'Rà và xác nhận trước khi gửi chat tạo ảnh.')
  if not isinstance(prompt,str)or not prompt.strip()or len(prompt)>20000 or body.get('kind','image')!='image':raise HTTPException(400,'Chỉ tạo ảnh; prompt tối đa 20.000 ký tự.')
  if not isinstance(refs,list)or len(refs)>8 or sum(BatchImages.decode_image(r)for r in refs)>24*1024**2:raise HTTPException(400,'Tối đa 8 ảnh tham khảo, tổng 24 MB.')
  if body.get('aspect','9:16')not in ('9:16','16:9','1:1','4:5'):raise HTTPException(400,'Tỉ lệ ảnh không hợp lệ.')
  pool=AccountPool(self.vault,source);choice=pool.status()
  if not choice['available']or body.get('selection_token')!=choice['token']:raise HTTPException(409,'Chọn/kiểm tài khoản và rà lại lựa chọn trước khi gửi.')
  if len(self.tasks)>=30:raise HTTPException(429,'Hàng chờ chat đầy; chưa gửi thêm.')
  # Selection chooses an account for a new job, never retries an old job elsewhere.
  aid=min(choice['permitted'],key=lambda a:list(self.assignments.values()).count(a))if choice['mode']=='balanced'else choice['permitted'][0]
  payload={'kind':'image','source':source,'account_id':aid,'prompt':prompt,'references':refs,'aspect':body.get('aspect','9:16'),'selection_token':choice['token'],'room_id':str(body.get('room_id')or body.get('product_id')or'')[:100],'scene_id':str(body.get('scene_id',''))[:100]}
  try:_,cached=self.ledger.claim(rid,payload)
  except (ValueError,RequestConflict)as e:raise HTTPException(409,str(e))from None
  if cached is not NO_RESULT:return self.lookup(rid)
  self.assignments[rid]=aid;self.tasks[rid]=asyncio.create_task(self.run(rid,payload));self.tasks[rid].add_done_callback(lambda t:self.tasks.pop(rid,None));return self.lookup(rid)
 async def run(self,rid,payload):
  state='failed';result=None;partial=self.root/(rid+'.partial');aid=payload['account_id']
  try:
   async with self.image_slots[payload['source']].slot(aid),self.total:
    row=self.row(aid)
    if not AccountPool.eligible(row):raise ValueError('Account disabled before dispatch')
    self.ledger.set_metadata(rid,{'provider':'web-images','source':payload['source'],'account_id':aid,'room_id':payload['room_id'],'scene_id':payload['scene_id']})
    if self.ledger.storage:self.ledger.storage.reserve_download(rid,24*1024**2)
    # Worker callback marks the exact moment a click may have reached the service.
    def sent():
     nonlocal state
     state='unknown';self.ledger.set_metadata(rid,{'dispatched':True})
    returned=await self.runner(rid,payload,partial,sent)
    paths=returned if isinstance(returned,list)else[partial]
    if not 1<=len(paths)<=8:raise ValueError('Invalid image count')
    outputs=[];total=0
    for index,path in enumerate(paths):
     path=Path(path)
     if path.parent!=self.root or path.name not in {rid+'.partial',rid+'.'+str(index)+'.partial'}:raise ValueError('Invalid result path')
     raw=path.read_bytes();total+=len(raw)
     if not 0<len(raw)<=24*1024**2 or total>96*1024**2:raise ValueError('Image too large')
     with Image.open(io.BytesIO(raw))as image:
      if image.width*image.height>40_000_000:raise ValueError('Image too large')
      fmt=image.format;image.verify()
     ext,mime={'PNG':('.png','image/png'),'JPEG':('.jpg','image/jpeg'),'WEBP':('.webp','image/webp')}[fmt]
     name=rid+(''if index==0 else'.'+str(index))+ext;os.replace(path,self.root/name)
     outputs.append({'file':name,'mime_type':mime,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    result={**outputs[0],'images':outputs,'kind':'image','origin':payload['source'],'model':payload['source']+'-chat-browser','account_id':aid,'cost':None};state='done'
    with self.vault.lock:
     row=self.row(aid);row.update(generation_verified=True,generation_verified_at=time.time(),successes=row.get('successes',0)+1,last_used_at=time.time());self.vault.put('accounts',row)
  except asyncio.CancelledError:raise
  except WebImageRejected as e:
   self.reject_account(aid,e.reason);self.ledger.set_metadata(rid,{'error_code':{'auth':'AUTH_REQUIRED','quota':'QUOTA_EXHAUSTED','verification':'VERIFICATION_REQUIRED'}[e.reason]})
  except Exception:
   self.ledger.set_metadata(rid,{'error_code':'RESULT_UNCERTAIN'if state=='unknown'else'NOT_SENT'})
  finally:
   for path in self.root.glob(rid+'*.partial'):path.unlink(missing_ok=True)
   partial.unlink(missing_ok=True);self.assignments.pop(rid,None);self.ledger.finish(rid,state,result)
   if state=='done'and result:
    for image in result.get('images',[]):
     if image.get('result_hash'):(self.root/image['file']).unlink(missing_ok=True)
   self.vault.put('logs',{'id':rid,'service':payload['source'],'kind':'Chat image','state':state,'account_id':aid,'room_id':payload['room_id'],'scene_id':payload['scene_id'],'at':time.time(),'cost':None,'code':'DONE'if state=='done'else'CHECK_BEFORE_RESUBMIT'})
 async def generate(self,rid,payload,output,sent):
  from tempfile import TemporaryDirectory
  site=self.source(payload['source']);stored=self.vault.secret('web-image-session:'+payload['account_id'])
  if not stored:raise ValueError('Missing stored session')
  from .browser_profiles import profiles
  manager=profiles(self.vault,self.data);entry=manager.reserve(payload['source'],payload['account_id'])
  pw,browser=await manager.browser(entry,filtered_state(stored,site))
  try:
   context=await browser.new_context(storage_state=filtered_state(stored,site));page=await context.new_page();await page.goto(site['url'],wait_until='domcontentloaded',timeout=60000)
   await self.require_session(page,context,site)
   editor=page.locator(site['editor']).first;button=page.locator(site['send']).first
   before=await page.locator(site['images']).evaluate_all('(nodes)=>nodes.map(n=>n.currentSrc||n.src)')
   with TemporaryDirectory(prefix='sf-image-refs-')as tmp:
    paths=[]
    for i,ref in enumerate(payload['references']):
     path=Path(tmp)/(str(i)+{'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[ref['mime_type']]);path.write_bytes(base64.b64decode(ref['data'],validate=True));paths.append(str(path))
    if paths:
     upload=page.locator('input[type="file"]').first
     if not await upload.count():raise ValueError('Image upload input unavailable')
     await upload.set_input_files(paths,timeout=20000)
    await editor.fill('Create exactly one image, aspect '+payload['aspect']+'. '+payload['prompt'])
    await button.wait_for(state='visible',timeout=15000)
    sent();await button.click(timeout=15000) # never click again after timeout
    previous=None;stable=0
    for _ in range(180):
     self.trace(rid,page,site)
     reason=await self.page_rejection(page,context,site)
     if reason:raise WebImageRejected(reason)
     current=await page.locator(site['images']).evaluate_all('(nodes)=>nodes.filter(n=>n.complete&&n.naturalWidth>=128&&n.naturalHeight>=128).map(n=>n.currentSrc||n.src)')
     fresh=list(dict.fromkeys(url for url in current if url and url not in before))
     busy=await page.locator('button[data-testid="stop-button"],button[aria-label="Stop generating"],[data-generation-state="pending"]').count()
     signature=tuple(fresh)
     stable=stable+1 if signature==previous and fresh and not busy else 0;previous=signature
     if fresh and stable>=3:
      if len(fresh)>8:raise ValueError('Too many images; inspect conversation')
      paths=[];total=0
      for index,url in enumerate(fresh):
       if not url.startswith(('blob:','data:image/'))and not allowed(url,site):raise ValueError('Untrusted result URL')
       raw=await page.evaluate('''async url=>{const r=await fetch(url,{credentials:'include'});if(!r.ok)throw Error('download');const reader=r.body.getReader(),chunks=[];let size=0;while(true){const v=await reader.read();if(v.done)break;size+=v.value.length;if(size>24*1024*1024){await reader.cancel();throw Error('size');}chunks.push(v.value);}let text='';for(const c of chunks)for(let i=0;i<c.length;i+=8192)text+=String.fromCharCode(...c.subarray(i,i+8192));return btoa(text);}''',url)
       decoded=base64.b64decode(raw,validate=True);total+=len(decoded)
       if total>96*1024**2:raise ValueError('Result group too large')
       if self.ledger.storage:self.ledger.storage.reserve_download(rid,total)
       path=output if index==0 else self.root/(rid+'.'+str(index)+'.partial');path.write_bytes(decoded);paths.append(path)
      self.trace(rid,page,site)
      if self.image_slots[payload['source']].limit()==1 and self.vault.secret('web-image-session:'+payload['account_id'])==stored:
       self.vault.set_secret('web-image-session:'+payload['account_id'],filtered_state(await context.storage_state(),site))
      return paths
     await asyncio.sleep(2)
    raise ValueError('No completed image group; inspect conversation')
  finally:await browser.close();await pw.stop()
 def file(self,rid,index=0):
  record=self.lookup(rid);result=record['result']or{};images=result.get('images')or[result]
  if record['state']!='done'or not 0<=index<len(images):raise HTTPException(404,'Chưa có ảnh đã lưu; không tự tạo lại.')
  result=images[index];name=result.get('file');expected={rid+(''if index==0 else'.'+str(index))+ext for ext in ('.png','.jpg','.webp')}
  if name not in expected:raise HTTPException(404,'Mã ảnh không hợp lệ.')
  if self.ledger.storage and result.get('result_hash'):
   stored=self.ledger.storage.lib.read_asset_path(result['result_hash'])
   if stored.is_file():return FileResponse(stored,media_type=result['mime_type'])
  if not(self.root/name).is_file():raise HTTPException(404,'Ảnh không còn trong kho.')
  return FileResponse(self.root/name,media_type=result['mime_type'])
 async def close(self):
  for lid in list(self.logins):await self.close_login(lid)
  for task in list(self.tasks.values()):task.cancel()
  await asyncio.gather(*list(self.tasks.values()),return_exceptions=True)

def install_web_images(app,vault,data,ledger):
 service=WebImages(vault,data,ledger)
 @app.get('/local-api/web-images/{source}/status')
 async def status(source:str):return service.status(source)
 @app.post('/local-api/web-images/{source}/concurrency')
 async def concurrency(source:str,body:dict):
  service.source(source)
  busy=any(service.row(aid)['service']==source for aid in service.assignments.values())
  return service.image_slots[source].configure(body,busy)
 @app.post('/local-api/web-images/{source}/login')
 async def login(source:str,body:dict):return await service.login(source,body.get('name'),body.get('account_id'))
 @app.post('/local-api/web-images/login/{lid}/save')
 async def save(lid:str):return await service.save_login(lid)
 @app.post('/local-api/web-images/login/{lid}/close')
 async def close(lid:str):await service.close_login(lid);return {'closed':True}
 @app.post('/local-api/web-images/{source}/selection')
 async def select(source:str,body:dict):
  service.source(source)
  if body.get('mode')not in ('selected','balanced'):raise HTTPException(400,'Nguồn chat hỗ trợ dùng riêng hoặc chia việc; không tự thử lại tài khoản khác.')
  return AccountPool(vault,source).select(body)
 @app.post('/local-api/web-images/jobs')
 async def submit(body:dict):return await service.submit(body)
 @app.get('/local-api/web-images/jobs/{rid}')
 async def lookup(rid:str):return service.lookup(rid)
 @app.get('/local-api/web-images/files/{rid}')
 async def file(rid:str,index:int=0):return service.file(rid,index)
 return service
