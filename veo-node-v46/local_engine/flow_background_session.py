"""App-owned headless browser using the existing Accounts profile, no CDP listener."""
import asyncio,hashlib,json,re,time
from urllib.parse import urlsplit
from .flow_ui_session import FlowUiSession,SessionUnavailable
from .google_login import flow_profile_path,installed_browser

PROJECT=re.compile(r'https://flow\.google\.com/project/[a-zA-Z0-9_-]+/?$')
async def launch_background(pw,profile):
 from .fingerprints import read_config,apply
 cfg=read_config(profile)
 options={'viewport':{'width':cfg['width'],'height':cfg['height']}}if cfg['enabled']else{}
 from .profile_cache import GATE,CACHE_ARGS
 async with GATE:
  context=await pw.chromium.launch_persistent_context(str(profile),executable_path=installed_browser(),headless=True,accept_downloads=True,timeout=25000,args=CACHE_ARGS,**options)
 await apply(context,cfg)
 return context

class BackgroundFlowSession(FlowUiSession):
 background=True
 def __init__(self,data,profile_key,expected_email):
  super().__init__(data,profile_key);self.expected_email=expected_email;self.owned_context=None
 async def attach(self,playwright_factory):
  if not self.profile.is_dir():raise SessionUnavailable('Chưa tìm thấy profile đăng nhập web. Kiểm tra tài khoản đã chọn tại tab Tài khoản.')
  try:
   self.playwright=await playwright_factory().start()
   try:self.owned_context=await launch_background(self.playwright,self.profile)
   except Exception:raise SessionUnavailable('Chưa mở được phiên nền. Nếu cửa sổ đăng nhập Flow còn mở, đóng riêng cửa sổ đó một lần rồi thử lại. Không cần giữ trang Flow mở khi tạo clip.')from None
   self.browser=self.owned_context.browser
   self.page=self.owned_context.pages[0]if self.owned_context.pages else await self.owned_context.new_page()
   await self.page.goto('https://flow.google.com/',wait_until='domcontentloaded',timeout=60000)
   deadline=time.monotonic()+15
   while time.monotonic()<deadline:
    if urlsplit(self.page.url).hostname=='accounts.google.com':raise SessionUnavailable('Phiên nền cần đăng nhập/xác minh lại. Xử lý một lần tại tab Tài khoản; chưa gửi tạo video.')
    if not self.is_flow(self.page.url):raise SessionUnavailable('Phiên nền không còn ở Flow; chưa gửi tạo video.')
    value=await self.page.evaluate("()=>String(window.WIZ_global_data?.oPEP7c||'')")
    if isinstance(value,str)and '@'in value:
     if value.strip().casefold()!=self.expected_email:raise SessionUnavailable('Tài khoản trong phiên nền không khớp tài khoản đang chọn. Đã dừng trước khi tạo video.')
     self.email=self.expected_email;await self.assert_ready();return
    await asyncio.sleep(.25)
   raise SessionUnavailable('Chưa xác minh được tài khoản trong phiên nền. Chưa gửi tạo video.')
  except BaseException:
   await self.disconnect();raise
 async def ensure_project(self,vault,aid,room):
  if not room:raise SessionUnavailable('Chưa xác định phòng workflow để chọn đúng dự án Flow.')
  key=hashlib.sha256(json.dumps([aid,room],separators=(',',':')).encode()).hexdigest()
  def stored():return (vault.secret('flow-background-projects')or{}).get(key)
  def save(value):
   rows=vault.secret('flow-background-projects')or{};rows[key]={'account_id':aid,'room_id':room,**value};vault.set_secret('flow-background-projects',rows)
  record=stored()
  if record and record.get('state')=='ready':
   if not PROJECT.fullmatch(str(record.get('url',''))):raise SessionUnavailable('Địa chỉ dự án Flow đã lưu không hợp lệ. Chưa gửi video.')
   await self.page.goto(record['url'],wait_until='domcontentloaded',timeout=60000)
   await self.assert_ready()
   if not PROJECT.fullmatch(self.page.url.split('?',1)[0]):raise SessionUnavailable('Chưa mở lại được dự án Flow đã lưu. Chưa gửi tạo video.')
   return
  await self.assert_ready()
  names=re.compile(r'^(?:add\s*|\+\s*)?(?:New project|Dự án mới|Tạo dự án)(?:\s*add)?$',re.I)
  buttons=self.page.get_by_role('button',name=names).or_(self.page.get_by_role('link',name=names)).filter(visible=True)
  try:await buttons.first.wait_for(state='visible',timeout=10000)
  except Exception:raise SessionUnavailable('Chưa nhận diện được bước mở dự án Flow trong phiên nền. Chưa gửi video; xem ảnh bước đang vướng trong node.')from None
  if await buttons.count()!=1:raise SessionUnavailable('Có nhiều lựa chọn dự án Flow; chưa tự chọn hoặc gửi video.')
  save({'state':'creating'})
  try:
   await buttons.click(timeout=10000)
   await self.page.wait_for_url(re.compile(r'^https://flow\.google\.com/project/[a-zA-Z0-9_-]+/?(?:\?.*)?$'),timeout=30000)
   await self.assert_ready()
   url=self.page.url.split('?',1)[0].rstrip('/')
   if not PROJECT.fullmatch(url):raise SessionUnavailable('Dự án Flow chưa xác minh được.')
   save({'state':'ready','url':url})
  except BaseException:
   save({'state':'unknown'})
   raise
 async def disconnect(self):
  context=self.owned_context;self.owned_context=None
  try:
   if context:await context.close()
  finally:await super().disconnect()
 async def save_media(self,url,target,limit=100*1024**2):
  """Stream only the attributed result media through its authenticated page."""
  import base64,secrets
  u=urlsplit(url);host=u.hostname or''
  allowed_blob=u.scheme=='blob'and url.startswith('blob:https://flow.google.com/')
  allowed_https=u.scheme=='https'and u.port in (None,443)and not u.username and not u.password and (host=='storage.googleapis.com'or host=='googleusercontent.com'or host.endswith('.googleusercontent.com')or host=='flow.google.com'and u.path.startswith(('/media/','/api/media/','/download/','/api/download/')))
  if not allowed_blob and not allowed_https:raise SessionUnavailable('Địa chỉ tệp kết quả Flow chưa được hỗ trợ; không tải nhầm nguồn.')
  key='sf_media_'+secrets.token_hex(12)
  try:
   await self.page.evaluate('''async ({url,key,limit})=>{
    const controller=new AbortController();
    try{const r=await fetch(url,{credentials:new URL(url).origin===location.origin?'include':'omit',redirect:'error',signal:controller.signal});
     if(!r.ok||!r.body||Number(r.headers.get('content-length')||0)>limit)throw Error('media_unavailable');
     window[key]={reader:r.body.getReader(),rest:null,total:0,controller,limit};
    }catch(e){controller.abort();throw Error('media_unavailable');}
   }''',{'url':url,'key':key,'limit':limit})
   size=0
   with target.open('wb')as stream:
    while True:
     part=await self.page.evaluate('''async key=>{
      const s=window[key];if(!s)throw Error('media_closed');
      let bytes=s.rest;s.rest=null;
      if(!bytes){const r=await s.reader.read();if(r.done)return {done:true};bytes=r.value;}
      if(bytes.length>262144){s.rest=bytes.subarray(262144);bytes=bytes.subarray(0,262144);}
      s.total+=bytes.length;if(s.total>s.limit){s.controller.abort();throw Error('media_too_large');}
      let text='';for(let i=0;i<bytes.length;i+=8192)text+=String.fromCharCode(...bytes.subarray(i,i+8192));
      return {done:false,data:btoa(text)};
     }''',key)
     if part.get('done'):break
     chunk=base64.b64decode(part['data'],validate=True);size+=len(chunk)
     if size>limit:raise SessionUnavailable('Video vượt giới hạn tải trong app.')
     stream.write(chunk)
   if not size:raise SessionUnavailable('Flow chưa trả dữ liệu video.')
  except BaseException:
   target.unlink(missing_ok=True);raise
  finally:
   try:await self.page.evaluate('''async key=>{const s=window[key];delete window[key];if(s){s.controller.abort();try{await s.reader.cancel()}catch{}}}''',key)
   except Exception:pass
