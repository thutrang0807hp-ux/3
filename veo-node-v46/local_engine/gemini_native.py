"""App-owned headless Gemini. Port of test-gemoni-chat 75f43c9's browser workflow.
Normal-browser sign-in precedes automation. No cookie export or extension.
Downloads: Gemini download control, authenticated request, then rendered pixels.
"""
import asyncio, base64, re, time
from pathlib import Path
from urllib.parse import urlparse
from fastapi import HTTPException

URL='https://gemini.google.com/app'
EDITOR='rich-textarea [contenteditable="true"]:visible, .ql-editor[contenteditable="true"]:visible, [contenteditable="true"][role="textbox"]:visible'
HOSTS={'gemini.google.com','lh3.google.com','lh3.googleusercontent.com'}

class NativeGemini:
 def __init__(self,service):
  self.service=service;self.pw=None;self.start_lock=asyncio.Lock();self.contexts={};self.turns={}
 async def context(self,aid):
  if aid in self.contexts:return self.contexts[aid][0]
  from .browser_profiles import profiles
  manager=profiles(self.service.vault,self.service.data);entry=manager.registry().get(aid)
  if not entry:raise HTTPException(409,'Đăng nhập lại Gemini để tạo hồ sơ riêng chạy ẩn.')
  lease=manager.lease(entry)
  if lease.locked():raise HTTPException(409,'Đóng cửa sổ đăng nhập Gemini do app mở trước khi chạy nền.')
  await lease.acquire()
  try:
   from playwright.async_api import async_playwright
   async with self.start_lock:
    if self.pw is None:self.pw=await async_playwright().start()
   cfg=manager.settings(entry)
   context=await self.pw.chromium.launch_persistent_context(str(manager.path(entry['service'],entry['key'])),executable_path=cfg['executable'],headless=True,accept_downloads=True,viewport={'width':1280,'height':900},args=['--no-first-run','--no-default-browser-check','--disable-background-mode'])
   self.contexts[aid]=(context,lease);return context
  except BaseException:
   lease.release();raise
 async def close_account(self,aid):
  item=self.contexts.pop(aid,None)
  if item:
   try:await item[0].close()
   finally:item[1].release()
 async def close(self):
  for aid in list(self.contexts):await self.close_account(aid)
  if self.pw:await self.pw.stop();self.pw=None
 async def verify(self,aid):
  context=await self.context(aid);page=await context.new_page()
  try:
   await page.goto(URL,wait_until='domcontentloaded',timeout=45000)
   await page.locator(EDITOR).first.wait_for(state='visible',timeout=22000)
   if not any(c['name']=='__Secure-1PSID'for c in await context.cookies(URL)):raise ValueError('Chưa đăng nhập Gemini.')
  finally:await page.close()
 async def attach(self,page,references):
  if not references:return
  if len(references)>8:raise ValueError('Tối đa 8 ảnh nguồn / tham chiếu.')
  control=page.locator('input[type=file]').first
  if not await control.count():
   upload=page.get_by_role('button',name=re.compile(r'upload|add files|attach|tải lên|thêm tệp|đính kèm',re.I)).first
   await upload.click(timeout=10000)
  await control.wait_for(state='attached',timeout=10000)
  files=[]
  for i,ref in enumerate(references):
   mime=ref['mime_type'];ext={'image/png':'png','image/jpeg':'jpg','image/webp':'webp'}.get(mime)
   if not ext:raise ValueError('Ảnh tham chiếu không hợp lệ.')
   files.append({'name':f'SceneForge-reference-{i+1}.{ext}','mimeType':mime,'buffer':base64.b64decode(ref['data'],validate=True)})
  await control.set_input_files(files,timeout=30000)
  await page.wait_for_function("n=>{const imgs=[...document.querySelectorAll('user-query img, .input-area-container img, .file-preview img, .attachment-preview img, .attachment img, .preview-container img')].filter(i=>i.complete&&i.naturalWidth>0);const labels=[...document.querySelectorAll('[aria-label],[title]')].map(e=>(e.getAttribute('aria-label')||'')+' '+(e.title||''));return imgs.length>=n||Array.from({length:n},(_,i)=>labels.some(t=>t.includes('SceneForge-reference-'+(i+1)))).every(Boolean)}",arg=len(files),timeout=45000)
 async def image(self,answer):
  await answer.wait_for(state='visible',timeout=90000)
  deadline=time.monotonic()+180
  while time.monotonic()<deadline:
   images=await answer.locator('img').evaluate_all("nodes=>nodes.map((i,index)=>({index,url:i.currentSrc,width:i.naturalWidth,height:i.naturalHeight,identified:!!i.closest('generated-image,generated-image-container,single-image,image-generation')}))")
   for im in images:
    u=urlparse(im['url']);kind=u.scheme
    allowed=(kind=='blob'and im['identified']and im['url'].startswith('blob:https://gemini.google.com/'))or(kind=='data'and im['identified']and re.match(r'^data:image/(png|jpeg|webp);base64,',im['url']))or(kind=='https'and u.hostname in HOSTS and not u.username and not u.password and not u.port and(im['identified']or re.match(r'^/(gg|gg-dl|rd-gg)(/|$)',u.path)))
    if allowed and im['width']>=256 and im['height']>=256:return im,answer.locator('img').nth(im['index'])
   await asyncio.sleep(.6)
  raise TimeoutError('Gemini chưa trả ảnh mới của lượt này.')
 async def save(self,context,page,answer,im,element,output):
  data=None
  # Download through the authenticated Gemini UI first, just like the tested repo.
  try:
   await element.hover(timeout=5000)
   buttons=answer.get_by_role('button',name=re.compile(r'download|tải xuống|tải ảnh',re.I)).or_(answer.get_by_role('link',name=re.compile(r'download|tải xuống|tải ảnh',re.I)))
   if await buttons.count()!=1:raise ValueError('Không có nút tải duy nhất.')
   async with page.expect_download(timeout=20000)as info:await buttons.click(timeout=5000)
   download=await info.value
   try:
    path=Path(await asyncio.wait_for(download.path(),20))
    if path.stat().st_size>24*1024**2:raise ValueError('Ảnh vượt 24 MB.')
    data=await asyncio.to_thread(path.read_bytes)
   finally:await download.delete()
  except Exception:pass
  if data is None:
   try:
    if im['url'].startswith(('blob:','data:')):
     encoded=await page.evaluate("async u=>{const r=await fetch(u);const b=await r.blob();if(b.size>25165824)throw Error('size');return new Promise((ok,no)=>{const f=new FileReader();f.onload=()=>ok(f.result.split(',')[1]);f.onerror=no;f.readAsDataURL(b)})}",im['url']);data=base64.b64decode(encoded,validate=True)
    else:
     response=await context.request.get(im['url'],headers={'referer':'https://gemini.google.com/'},max_redirects=0,timeout=20000)
     try:
      if not response.ok:raise ValueError('Không tải được ảnh trong phiên Gemini.')
      data=await response.body()
     finally:await response.dispose()
   except Exception:pass
  if data is None:
   encoded=await element.evaluate("(e,u)=>{if(e.currentSrc!==u||e.naturalWidth*e.naturalHeight>25000000)throw Error('image changed');const c=document.createElement('canvas');c.width=e.naturalWidth;c.height=e.naturalHeight;c.getContext('2d').drawImage(e,0,0);return c.toDataURL('image/png').split(',')[1]}",im['url']);data=base64.b64decode(encoded,validate=True)
  if not 0<len(data)<=24*1024**2:raise ValueError('Ảnh vượt giới hạn 24 MB.')
  from PIL import Image
  import io
  with Image.open(io.BytesIO(data))as image:
   if image.format not in ('PNG','JPEG','WEBP')or image.width*image.height>40000000:raise ValueError('Ảnh không hợp lệ.')
   image.verify()
  await asyncio.to_thread(Path(output).write_bytes,data)
 async def generate(self,rid,aid,payload,output):
  accepted=False;page=None;phase='open_profile'
  try:
   context=await self.context(aid)
   if payload.get('browser_receive'):
    accepted=True
    turn=self.turns.get(rid)
    if not turn or turn['aid']!=aid:return {'ok':False,'accepted':None,'code':'GEMINI_NATIVE_RECEIPT_MISSING'}
    page=turn['page'];answer=page.locator('model-response').nth(turn['answer'])
   else:
    if rid in self.turns:return {'ok':False,'accepted':None,'code':'GEMINI_BROWSER_OUTCOME_UNKNOWN'}
    page=await context.new_page();await page.goto(URL,wait_until='domcontentloaded',timeout=45000)
    editor=page.locator(EDITOR).first;await editor.wait_for(state='visible',timeout=22000)
    phase='attach_references';await self.attach(page,payload.get('references',[]))
    count=await page.locator('model-response').count()
    prompt=payload['prompt']
    if payload['kind']=='image':prompt='Hãy tạo và trả về một ảnh mới dựa trên mô tả và các ảnh tham chiếu dưới đây.\n\n'+prompt
    phase='fill_prompt';await editor.fill(prompt,timeout=30000)
    send=page.get_by_role('button',name=re.compile(r'^(send( message| prompt)?|gửi( tin nhắn| lời nhắc)?)$',re.I)).or_(page.locator('button.send-button')).first
    await send.wait_for(state='visible',timeout=12000)
    phase='send_prompt';self.turns[rid]={'aid':aid,'page':page,'answer':count};accepted=None
    await send.click(timeout=12000);accepted=True
    answer=page.locator('model-response').nth(count)
   if payload['kind']=='image':
    phase='wait_image';im,element=await self.image(answer);phase='download_image';await self.save(context,page,answer,im,element,output)
    result={'ok':True,'download_variant':'native-authenticated-browser'}
   else:
    await answer.wait_for(state='visible',timeout=90000);last='';changed=time.monotonic();deadline=time.monotonic()+180
    while time.monotonic()<deadline:
     text=(await answer.inner_text()).strip()
     if text!=last:last=text;changed=time.monotonic()
     if text and time.monotonic()-changed>3 and not await page.get_by_role('button',name=re.compile(r'^(stop|dừng|ngừng)\b',re.I)).first.is_visible():break
     await asyncio.sleep(.5)
    else:raise TimeoutError('Gemini chưa trả xong văn bản.')
    result={'ok':True,'text':last}
   self.turns.pop(rid,None);await page.close();return result
  except Exception as exc:
   if accepted is False and page:
    try:await page.close()
    except Exception:pass
   return {'ok':False,'accepted':accepted,'code':'GEMINI_NATIVE_FAILED','phase':phase,'error_type':type(exc).__name__}
