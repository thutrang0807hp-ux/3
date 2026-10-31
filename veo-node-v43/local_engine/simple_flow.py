"""Single-session, user-confirmed Flow path; no engine, extension or cookie export."""
import asyncio,base64,hashlib,io,json,re,secrets,time
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse
from .request_ledger import NO_RESULT,RequestConflict
from .admission import guarded_submission
from .simple_flow_upload import upload_reference

MODEL='veo-3.1-lite-i2v-8s-portrait'
class SimpleStopped(RuntimeError):pass

class SimpleFlow:
 def __init__(self,data,vault,ledger):
  self.data=Path(data);self.vault=vault;self.ledger=ledger
  self.root=self.data/'flow-results';self.root.mkdir(exist_ok=True)
  self.context=self.pw=self.page=self.login_process=None
  self.channel='msedge';self.email=None;self.connected=False;self.token=secrets.token_hex(24)
  self.task=None;self.tasks={};self.pending=None;self.reply=None;self.sent=False
  self.active=None;self.project=None;self.state='idle';self.message='Chưa kết nối Flow đơn giản.'
  self.gate=asyncio.Lock();self.download_waiter=None;self.download_task=None
 def enabled(self):return (self.vault.secret('flow-transport-v2')or{}).get('mode','simple')=='simple'
 def status(self):
  return {'state':self.state,'message':self.message,'interaction':self.pending,'active_request':self.active,'unresolved':self.unresolved(),
   'configured':True,'account_binding':self.connected,'transport':'web_ui','connection_method':'simple_flow',
   'models':[MODEL],'model_details':[{'id':MODEL,'description':'Lite · 8s · 9:16 · xác nhận trên Flow','accepts_images':True,'video_type':'i2v','max_images':1}],
   'per_account':1,'automatic_retry':False,'generation_verified':bool(self.vault.secret('simple-flow-verified')),
   'selection':{'mode':'selected','account_id':self.account_id(),'account_name':self.email or 'Flow · phiên đã xác nhận','available':bool(self.connected and self.page and not self.page.is_closed()),'token':self.token}}
 def unresolved(self):
  with self.ledger.connect()as db:
   rows=db.execute("SELECT r.id,m.metadata FROM request r JOIN request_meta m ON r.id=m.id WHERE r.state='unknown'").fetchall()
  return [{'id':rid,'scene_id':(json.loads(meta or '{}')).get('scene_id','')}for rid,meta in rows if (json.loads(meta or '{}')).get('transport')=='simple_flow']
 async def review(self,rid,body):
  self.valid_id(rid)
  if self.busy():raise HTTPException(409,'Dừng lượt đang chạy trước khi đối soát.')
  row=self.lookup(rid)
  if row['state']!='unknown' or body.get('confirm_no_result')is not True:raise HTTPException(409,'Cần kiểm tra lượt trên Flow và xác nhận chưa có kết quả để cho phép tạo lượt khác.')
  self.ledger.set_metadata(rid,{'message':'Bạn đã kiểm tra Flow và cho phép tạo lượt mới thủ công; kết quả lượt cũ chưa được app xác minh.','user_reviewed':True})
  self.ledger.finish(rid,'failed');self.state='ready'if self.connected else'idle';return self.lookup(rid)
 def account_id(self):return 'flow-simple-'+hashlib.sha256(self.token.encode()).hexdigest()[:24] if self.connected else None
 def busy(self):return bool(self.task and not self.task.done())
 async def checkpoint(self,kind,message):
  self.state='awaiting_user';self.message=message;self.reply=asyncio.get_running_loop().create_future()
  self.pending={'id':secrets.token_hex(16),'kind':kind,'message':message}
  try:
   answer=await self.reply
   if not answer:raise SimpleStopped('Đã dừng theo yêu cầu; không tự gửi lại.')
  finally:self.pending=None;self.reply=None
 async def respond(self,body):
  if not self.pending or body.get('id')!=self.pending['id'] or not self.reply or self.reply.done():raise HTTPException(409,'Bước xác nhận đã đổi; đọc lại trạng thái.')
  if type(body.get('accept'))is not bool:raise HTTPException(400,'Thiếu lựa chọn xác nhận.')
  self.reply.set_result(body['accept']);return {'accepted':True}
 async def disconnect_browser(self):
  context,pw=self.context,self.pw;self.context=self.page=self.pw=None;self.email=None;self.connected=False;self.project=None;self.token=secrets.token_hex(24)
  try:
   if context:await context.close()
  finally:
   if pw:await pw.stop()
 async def connect(self,body):
  async with self.gate:
   if self.busy():raise HTTPException(409,'Đang có lượt Flow; hoàn tất hoặc dừng lượt hiện tại.')
   channel=body.get('browser','msedge')
   if channel not in ('msedge','chrome'):raise HTTPException(400,'Chọn Edge hoặc Chrome.')
   await self.disconnect_browser();self.channel=channel
   self.task=asyncio.create_task(self.login());return self.status()
 async def login(self):
  import os,subprocess
  try:
   # Browser selection is explicit and profiles are separate for Edge and Chrome.
   executable=self.find_browser(self.channel)
   profile=self.data/'browser-profiles'/'simple-flow'/self.channel;profile.mkdir(parents=True,exist_ok=True)
   self.state='opening';self.message='Đang mở trình duyệt đăng nhập thông thường.'
   self.login_process=subprocess.Popen([str(executable),'--user-data-dir='+str(profile.resolve()),'--no-first-run','--disable-background-mode','--new-window','https://flow.google.com/'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**({'creationflags':0x08000000}if os.name=='nt'else{}))
   while True:
    await self.checkpoint('login','Đăng nhập Flow trong cửa sổ vừa mở. Mở được Flow rồi ĐÓNG các cửa sổ của phiên này và bấm Tiếp tục. Nếu Google từ chối, bấm Dừng.')
    if self.login_process.poll()is not None:break
    self.message='Cửa sổ đăng nhập còn chạy; đóng cửa sổ đó rồi tiếp tục.'
   from playwright.async_api import async_playwright
   self.state='connecting';self.message='Đang mở lại profile đã chọn.'
   self.pw=await async_playwright().start()
   self.context=await self.pw.chromium.launch_persistent_context(str(profile),executable_path=str(executable),headless=False,accept_downloads=True)
   self.page=self.context.pages[0] if self.context.pages else await self.context.new_page()
   await self.page.goto('https://flow.google.com/',wait_until='domcontentloaded',timeout=60000)
   await self.checkpoint('project','Kiểm tra đúng tài khoản và mở đúng dự án Flow muốn dùng. Nếu cửa sổ này yêu cầu đăng nhập lại hoặc từ chối đăng nhập, bấm Dừng; chưa tạo video.')
   from urllib.parse import urlsplit
   projects=[]
   for page in self.context.pages:
    u=urlsplit(page.url)
    if u.scheme=='https'and u.hostname=='flow.google.com'and re.fullmatch(r'/project/[a-zA-Z0-9_-]+/?',u.path):projects.append(page)
   if len(projects)!=1:raise SimpleStopped('Giữ duy nhất một tab dự án Flow trong cửa sổ này rồi kết nối lại.')
   self.page=projects[0];self.email=await self.identity()
   self.project=self.project_url();self.token=secrets.token_hex(24);self.connected=True
   self.state='ready';self.message='Đã nhận phiên Flow. Giữ cửa sổ dự án mở; node gửi một clip mỗi lần.'
  except asyncio.CancelledError:
   await self.disconnect_browser();self.state='idle';self.message='Đã dừng kết nối.';raise
  except Exception as exc:
   await self.disconnect_browser();self.state='failed';self.message=str(exc) if isinstance(exc,SimpleStopped) else 'Chưa nối được phiên Flow. Kiểm tra cửa sổ đã đóng và mở đúng dự án. '+type(exc).__name__
  finally:self.pending=None
 @staticmethod
 def find_browser(channel):
  import os,shutil
  relative={'msedge':'Microsoft/Edge/Application/msedge.exe','chrome':'Google/Chrome/Application/chrome.exe'}[channel]
  candidates=[Path(os.environ[k])/relative for k in ('PROGRAMFILES(X86)','PROGRAMFILES','LOCALAPPDATA')if os.environ.get(k)]
  if os.name=='nt':
   import winreg
   for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
    try:
     with winreg.OpenKey(hive,'Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\'+Path(relative).name)as key:candidates.append(Path(winreg.QueryValue(key,None).strip('"')))
    except OSError:pass
  else:
   found=shutil.which('microsoft-edge' if channel=='msedge' else 'google-chrome')
   if found:candidates.append(Path(found))
  for p in candidates:
   if p.is_file():return p
  raise SimpleStopped('Không tìm thấy trình duyệt đã chọn; chọn trình duyệt đã cài trên máy.')
 def project_url(self):
  from urllib.parse import urlsplit
  u=urlsplit(self.page.url)
  if u.scheme!='https' or u.hostname!='flow.google.com' or not re.fullmatch(r'/project/[a-zA-Z0-9_-]+/?',u.path):raise SimpleStopped('Mở một dự án trên flow.google.com trước; chưa gửi video.')
  return u.scheme+'://'+u.hostname+u.path.rstrip('/')
 async def identity(self):
  from urllib.parse import urlsplit
  if not self.page or self.page.is_closed():raise SimpleStopped('Cửa sổ Flow đã đóng.')
  u=urlsplit(self.page.url)
  if u.scheme!='https' or u.hostname!='flow.google.com':raise SimpleStopped('Tab không còn ở Flow; tự kiểm tra đăng nhập trên web.')
  value=await self.page.evaluate("() => String(window.WIZ_global_data?.oPEP7c || '')")
  return value.strip().casefold() if isinstance(value,str)and '@'in value else None
 async def assert_ready(self):
  current=await self.identity()
  if not self.connected or (self.email is not None and current!=self.email) or self.project_url()!=self.project:raise SimpleStopped('Tài khoản hoặc dự án đã đổi; chưa gửi thêm thao tác.')
 def lookup(self,rid):
  self.valid_id(rid)
  with self.ledger.connect()as db:row=db.execute('SELECT state,result FROM request WHERE id=?',(rid,)).fetchone()
  if not row or self.ledger.metadata(rid).get('transport')!='simple_flow':raise HTTPException(404,'Không có lượt SimpleFlow này.')
  meta=self.ledger.metadata(rid)
  return {**self.ledger.receipt(rid),'state':row[0],'result':json.loads(row[1]) if row[0]=='done'else None,'message':meta.get('message',self.message if self.active==rid else ''),'automatic_retry':False}
 @staticmethod
 def valid_id(rid):
  if not isinstance(rid,str)or not re.fullmatch(r'flow-[a-zA-Z0-9-]{8,100}',rid):raise HTTPException(400,'Mã lượt Flow không hợp lệ.')
 @guarded_submission
 async def submit(self,body):
  if not self.enabled():raise HTTPException(409,'Node Veo mới cần phiên Flow đơn giản. Bấm Kết nối Flow trước.')
  rid=body.get('request_id');self.valid_id(rid)
  prompt=body.get('prompt');refs=body.get('references')
  if body.get('confirm_send')is not True or body.get('kind')!='video' or body.get('model')!=MODEL:raise HTTPException(400,'Chỉ nhận video Lite I2V 8 giây đã xác nhận.')
  if not isinstance(prompt,str)or not prompt.strip()or len(prompt)>20000:raise HTTPException(400,'Prompt trống hoặc quá dài.')
  if not isinstance(refs,list)or len(refs)!=1 or not isinstance(refs[0],dict):raise HTTPException(400,'Cần đúng một ảnh đầu đã duyệt.')
  ref=refs[0]
  try:
   raw=base64.b64decode(ref.get('data',''),validate=True)
   if not 0<len(raw)<=6*1024**2:raise ValueError()
   from PIL import Image
   with Image.open(io.BytesIO(raw))as image:
    if image.width*image.height>40_000_000:raise ValueError()
    image.verify();fmt=Image.MIME.get(image.format)
   if fmt not in ('image/png','image/jpeg','image/webp')or fmt!=ref.get('mime_type'):raise ValueError()
  except Exception:raise HTTPException(400,'Ảnh đầu không hợp lệ hoặc vượt 6 MB.')from None
  payload={'kind':'video','model':MODEL,'prompt':prompt,'references':refs,'room_id':str(body.get('room_id',''))[:100],'scene_id':str(body.get('scene_id',''))[:100],'part':str(body.get('part',''))[:40],'account_id':self.account_id(),'transport':'simple_flow'}
  async with self.gate:
   # Existing IDs are read before readiness checks so a lost browser never resubmits them.
   with self.ledger.connect()as db:exists=db.execute('SELECT 1 FROM request WHERE id=?',(rid,)).fetchone()
   if exists:
    meta=self.ledger.metadata(rid)
    if meta.get('transport')!='simple_flow':raise HTTPException(409,'Mã lượt đã dùng cho nguồn khác.')
    old=meta.get('payload_sha256');digest=hashlib.sha256(json.dumps({k:v for k,v in payload.items()if k!='account_id'},sort_keys=True).encode()).hexdigest()
    if old!=digest:raise HTTPException(409,'Mã lượt đã dùng cho nội dung khác.')
    return self.lookup(rid)
   if self.busy():raise HTTPException(409,'Chỉ chạy một clip mỗi lần; hoàn tất lượt đang mở trước.')
   if not self.connected or body.get('selection_token')!=self.token:raise HTTPException(409,'Mở Kết nối Flow đơn giản trên node và chọn đúng phiên trước.')
   try:await self.assert_ready()
   except SimpleStopped as exc:raise HTTPException(409,str(exc))from None
   if self.unresolved():raise HTTPException(409,'Có lượt SimpleFlow chưa rõ kết quả; kiểm tra trên Flow trước khi tạo lượt khác.')
   try:self.ledger.claim(rid,payload)
   except (ValueError,RequestConflict)as exc:raise HTTPException(409,str(exc))from None
   digest=hashlib.sha256(json.dumps({k:v for k,v in payload.items()if k!='account_id'},sort_keys=True).encode()).hexdigest()
   self.ledger.set_metadata(rid,{'transport':'simple_flow','payload_sha256':digest,'clicked':False})
   self.active=rid;self.sent=False;self.task=asyncio.create_task(self.run(rid,payload,raw))
   self.tasks[rid]=self.task
   return self.lookup(rid)
 async def run(self,rid,payload,raw):
  ext={'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[payload['references'][0]['mime_type']]
  reference=self.root/(rid+'.input'+ext)
  try:
   reference.write_bytes(raw)
   await self.assert_ready()
   await self.checkpoint('project','Cảnh '+payload['scene_id']+': chọn chế độ tạo video từ ảnh trong dự án đang mở rồi Tiếp tục.')
   await self.assert_ready()
   while True:
    delivered=await upload_reference(self.page,reference,lambda text:None)
    try:await self.checkpoint('image','Kiểm tra ảnh đầu đã gắn đúng trong ô tạo Flow. '+('Đã gửi tệp.'if delivered else'Chưa tự tải được: tải ảnh thủ công từ '+str(reference))+ ' Tiếp tục chỉ khi đã nhìn thấy đúng ảnh; bấm Dừng nếu chưa đúng.')
    except SimpleStopped:raise
    break
   await self.assert_ready()
   editors=self.page.locator('textarea,[contenteditable="true"],[role="textbox"]').filter(visible=True)
   if await editors.count()==1:await editors.fill(payload['prompt'])
   else:await self.checkpoint('prompt','Không nhận diện duy nhất ô prompt. Chép prompt từ node vào Flow rồi Tiếp tục.')
   await self.checkpoint('submit','Cảnh '+payload['scene_id']+': kiểm tra đúng ảnh, prompt, Veo Lite, 8 giây, 9:16 và x1 trên Flow. Tiếp tục cho phép bấm Tạo một lần, có thể tốn credit.')
   await self.assert_ready()
   buttons=self.page.get_by_role('button',name=re.compile(r'^(Generate|Create video|Tạo video|Tạo)$',re.I)).filter(visible=True)
   automatic=await buttons.count()==1 and await buttons.is_enabled()
   self.download_waiter=asyncio.get_running_loop().create_future();self.page.on('download',self.on_download)
   self.ledger.set_metadata(rid,{'clicked':bool(automatic),'manual_submit_allowed':not automatic});self.sent=True
   if automatic:await buttons.click()
   else:await self.checkpoint('manual-submit','Chưa nhận diện duy nhất nút tạo. Bạn bấm Tạo trực tiếp trên Flow MỘT lần, rồi Tiếp tục. App không bấm thay trong bước này; nếu Flow báo lỗi, bấm Dừng để kiểm tra.')
   self.state='waiting_download';self.message='Chờ video trên Flow. Bấm tải đúng video của cảnh '+payload['scene_id']+'.'
   path=await asyncio.wait_for(self.download_waiter,1800)
   await self.checkpoint('result','Đã nhận tệp video cho cảnh '+payload['scene_id']+'. Xem lại video trên Flow: Tiếp tục xác nhận đúng clip để nhập về node; Dừng giữ lượt cần kiểm tra.')
   await self.assert_ready()
   size=path.stat().st_size;hasher=hashlib.sha256()
   with path.open('rb')as stream:
    for chunk in iter(lambda:stream.read(1024*1024),b''):hasher.update(chunk)
   digest=hasher.hexdigest()
   result={'file':path.name,'mime_type':'video/webm'if path.suffix=='.webm'else'video/mp4','sha256':digest,'bytes':size,'account_id':payload['account_id'],'room_id':payload['room_id'],'scene_id':payload['scene_id'],'part':payload['part'],'model':MODEL,'kind':'video','origin':'flow','cost':None}
   self.ledger.finish(rid,'done',result);self.vault.set_secret('simple-flow-verified',True)
   self.state='ready';self.message='Đã lưu video; node sẽ nhận về đúng cảnh.'
  except BaseException as exc:
   state='unknown'if self.sent else'failed';self.ledger.finish(rid,state)
   message=str(exc)if isinstance(exc,SimpleStopped)else'Phiên Flow đã dừng: '+type(exc).__name__+'. Không tự gửi lại.'
   self.ledger.set_metadata(rid,{'message':message});self.state=state;self.message=message
   if isinstance(exc,asyncio.CancelledError):raise
  finally:
   if self.page:self.page.remove_listener('download',self.on_download)
   if self.download_task and not self.download_task.done():
    self.download_task.cancel();await asyncio.gather(self.download_task,return_exceptions=True)
   reference.unlink(missing_ok=True);self.pending=None;self.active=None;self.download_waiter=None;self.download_task=None;self.tasks.pop(rid,None)
 def on_download(self,download):
  if not self.active or not self.sent or not self.download_waiter or self.download_waiter.done()or self.download_task:return
  self.download_task=asyncio.create_task(self.save_download(download))
 async def save_download(self,download):
  rid=self.active;tmp=self.root/(rid+'.partial')
  try:
   suffix=Path(download.suggested_filename.replace('\\','/')).suffix.lower()
   if suffix not in ('.mp4','.webm'):raise SimpleStopped('Tệp tải không phải video MP4/WebM.')
   await download.save_as(str(tmp))
   if not 0<tmp.stat().st_size<=100*1024**2:raise SimpleStopped('Kích thước video không hợp lệ.')
   from .machine_checks import run_command
   rc,out,_=await run_command('ffprobe','-v','error','-protocol_whitelist','file,pipe','-show_streams','-show_format','-of','json',str(tmp),timeout=30)
   info=json.loads(out)if not rc else{};video=next((x for x in info.get('streams',[])if x.get('codec_type')=='video'),None)
   if not video:raise SimpleStopped('Tệp tải chưa xác minh được là video.')
   width,height=int(video.get('width',0)),int(video.get('height',0));duration=float(info.get('format',{}).get('duration',0))
   if not height or abs(width/height-9/16)>.03 or not 7.5<=duration<=8.5:raise SimpleStopped('Video tải về không khớp 8 giây, dọc 9:16. Giữ lượt để kiểm tra trên Flow.')
   fmt=info.get('format',{}).get('format_name','')
   if 'webm'in fmt:suffix='.webm'
   elif 'mp4'in fmt:suffix='.mp4'
   else:raise SimpleStopped('Định dạng tệp tải chưa được hỗ trợ.')
   target=self.root/(rid+suffix);tmp.replace(target)
   if self.download_waiter and not self.download_waiter.done():self.download_waiter.set_result(target)
  except Exception as exc:
   tmp.unlink(missing_ok=True)
   if self.download_waiter and not self.download_waiter.done():self.download_waiter.set_exception(exc)
 async def stop(self):
  if self.task and not self.task.done():
   self.task.cancel();await asyncio.gather(self.task,return_exceptions=True)
  self.pending=None
  return self.status()
 async def close(self):
  await self.stop();await self.disconnect_browser()
 def file(self,rid):
  row=self.lookup(rid)
  if row['state']!='done':raise HTTPException(409,'Video chưa được nhận và xác nhận.')
  if self.ledger.storage:
   stored=self.ledger.storage.file(rid)
   if stored:return FileResponse(stored,media_type=row['result']['mime_type'])
  path=self.root/row['result']['file'];return FileResponse(path,media_type=row['result']['mime_type'])

def install_simple_flow(app,data,vault,ledger,provider):
 service=SimpleFlow(data,vault,ledger);provider.simple=service
 @app.post('/local-api/flow/simple/jobs')
 async def submit(body:dict):return await service.submit(body)
 @app.get('/local-api/flow/simple/jobs/{rid}')
 async def lookup(rid:str):return service.lookup(rid)
 @app.get('/local-api/flow/simple/files/{rid}')
 async def file(rid:str):return service.file(rid)
 @app.get('/local-api/flow/simple/status')
 async def status():return {**service.status(),'enabled':service.enabled()}
 @app.post('/local-api/flow/simple/connect')
 async def connect(body:dict):
  vault.set_secret('flow-transport-v2',{'mode':'simple'})
  return await service.connect(body)
 @app.post('/local-api/flow/simple/respond')
 async def respond(body:dict):return await service.respond(body)
 @app.post('/local-api/flow/simple/review/{rid}')
 async def review(rid:str,body:dict):return await service.review(rid,body)
 @app.post('/local-api/flow/simple/stop')
 async def stop(body:dict=None):return await service.stop()
 @app.post('/local-api/flow/simple/disconnect')
 async def disconnect(body:dict=None):
  await service.close();service.state='idle';service.message='Đã ngắt phiên; profile vẫn được giữ.';return service.status()
 @app.post('/local-api/flow/simple/mode')
 async def mode(body:dict):
  if service.busy()or provider.tasks:raise HTTPException(409,'Hoàn tất hoặc dừng lượt đang chạy trước khi đổi đường kết nối.')
  if body.get('mode')not in ('simple','legacy'):raise HTTPException(400,'Đường kết nối không hợp lệ.')
  if body['mode']=='legacy':await service.disconnect_browser()
  vault.set_secret('flow-transport-v2',{'mode':body['mode']});return {'mode':body['mode']}
 return service
