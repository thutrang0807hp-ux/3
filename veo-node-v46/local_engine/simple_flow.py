"""Single-session, user-confirmed Flow path; no engine, extension or cookie export."""
import asyncio,base64,hashlib,io,json,re,secrets,time
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse
from .request_ledger import NO_RESULT,RequestConflict
from .admission import guarded_submission
from .simple_flow_upload import upload_reference,upload_to_project
from .simple_flow_dom import ResultObserver,create_button,wait_composer,prepare_settings,settings_ready,previews,uploaded_preview

MODEL='veo-3.1-lite-i2v-8s-portrait'
class SimpleStopped(RuntimeError):pass
class FlowGenerationFailed(SimpleStopped):pass

class SimpleFlow:
 def __init__(self,data,vault,ledger):
  self.data=Path(data);self.vault=vault;self.ledger=ledger
  self.root=self.data/'flow-results';self.root.mkdir(exist_ok=True)
  self.context=self.pw=self.page=self.login_process=None
  self.channel='msedge';self.email=None;self.connected=False;self.token=secrets.token_hex(24)
  self.task=None;self.tasks={};self.pending=None;self.reply=None;self.sent=False
  self.active=None;self.project=None;self.state='idle';self.message='Chưa kết nối Flow đơn giản.'
  self.gate=asyncio.Lock();self.download_waiter=None;self.download_task=None;self.observer=None;self.auto_download=None;self.download_item=None
  self.account_bridge=None;self.account_session=None;self.pinned_binding=None;self.pinned_account=None;self.pinned_room=None
  self.upload_report=None;self.network_probes={};self.network_probe_errors={};self.task_trackers={}
  binding=self.binding()
  if binding:self.channel=binding['browser'];self.token=binding['token'];self.message='Đã lưu dự án Flow; sẽ mở lại khi tạo clip.'
 def binding(self):
  row=self.vault.secret('simple-flow-binding')or{}
  if row.get('browser')not in ('msedge','chrome')or not re.fullmatch(r'https://flow\.google\.com/project/[a-zA-Z0-9_-]+',str(row.get('project','')))or not re.fullmatch(r'[a-f0-9]{48}',str(row.get('token',''))):return None
  return row
 def save_binding(self):
  self.vault.set_secret('simple-flow-binding',{'browser':self.channel,'project':self.project,'email':self.email,'token':self.token})
 def enabled(self):return self.account_bridge is not None or (self.vault.secret('flow-transport-v2')or{}).get('mode','simple')=='simple'
 def status(self):
  if self.account_bridge:
   selection=self.account_bridge.selection()
   message=self.message if self.busy()or self.state in ('failed','unknown')else ('Đã chọn '+str(selection.get('account_name'))+' từ tab Tài khoản. Phiên được mở nền khi tạo clip.'if selection['available']else'Đăng nhập web và chọn một tài khoản Flow tại Cài đặt → Tài khoản.')
   return {'state':self.state,'message':message,'interaction':self.pending,'active_request':self.active,'unresolved':self.unresolved(),'saved_video_reviews':self.saved_video_reviews(),
    'configured':True,'account_binding':selection['available'],'transport':'web_ui','connection_method':'account_web','shared_accounts':True,'background':bool(self.account_bridge.background),
    'models':[MODEL],'model_details':[{'id':MODEL,'description':'Lite · 8s · 9:16 · tài khoản web đã chọn','accepts_images':True,'video_type':'i2v','max_images':1}],
    'per_account':1,'automatic_retry':False,'selection':selection,'project_url':self.project,'restorable':False,
    'generation_verified':bool(self.vault.secret('simple-flow-verified'))}
  return {'state':self.state,'message':self.message,'interaction':self.pending,'active_request':self.active,'unresolved':self.unresolved(),'saved_video_reviews':self.saved_video_reviews(),
   'browser':self.channel,'project_url':self.project or (self.binding()or{}).get('project'),'restorable':bool(self.binding()),
   'configured':True,'account_binding':self.connected,'transport':'web_ui','connection_method':'simple_flow',
   'models':[MODEL],'model_details':[{'id':MODEL,'description':'Lite · 8s · 9:16 · xác nhận trên Flow','accepts_images':True,'video_type':'i2v','max_images':1}],
   'per_account':1,'automatic_retry':False,'generation_verified':bool(self.vault.secret('simple-flow-verified')),
   'selection':{'mode':'selected','account_id':self.account_id(),'account_name':self.email or (self.binding()or{}).get('email') or 'Flow · phiên đã xác nhận','available':bool(self.connected and self.page and not self.page.is_closed()),'token':self.token}}
 def unresolved(self):
  with self.ledger.connect()as db:
   rows=db.execute("SELECT r.id,m.metadata,r.updated FROM request r JOIN request_meta m ON r.id=m.id WHERE r.state='unknown' ORDER BY r.updated DESC").fetchall()
  return [{'id':rid,'scene_id':data.get('scene_id',''),'part':data.get('part',''),'room_id':data.get('room_id',''),'account_id':data.get('account_id',''),'updated':updated,'needs_manual_review':time.time()-updated>=180}for rid,meta,updated in rows for data in [json.loads(meta or '{}')] if data.get('transport')=='simple_flow' and data.get('saved_video_review',{}).get('allow_new_generation') is not True]
 def saved_video_reviews(self):
  with self.ledger.connect()as db:
   rows=db.execute("SELECT r.id,m.metadata FROM request r JOIN request_meta m ON r.id=m.id WHERE r.state='unknown'").fetchall()
  return [data['saved_video_review'] for rid,meta in rows for data in [json.loads(meta or '{}')] if data.get('transport')=='simple_flow' and data.get('saved_video_review',{}).get('allow_new_generation') is True]
 async def review(self,rid,body):
  self.valid_id(rid)
  if self.busy():raise HTTPException(409,'Dừng lượt đang chạy trước khi đối soát.')
  row=self.lookup(rid)
  if row['state']!='unknown' or body.get('confirm_no_result')is not True:raise HTTPException(409,'Cần kiểm tra lượt trên Flow và xác nhận chưa có kết quả để cho phép tạo lượt khác.')
  self.ledger.set_metadata(rid,{'message':'Bạn đã kiểm tra Flow và cho phép tạo lượt mới thủ công; kết quả lượt cũ chưa được app xác minh.','user_reviewed':True})
  self.ledger.finish(rid,'failed');self.state='ready'if self.connected else'idle';return self.lookup(rid)
 def account_id(self):
  if self.account_bridge:return self.account_bridge.selection().get('account_id')
  return 'flow-simple-'+hashlib.sha256(self.token.encode()).hexdigest()[:24] if self.connected or self.binding() else None
 def busy(self):return bool(self.task and not self.task.done())
 async def start_upload_only(self,body):
  ref=body.get('reference')or{}
  try:
   raw=base64.b64decode(ref.get('data',''),validate=True)
   if not 0<len(raw)<=6*1024**2:raise ValueError()
   from PIL import Image
   with Image.open(io.BytesIO(raw))as image:
    if image.width*image.height>40_000_000:raise ValueError()
    image.verify();mime=Image.MIME.get(image.format)
   if mime not in ('image/png','image/jpeg','image/webp')or mime!=ref.get('mime_type'):raise ValueError()
  except Exception:raise HTTPException(400,'Ảnh không hợp lệ hoặc vượt 6 MB.')from None
  if not isinstance(body.get('room_id'),str)or not body['room_id']:raise HTTPException(400,'Chưa có phòng để mở dự án Flow.')
  async with self.gate:
   if self.busy():raise HTTPException(409,'Đang có tác vụ Flow. Đợi hoàn tất hoặc dừng tác vụ trước.')
   if not self.account_bridge:raise HTTPException(409,'Chọn tài khoản web tại tab Tài khoản.')
   selection=self.account_bridge.selection()
   if not selection['available']or body.get('selection_token')!=selection['token']:raise HTTPException(409,'Tài khoản đã đổi hoặc chưa sẵn sàng. Chọn lại tại tab Tài khoản.')
   rid='flow-upload-'+secrets.token_hex(12)
   self.upload_report={'request_id':rid,'state':'running','message':'Đang mở dự án để chỉ tải ảnh.','delivered':False,'has_preview':False,'reference_sha256':hashlib.sha256(raw).hexdigest(),'logs':[]}
   self.active=rid;self.pinned_account=selection['account_id'];self.pinned_room=body['room_id'];self.sent=False
   self.task=asyncio.create_task(self.run_upload_only(rid,raw,mime))
   return dict(self.upload_report)
 def upload_only_status(self,rid):
  if not self.upload_report or self.upload_report['request_id']!=rid:raise HTTPException(404,'Không có lần thử tải ảnh này trong phiên đang mở.')
  return dict(self.upload_report)
 async def run_upload_only(self,rid,raw,mime):
  reference=self.root/(rid+{'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[mime])
  report=self.upload_report;outcome='failed'
  def log(text):report['logs'].append(text);report['message']=text
  try:
   reference.write_bytes(raw)
   await self.disconnect_browser();await self.restore();await self.assert_ready()
   # Only wait for an editor or file input. No Ingredients/settings/Generate check.
   deadline=time.monotonic()+90
   while time.monotonic()<deadline:
    await self.assert_ready()
    if await self.page.locator('input[type=file]').count()or await self.page.locator('textarea,[contenteditable="true"],[role="textbox"]').filter(visible=True).count():break
    await asyncio.sleep(.25)
   else:raise SimpleStopped('Flow vẫn chưa tải xong vùng thao tác; chưa giao tệp.')
   await self.page.screenshot(path=str(self.root/(rid+'.before.png')),timeout=5000)
   report['delivered']=await upload_to_project(self.page,reference,log,report)
   outcome='delivered_unverified'if report['delivered']else'failed'
   report['message']=('Đã giao tệp ảnh cho Flow. Chưa xác minh ảnh đã lưu vào dự án. Không điền prompt hoặc tạo video.'if report['delivered']else report.get('message','Chưa giao được tệp ảnh cho Flow.'))
   if report['delivered']:await asyncio.sleep(3)
  except BaseException as exc:
   report['state']='failed';report['message']=str(exc)if isinstance(exc,SimpleStopped)else'Đã dừng thử tải ảnh: '+type(exc).__name__+'. Không tạo video.'
   if isinstance(exc,asyncio.CancelledError):raise
  finally:
   try:
    if self.page and not self.page.is_closed():
     try:
      await self.page.screenshot(path=str(self.root/(rid+'.preview.png')),timeout=5000);report['has_preview']=True
     except Exception:report['preview_error']='Chưa chụp được ảnh sau tải.'
    report['state']=outcome
    (self.root/(rid+'.upload-report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
   finally:
    self.active=None
    # File delivery can precede Flow's network upload. Keep the source file and
    # browser alive after delivery; closing here would cut off a slow upload.
    if not report['delivered']:
     reference.unlink(missing_ok=True);await self.disconnect_browser()
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
  if self.account_bridge:
   session=self.account_session;self.account_session=None;self.context=self.page=self.pw=None;self.connected=False;self.email=None;self.project=None;self.pinned_binding=None
   if session:await session.disconnect()
   return
  context,pw=self.context,self.pw;self.context=self.page=self.pw=None;self.email=None;self.connected=False;self.project=None;self.token=(self.binding()or{}).get('token')or secrets.token_hex(24)
  try:
   if context:await context.close()
  finally:
   if pw:await pw.stop()
 async def connect(self,body):
  if self.account_bridge:raise HTTPException(409,'Đăng nhập Flow tại Cài đặt → Tài khoản. Node Veo dùng trực tiếp tài khoản đang chọn, không có kết nối riêng.')
  async with self.gate:
   if self.busy():raise HTTPException(409,'Đang có lượt Flow; hoàn tất hoặc dừng lượt hiện tại.')
   channel=body.get('browser',self.channel)
   if channel not in ('msedge','chrome'):raise HTTPException(400,'Chọn Edge hoặc Chrome.')
   if self.connected and channel==self.channel and not body.get('force_login'):
    try:
     await self.assert_ready();return self.status()
    except SimpleStopped:pass
   await self.disconnect_browser();self.channel=channel
   saved=self.binding()
   self.task=asyncio.create_task(self.reconnect()if saved and saved['browser']==channel and not body.get('force_login')else self.login());return self.status()
 async def reconnect(self):
  try:await self.restore()
  except asyncio.CancelledError:
   await self.disconnect_browser();self.state='idle';raise
  except Exception as exc:
   await self.disconnect_browser();self.state='failed';self.message=str(exc)if isinstance(exc,SimpleStopped)else'Không mở lại được phiên Flow. Dùng Đăng nhập lại. '+type(exc).__name__
 async def restore(self):
  if self.account_bridge:
   from .flow_ui_session import SessionUnavailable
   try:
    session,binding=await self.account_bridge.attach(self.pinned_account)
    self.account_session=session;self.pinned_binding=binding;self.page=session.page;self.context=session.page.context
    if getattr(session,'background',False):await session.ensure_project(self.vault,self.pinned_account,self.pinned_room)
    self.email=session.email;self.project=self.project_url();self.connected=True
    return
   except SessionUnavailable as exc:raise SimpleStopped(str(exc))from None
  saved=self.binding()
  if not saved:raise SimpleStopped('Chưa có dự án đã lưu. Kết nối Flow lần đầu trước.')
  self.channel=saved['browser'];self.state='connecting';self.message='Đang mở lại dự án Flow đã lưu.'
  executable=self.find_browser(self.channel)
  profile=self.data/'browser-profiles'/'simple-flow'/self.channel
  from playwright.async_api import async_playwright
  self.pw=await async_playwright().start()
  self.context=await self.pw.chromium.launch_persistent_context(str(profile),executable_path=str(executable),headless=False,accept_downloads=True)
  self.page=self.context.pages[0]if self.context.pages else await self.context.new_page()
  await self.page.goto(saved['project'],wait_until='domcontentloaded',timeout=60000)
  current=await self.identity()
  if self.project_url()!=saved['project'] or (saved.get('email')and current!=saved['email']):raise SimpleStopped('Phiên Flow đã đổi hoặc cần đăng nhập lại. Chưa gửi lượt tạo.')
  if not saved.get('email'):
   await self.checkpoint('project','Chưa đọc được email từ Flow. Kiểm tra đúng tài khoản/dự án rồi Tiếp tục một lần cho phiên này.')
   current=await self.identity()
   if self.project_url()!=saved['project']:raise SimpleStopped('Dự án đã đổi; kết nối lại trước.')
  self.project=saved['project'];self.email=current;self.token=saved['token'];self.connected=True;self.save_binding()
  self.state='ready';self.message='Đã mở lại dự án Flow đã lưu.'
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
   self.project=self.project_url();self.token=secrets.token_hex(24);self.connected=True;self.save_binding()
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
  if self.account_bridge:
   from .flow_ui_session import SessionUnavailable
   if not self.account_session or not self.pinned_binding:raise SimpleStopped('Chưa kiểm tra được phiên web của tài khoản đã chọn. Đăng nhập lại tại tab Tài khoản.')
   try:await self.account_bridge.check(self.account_session,self.pinned_binding)
   except SessionUnavailable as exc:raise SimpleStopped(str(exc))from None
  current=await self.identity()
  if not self.connected or (self.email is not None and current!=self.email) or self.project_url()!=self.project:raise SimpleStopped('Tài khoản hoặc dự án đã đổi; chưa gửi thêm thao tác.')
 def lookup(self,rid):
  self.valid_id(rid)
  with self.ledger.connect()as db:row=db.execute('SELECT state,result,updated FROM request WHERE id=?',(rid,)).fetchone()
  if not row or self.ledger.metadata(rid).get('transport')!='simple_flow':raise HTTPException(404,'Không có lượt SimpleFlow này.')
  meta=self.ledger.metadata(rid)
  provider_task=meta.get('provider_task')or{};receipt=self.ledger.receipt(rid)
  return {**receipt,'submitted':True if provider_task.get('association_confirmed')else receipt['submitted'],'state':row[0],'result':json.loads(row[1]) if row[0]=='done'else None,'message':meta.get('message',self.message if self.active==rid else ''),'phase':meta.get('phase'),'progress':meta.get('progress'),'progress_source':meta.get('progress_source'),'has_preview':bool(meta.get('has_preview')),'automatic_retry':False,'provider_task':provider_task or None,'network_probe_available':rid in self.network_probes or (self.root/(rid+'.network.json')).is_file(),'saved_video_review':meta.get('saved_video_review'),'needs_manual_review':row[0]=='unknown' and time.time()-row[2]>=180 and not meta.get('saved_video_review',{}).get('allow_new_generation')}
 @staticmethod
 def valid_id(rid):
  if not isinstance(rid,str)or not re.fullmatch(r'flow-[a-zA-Z0-9-]{8,100}',rid):raise HTTPException(400,'Mã lượt Flow không hợp lệ.')
 def diagnose(self,rid,store_id='',room_id=''):
  self.valid_id(rid)
  report={'request_id':rid,'current_store_id':self.ledger.store_id,'expected_store_id':store_id or None,'data_directory':str(self.data.resolve()),'checked_at':time.time(),'record':None,'can_retry':False}
  with self.ledger.connect()as db:row=db.execute('SELECT state FROM request WHERE id=?',(rid,)).fetchone()
  meta=self.ledger.metadata(rid)
  if store_id and store_id!=self.ledger.store_id:
   code='different_store';message='Ứng dụng đang dùng bộ dữ liệu khác với lúc tạo lượt này. Lượt cũ vẫn được giữ; chưa tự tạo lại.'
  elif not row:
   code='missing_record'if store_id else'unknown_store'
   message='Không có bản ghi lượt này trong dữ liệu ứng dụng đang mở. Chưa đủ thông tin để biết lượt đã gửi lên Flow hay chưa; app giữ nguyên lịch sử.'
  elif meta.get('transport')!='simple_flow':
   code='different_service';message='Lượt này thuộc đường xử lý khác, không phải lượt Veo nền hiện tại. App giữ nguyên lịch sử.'
  elif room_id and meta.get('room_id')!=room_id:
   code='different_room';message='Lượt này thuộc phòng khác. App không nhập kết quả vào phòng đang mở.'
  else:
   code='found';message='Đã tìm thấy bản ghi trong app; chưa đồng nghĩa đã tìm thấy video trên Flow.';report['record']=self.lookup(rid);report['result_tracking']=meta.get('result_tracking');report['tracking_capture_error']=meta.get('tracking_capture_error');report['network_probe']=self.network_probe_snapshot(rid);report['network_probe_error']=self.network_probe_errors.get(rid)
  return {**report,'code':code,'message':message}
 @guarded_submission
 async def submit(self,body):
  if getattr(self,'pair_trial_only',False) and not (body.get('prepared_request_id') and body.get('prepared_request_id')==(getattr(self,'pair_report',None) or {}).get('request_id')):raise HTTPException(409,'Cần chuẩn bị ảnh + prompt bằng lượt trực tiếp trước khi tạo video.')
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
  if body.get('prepared_request_id'):
   payload['prepared_request_id']=body['prepared_request_id']
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
   if self.account_bridge:
    selection=self.account_bridge.selection()
    if not selection['available']or body.get('selection_token')!=selection['token']:raise HTTPException(409,'Tài khoản Flow đã chọn đã đổi hoặc chưa có phiên web dùng được. Kiểm tra Cài đặt → Tài khoản trước; chưa gửi lượt tạo.')
    payload['account_id']=selection['account_id']
   else:
    if (not self.connected and not self.binding())or body.get('selection_token')!=self.token:raise HTTPException(409,'Mở Kết nối Flow đơn giản trên node và chọn đúng phiên trước.')
    if self.connected and self.page and self.page.is_closed():await self.disconnect_browser()
    if self.connected:
     try:await self.assert_ready()
     except SimpleStopped as exc:raise HTTPException(409,str(exc))from None
   if self.unresolved():raise HTTPException(409,'Có lượt SimpleFlow chưa rõ kết quả; kiểm tra trên Flow trước khi tạo lượt khác.')
   if payload.get('prepared_request_id'):
    from .flow_prepare import validate_prepared,PrepareStopped
    try:await validate_prepared(self,payload,raw)
    except PrepareStopped as exc:raise HTTPException(409,str(exc))from None
   try:self.ledger.claim(rid,payload)
   except (ValueError,RequestConflict)as exc:raise HTTPException(409,str(exc))from None
   digest=hashlib.sha256(json.dumps({k:v for k,v in payload.items()if k!='account_id'},sort_keys=True).encode()).hexdigest()
   self.ledger.set_metadata(rid,{'transport':'simple_flow','payload_sha256':digest,'clicked':False,'automatic':body.get('automatic')is True,'phase':'preparing','progress':None,'prompt':payload['prompt'],'part':payload['part']})
   self.active=rid;self.pinned_account=payload['account_id'];self.pinned_room=payload['room_id'];self.cancel_reason=None;self.sent=False;self.task=asyncio.create_task(self.run(rid,payload,raw))
   self.tasks[rid]=self.task
   return self.lookup(rid)
 async def run(self,rid,payload,raw):
  network_probe=None
  ext={'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[payload['references'][0]['mime_type']]
  reference=self.root/(rid+'.input'+ext)
  try:
   reference.write_bytes(raw)
   background=bool(self.account_bridge and self.account_bridge.background)
   automatic_mode=background or self.ledger.metadata(rid).get('automatic')is True
   self.phase(rid,'opening','Đang mở phiên Flow nền từ tài khoản đã chọn.'if background else'Đang kiểm tra phiên Flow.')
   if not self.connected:await self.restore()
   await self.assert_ready()
   if payload.get('prepared_request_id'):
    from .flow_prepare import validate_prepared,PrepareStopped
    self.phase(rid,'checking_prepared','Đang đọc lại đúng ảnh, prompt và cấu hình đã chuẩn bị; chưa gửi tạo.')
    try:await validate_prepared(self,payload,raw)
    except PrepareStopped as exc:raise SimpleStopped(str(exc))from None
   else:
    if automatic_mode:
     self.phase(rid,'loading','Đang chờ Flow tải xong vùng tạo Ingredients; chưa tải ảnh hoặc điền prompt.')
     if not await wait_composer(self.page,self.assert_ready):raise SimpleStopped('Flow chưa tải xong vùng tạo sau 90 giây (Loading hoặc chưa có ô nhập). Chưa tải ảnh, điền prompt hoặc bấm Tạo; xem ảnh chẩn đoán trong node.')
    if not automatic_mode:await self.checkpoint('project','Cảnh '+payload['scene_id']+': chọn chế độ tạo video từ ảnh trong dự án đang mở rồi Tiếp tục.')
    settings=await prepare_settings(self.page)if automatic_mode else False
    before=await previews(self.page)if automatic_mode else []
    self.phase(rid,'uploading','Đang tải ảnh đầu lên Flow.')
    upload_steps=[]
    def upload_log(text):
     upload_steps.append(text)
     self.ledger.set_metadata(rid,{'upload_step':text})
    delivered=await upload_reference(self.page,reference,upload_log)
    attached=await uploaded_preview(self.page,before)if automatic_mode and delivered else False
    if automatic_mode and not attached:
     if background:
      detail='Đã giao tệp nhưng chưa thấy ảnh mới gắn trong vùng tạo.'if delivered else'Chưa giao được tệp vào Flow.'
      raise SimpleStopped(detail+' '+(upload_steps[-1]if upload_steps else'')+' Chưa điền prompt hoặc bấm Tạo; xem ảnh bước đang vướng trong node.')
     await self.checkpoint('image','Chưa xác nhận ảnh tham khảo đã gắn thành công trong Ingredients. Kiểm tra đúng ảnh trên Flow rồi Tiếp tục; chưa điền prompt hoặc bấm Tạo.')
     attached=await uploaded_preview(self.page,before)
     if not attached:raise SimpleStopped('Chưa xác nhận ảnh tham khảo đã gắn thành công. Chưa điền prompt hoặc bấm Tạo.')
    if not automatic_mode:
     await self.checkpoint('image','Kiểm tra ảnh đầu đã gắn đúng trong ô tạo Flow. '+('Đã gửi tệp.'if delivered else'Chưa tự tải được: tải ảnh thủ công từ '+str(reference))+' Tiếp tục chỉ khi đã nhìn thấy đúng ảnh; bấm Dừng nếu chưa đúng.')
    await self.assert_ready()
    editors=self.page.locator('textarea,[contenteditable="true"],[role="textbox"]').filter(visible=True)
    filled=await editors.count()==1
    if filled:await editors.fill(payload['prompt'])
    elif not automatic_mode:await self.checkpoint('prompt','Không nhận diện duy nhất ô prompt. Chép prompt từ node vào Flow rồi Tiếp tục.')
    if automatic_mode:
     # One fallback checkpoint for the specific unverified inputs, not three routine steps.
     missing=[]
     if self.email is None:missing.append('đúng tài khoản Flow')
     if not settings:missing.append('Veo Lite, 8 giây, 9:16, x1, Ingredients')
     if not attached:missing.append('ảnh tham khảo đã gắn thành công trong Ingredients')
     if not filled:missing.append('prompt từ node đã được dán đúng')
     if missing and background:raise SimpleStopped('Chưa tự xác minh được '+', '.join(missing)+'. Chưa bấm Tạo; xem ảnh bước đang vướng trong node.')
     if missing:await self.checkpoint('review','Chưa tự xác minh được: '+', '.join(missing)+'. Kiểm tra trên Flow rồi Tiếp tục để tạo một lần; có thể tốn credit.')
     elif not await settings_ready(self.page):raise SimpleStopped('Cài đặt Flow đã đổi trước khi gửi. Chưa bấm Tạo.')
     if not await uploaded_preview(self.page,before,timeout=1):raise SimpleStopped('Ảnh tham khảo không còn được xác nhận trong Ingredients trước khi gửi. Chưa bấm Tạo.')
    else:await self.checkpoint('submit','Cảnh '+payload['scene_id']+': kiểm tra đúng ảnh, prompt, Veo Lite, 8 giây, 9:16 và x1 trên Flow. Tiếp tục cho phép bấm Tạo một lần, có thể tốn credit.')
    await self.assert_ready()
   await self.assert_ready()
   button=await create_button(self.page)
   if button is None and background:raise SimpleStopped('Chưa nhận diện được nút tạo trong phiên Flow nền. Chưa gửi video; xem ảnh bước đang vướng trong node.')
   self.download_waiter=asyncio.get_running_loop().create_future()
   if not background:self.page.on('download',self.on_download)
   observer=ResultObserver(self.page,payload['prompt']);await observer.baseline();self.observer=observer
   if payload.get('prepared_request_id'):
    try:await validate_prepared(self,payload,raw)
    except PrepareStopped as exc:raise SimpleStopped(str(exc))from None
   if button is not None:
    try:
     from .flow_network_probe import FlowNetworkProbe
     from .flow_task_tracker import FlowTaskTracker
     tracker=FlowTaskTracker(self.page,payload['prompt'],self.project,self.assert_ready,
      lambda snapshot:self.ledger.set_metadata(rid,{'provider_task':snapshot}))
     self.task_trackers[rid]=tracker
     network_probe=FlowNetworkProbe(self.page,rid,payload['prompt'],self.assert_ready,context={k:payload[k]for k in ('room_id','scene_id','part','account_id')},task_tracker=tracker)
     await network_probe.start();self.network_probes[rid]=network_probe
    except SimpleStopped:raise
    except Exception as exc:
     self.network_probe_errors[rid]=type(exc).__name__
     if network_probe:
      try:await network_probe.stop()
      except Exception:pass
     network_probe=None
     raise SimpleStopped('Chưa mở được bộ theo dõi ID. Chưa bấm Tạo; không gửi lượt không có bộ ghi nhận.')from None
   self.ledger.set_metadata(rid,{'clicked':False,'manual_submit_allowed':button is None})
   if payload.get('prepared_request_id'):
    prepared=(getattr(self,'pair_report',None) or {})
    if prepared.get('request_id')!=payload['prepared_request_id']:prepared=self.prepare_report
   self.phase(rid,'submitting','Đang gửi một lượt tạo trên Flow.')
   if button is not None:
    if network_probe:
     try:await network_probe.mark_generate_attempt()
     except SimpleStopped:raise
     except Exception as exc:
      self.network_probe_errors[rid]=type(exc).__name__
      raise SimpleStopped('Chưa ghi nhận được thời điểm gửi. Chưa bấm Tạo.')from None
    # A recorder failure never bypasses the original account/project guard.
    await self.assert_ready()
    self.ledger.set_metadata(rid,{'clicked':True});self.sent=True
    if payload.get('prepared_request_id'):prepared['state']='submitted'
    await button.click(timeout=15000)
    if network_probe:
     network_probe.mark_click_returned();self.save_network_probe(rid)
   else:
    self.sent=True
    if payload.get('prepared_request_id'):prepared['state']='submitted'
    await self.checkpoint('manual-submit','Chưa nhận diện duy nhất nút tạo. Bấm Tạo trên Flow MỘT lần rồi Tiếp tục. App không bấm lại.')
   self.state='waiting_download';self.phase(rid,'waiting','Đã bấm tạo; chưa xác nhận Flow tiếp nhận hoặc liên kết được tác vụ.')
   path=await self.wait_result(rid,observer)
   if background and self.auto_download is None:raise SimpleStopped('Đã có tệp nhưng chưa xác minh được đúng lượt video. Không tạo lại; giữ lượt để đối soát.')
   if not (automatic_mode and self.auto_download is not None):
    await self.checkpoint('result','Đã nhận tệp video cho cảnh '+payload['scene_id']+'. Xem lại video trên Flow: Tiếp tục xác nhận đúng clip để nhập về node; Dừng giữ lượt cần kiểm tra.')
   await self.assert_ready()
   size=path.stat().st_size;hasher=hashlib.sha256()
   with path.open('rb')as stream:
    for chunk in iter(lambda:stream.read(1024*1024),b''):hasher.update(chunk)
   digest=hasher.hexdigest()
   result={'file':path.name,'mime_type':'video/webm'if path.suffix=='.webm'else'video/mp4','sha256':digest,'bytes':size,'account_id':payload['account_id'],'room_id':payload['room_id'],'scene_id':payload['scene_id'],'part':payload['part'],'model':MODEL,'kind':'video','origin':'flow','cost':None}
   provider_task=self.ledger.metadata(rid).get('provider_task')or{}
   if provider_task.get('association_confirmed'):
    result['provider_identity']={key:provider_task[key]for key in ('media_id','project_id','workflow_id')}
   self.phase(rid,'complete','Đã nhận video về đúng cảnh.');self.ledger.finish(rid,'done',result);self.vault.set_secret('simple-flow-verified',True)
   self.state='ready';self.message='Đã lưu video; node sẽ nhận về đúng cảnh.'
  except BaseException as exc:
   state='failed'if isinstance(exc,FlowGenerationFailed)else'unknown'if self.sent else'failed';self.ledger.finish(rid,state)
   message=('Tác vụ đã dừng ('+str(getattr(self,'cancel_reason',None)or'phiên ứng dụng bị hủy')+'). '+('Kiểm tra lượt đã gửi trước khi tạo thêm.'if self.sent else'Chưa bấm tạo video.'))if isinstance(exc,asyncio.CancelledError)else(str(exc)if isinstance(exc,SimpleStopped)else'Phiên Flow đã dừng: '+type(exc).__name__+'. Không tự gửi lại.')
   self.ledger.set_metadata(rid,{'message':message,'cancel_reason':getattr(self,'cancel_reason',None)if isinstance(exc,asyncio.CancelledError)else None});self.state=state;self.message=message
   if self.observer:await self.capture_tracking(rid,self.observer)
   if self.account_bridge and self.account_bridge.background:await self.capture_preview(rid)
   if not self.connected:await self.disconnect_browser()
   if isinstance(exc,asyncio.CancelledError):raise
  finally:
   if network_probe:
    try:
     evidence=await network_probe.stop();evidence['capture_state']='stopped';self.save_network_probe(rid,evidence)
    except Exception as exc:self.network_probe_errors[rid]=type(exc).__name__
    self.network_probes.pop(rid,None)
   self.task_trackers.pop(rid,None)
   if self.page:self.page.remove_listener('download',self.on_download)
   if self.download_task and not self.download_task.done():
    self.download_task.cancel();await asyncio.gather(self.download_task,return_exceptions=True)
   reference.unlink(missing_ok=True);self.pending=None;self.active=None;self.download_waiter=None;self.download_task=None;self.tasks.pop(rid,None);self.observer=None;self.auto_download=None;self.download_item=None
   if self.account_bridge:await self.disconnect_browser()
 def network_probe_snapshot(self,rid):
  self.valid_id(rid)
  probe=self.network_probes.get(rid)
  if probe:return {**probe.snapshot(),'capture_state':'active'}
  path=self.root/(rid+'.network.json')
  if not path.is_file():return {'capture_state':'not_recorded','message':'Lượt này chưa có log mạng; probe chỉ ghi các lượt tạo sau khi cập nhật.'}
  try:
   if path.stat().st_size>16*1024*1024:return {'capture_state':'report_size_limit'}
   return json.loads(path.read_text(encoding='utf-8'))
  except Exception as exc:return {'capture_state':'unavailable','error_type':type(exc).__name__}
 def save_network_probe(self,rid,evidence=None):
  try:
   evidence=self.network_probe_snapshot(rid) if evidence is None else evidence
   target=self.root/(rid+'.network.json');temporary=self.root/(rid+'.network.tmp')
   temporary.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(target)
  except Exception as exc:self.network_probe_errors[rid]=type(exc).__name__
 async def capture_tracking(self,rid,observer):
  try:
   await self.assert_ready()
   from .flow_tracking_diagnostics import observer_report
   snapshot=await asyncio.wait_for(observer_report(observer),3)
   snapshot['session_source']='active_generation'
   self.ledger.set_metadata(rid,{'result_tracking':snapshot})
  except Exception as exc:
   self.ledger.set_metadata(rid,{'tracking_capture_error':type(exc).__name__})
 async def capture_preview(self,rid):
  if not self.page or self.page.is_closed():return
  try:
   await self.page.screenshot(path=str(self.root/(rid+'.preview.png')),timeout=5000);self.ledger.set_metadata(rid,{'has_preview':True})
  except Exception:pass
 def phase(self,rid,phase,message,progress=None):
  self.message=message;self.ledger.set_metadata(rid,{'phase':phase,'message':message,'progress':progress,'progress_source':'flow_ui'if progress is not None else None})
 async def wait_result(self,rid,observer):
  tracker=self.task_trackers.get(rid)
  if tracker:return await self.wait_linked_result(rid,tracker)
  deadline=time.monotonic()+1800;preview_after=time.monotonic()+45;preview_taken=False;last=None;last_tracking=0;last_network=0
  while not self.download_waiter.done():
   if time.monotonic()>deadline:raise SimpleStopped('Flow chưa trả video sau 30 phút; kiểm tra lượt cũ, không tự gửi lại.')
   await self.assert_ready()
   if rid in self.network_probes and time.monotonic()-last_network>=5:
    self.save_network_probe(rid);last_network=time.monotonic()
   try:row=await observer.read()
   except Exception:row=None
   if time.monotonic()-last_tracking>=10:
    await self.capture_tracking(rid,observer);last_tracking=time.monotonic()
   if row:
    if row['failed']:raise SimpleStopped('Flow báo tạo thất bại cho lượt đang theo dõi. Xem chi tiết trong node; app không tự gửi lại.')
    progress=row.get('progress');phase='downloading'if row['video']else'generating'
    snapshot=(phase,progress)
    if snapshot!=last:self.phase(rid,phase,'Đã có video; đang nhận về app.'if row['video']else'Flow đang tạo video'+(' · '+str(round(progress))+'%'if progress is not None else'.'),progress);last=snapshot
    if row['video']and self.account_bridge and self.account_bridge.background:
     tmp=self.root/(rid+'.partial')
     try:
      await asyncio.wait_for(self.account_session.save_media(row.get('media_url',''),tmp),120)
      path=await self.validate_video(rid,tmp,'.mp4');self.auto_download=True;return path
     except BaseException as exc:
      tmp.unlink(missing_ok=True)
      if isinstance(exc,asyncio.CancelledError):raise
      raise SimpleStopped('Flow đã có video nhưng app chưa nhận được tệp của đúng lượt. '+(str(exc)if type(exc).__name__=='SessionUnavailable'else'Chi tiết: '+type(exc).__name__)+'. Không tạo lại; xem ảnh bước đang vướng trong node.')from None
    if row['video']and not observer.clicked and not self.download_task:
     try:
      await observer.download(row,lambda item:setattr(self,'auto_download',item if item is self.download_item else None))
     except SimpleStopped:raise
     except Exception:self.phase(rid,'waiting_download','Chưa tự tải được đúng clip. Bấm tải video đó trên Flow; không cần tạo lại.')
   if not row and not preview_taken and time.monotonic()>=preview_after and self.account_bridge and self.account_bridge.background:
    await self.capture_preview(rid);preview_taken=True
   if not row and last!=('waiting',None):
    self.phase(rid,'waiting','Đã bấm tạo; chưa có bằng chứng xác nhận Flow tiếp nhận. Đang thu dữ liệu, chưa xác định kết quả.');last=('waiting',None)
   await asyncio.wait({self.download_waiter},timeout=1)
  return self.download_waiter.result()
 async def wait_linked_result(self,rid,tracker):
  """Provider-ID path: never fall back to prompt/thumbnail attribution."""
  deadline=time.monotonic()+600;last=None;last_network=0
  while time.monotonic()<deadline:
   await self.assert_ready()
   if tracker.blocked:
    raise SimpleStopped('Không còn đủ bằng chứng liên kết một lượt gửi với một video. Giữ lượt để kiểm tra; không tự tạo lại.')
   if tracker.correlation_expired():
    self.phase(rid,'needs_review','Sau 60 giây chưa lấy được ID video của lượt vừa bấm. Chưa xác nhận Flow tiếp nhận; không tự tạo lại.')
    raise SimpleStopped(self.message)
   await tracker.tick()
   if tracker.blocked:
    raise SimpleStopped('Liên kết ID đã thay đổi hoặc chưa lưu được. Chưa nhận video; không tự tạo lại.')
   record=tracker.snapshot();state=record['state']
   if time.monotonic()-last_network>=5:
    self.save_network_probe(rid);last_network=time.monotonic()
   if state=='rpc_rejected':
    details=record.get('submit_rpc_error')or{}
    codes=details.get('public_error_codes')or[]
    suffix=' · '+', '.join(codes)if codes else ' · mã RPC '+str(details['rpc_error_code'])if 'rpc_error_code'in details else''
    message='Flow trả phản hồi lỗi cho lệnh tạo'+suffix+'. Chưa có ID video; không tự gửi lại.'
    self.phase(rid,'submit_rejected',message)
    raise SimpleStopped(message)
   if state=='failed':
    message='Flow báo tạo thất bại cho đúng ID video đã gửi.'
    if record.get('failure_code'):message+=' '+record['failure_code']
    self.phase(rid,'generation_failed',message)
    raise FlowGenerationFailed(message+' App không tự gửi lại.')
   if state=='ready':
    self.phase(rid,'downloading','Đã xác định đúng video hoàn tất; đang tải về app.')
    tmp=self.root/(rid+'.partial')
    try:
     await asyncio.wait_for(tracker.download_to(tmp),120)
     path=await self.validate_video(rid,tmp,'.mp4')
     await self.assert_ready()
     if tracker.blocked:raise SimpleStopped('Liên kết video thay đổi trong khi tải. Chưa nhập video vào cảnh.')
     self.auto_download=True
     self.ledger.set_metadata(rid,{'provider_video_downloaded':True})
     return path
    except BaseException as exc:
     tmp.unlink(missing_ok=True)
     if isinstance(exc,asyncio.CancelledError):raise
     self.ledger.set_metadata(rid,{'provider_video_downloaded':False,'provider_download_error':type(exc).__name__})
     raise SimpleStopped('Flow đã có đúng video nhưng app chưa tải và xác minh được tệp ('+type(exc).__name__+'). Giữ ID để kiểm tra; không tạo lại.')from None
   snapshot=(state,record.get('tracking_error'))
   if snapshot!=last:
    if record.get('tracking_error'):
     self.phase(rid,'tracking_error','Đã có ID video nhưng chưa đọc được trạng thái. App chỉ thử đọc lại, không gửi tạo lại.')
    elif state=='success':
     self.phase(rid,'resolving_video','Flow báo video hoàn tất; đang lấy tệp theo đúng ID.')
    elif record.get('association_confirmed'):
     self.phase(rid,'generating','Đã liên kết ID video; đang chờ Flow báo kết quả. Chưa có phần trăm render.')
    else:
     self.phase(rid,'waiting','Đã bấm tạo; đang chờ phản hồi chứa ID video, chưa xác nhận Flow tiếp nhận.')
    last=snapshot
   if record['read_failures']>=3:
    raise SimpleStopped('Đã lưu ID video nhưng ba lần đọc trạng thái không thành công. Cần kiểm tra lượt đã gửi; app không tự tạo lại.')
   await asyncio.sleep(1)
  raise SimpleStopped('Hết thời gian theo dõi; kết quả chưa được nhận về app. Giữ ID video để kiểm tra, không tự tạo lại.')
 def on_download(self,download):
  # Unrelated browser downloads cannot complete a job tracked by provider ID.
  if self.active in self.task_trackers:return
  if not self.active or not self.sent or not self.download_waiter or self.download_waiter.done()or self.download_task:return
  self.download_item=download;self.download_task=asyncio.create_task(self.save_download(download))
 async def save_download(self,download):
  rid=self.active;tmp=self.root/(rid+'.partial')
  try:
   suffix=Path(download.suggested_filename.replace('\\','/')).suffix.lower()
   if suffix not in ('.mp4','.webm'):raise SimpleStopped('Tệp tải không phải video MP4/WebM.')
   await asyncio.wait_for(download.save_as(str(tmp)),120)
   target=await self.validate_video(rid,tmp,suffix)
   if self.download_waiter and not self.download_waiter.done():self.download_waiter.set_result(target)
  except Exception as exc:
   tmp.unlink(missing_ok=True)
   if not isinstance(exc,SimpleStopped):exc=SimpleStopped('Chưa tải được tệp video từ Flow ('+type(exc).__name__+'). Giữ lượt này để đối soát, không tự tạo lại.')
   if self.download_waiter and not self.download_waiter.done():self.download_waiter.set_exception(exc)
 async def validate_video(self,rid,tmp,suffix):
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
  return target
 async def stop(self,reason='bạn bấm dừng'):
  self.cancel_reason=reason
  if self.task and not self.task.done():
   self.task.cancel();await asyncio.gather(self.task,return_exceptions=True)
  self.pending=None
  return self.status()
 async def close(self):
  await self.stop('đóng hoặc khởi động lại ứng dụng');await self.disconnect_browser()
 def file(self,rid):
  row=self.lookup(rid)
  if row['state']!='done':raise HTTPException(409,'Video chưa được nhận và xác nhận.')
  if self.ledger.storage:
   stored=self.ledger.storage.file(rid)
   if stored:return FileResponse(stored,media_type=row['result']['mime_type'])
  path=self.root/row['result']['file'];return FileResponse(path,media_type=row['result']['mime_type'])

def install_simple_flow(app,data,vault,ledger,provider):
 service=SimpleFlow(data,vault,ledger);provider.simple=service
 from .flow_account_session import AccountWebSession
 service.account_bridge=AccountWebSession(data,provider.account_service,background=True)
 from .flow_settings import register_settings_routes
 register_settings_routes(app,service)
 from .flow_prepare import register_prepare_routes
 register_prepare_routes(app,service)
 from .flow_pair_trial import register_pair_routes
 register_pair_routes(app,service)
 @app.post('/local-api/flow/simple/jobs')
 async def submit(body:dict):return await service.submit(body)
 @app.post('/local-api/flow/simple/upload-only')
 async def upload_only(body:dict):return await service.start_upload_only(body)
 @app.get('/local-api/flow/simple/upload-only/{rid}')
 async def upload_only_status(rid:str):return service.upload_only_status(rid)
 @app.get('/local-api/flow/simple/upload-only/{rid}/preview')
 async def upload_only_preview(rid:str):
  report=service.upload_only_status(rid)
  if service.page and not service.page.is_closed() and not service.busy():
   try:
    await service.page.screenshot(path=str(service.root/(rid+'.preview.png')),timeout=5000);report['has_preview']=True
   except Exception:pass
  if not report['has_preview']:raise HTTPException(404,'Chưa có ảnh sau tải.')
  return FileResponse(service.root/(rid+'.preview.png'),media_type='image/png',headers={'Cache-Control':'no-store'})
 @app.get('/local-api/flow/simple/jobs/{rid}')
 async def lookup(rid:str):return service.lookup(rid)
 @app.get('/local-api/flow/simple/diagnostics/{rid}')
 async def diagnostics(rid:str,store_id:str='',room_id:str=''):return service.diagnose(rid,store_id,room_id)
 @app.post('/local-api/flow/simple/tracking-diagnostics/{rid}')
 async def tracking_diagnostics(rid:str,body:dict):
  from .flow_tracking_diagnostics import inspect_tracking
  return await inspect_tracking(service,rid,body)
 @app.get('/local-api/flow/simple/files/{rid}')
 async def file(rid:str):return service.file(rid)
 @app.get('/local-api/flow/simple/preview/{rid}')
 async def preview(rid:str):
  service.lookup(rid);path=service.root/(rid+'.preview.png')
  if not path.is_file():raise HTTPException(404,'Chưa có ảnh bước Flow.')
  return FileResponse(path,media_type='image/png',headers={'Cache-Control':'no-store'})
 @app.get('/local-api/flow/simple/status')
 async def status():return {**service.status(),'enabled':service.enabled()}
 @app.post('/local-api/flow/simple/connect')
 async def connect(body:dict):
  if service.account_bridge:raise HTTPException(409,'Đăng nhập web tại Cài đặt → Tài khoản. Node Veo dùng tài khoản đang chọn, không có kết nối riêng.')
  vault.set_secret('flow-transport-v2',{'mode':'simple'})
  return await service.connect(body)
 @app.post('/local-api/flow/simple/respond')
 async def respond(body:dict):return await service.respond(body)
 @app.post('/local-api/flow/simple/acknowledge-saved-video/{rid}')
 async def acknowledge_saved_video(rid:str,body:dict):
  from .flow_saved_video_review import acknowledge_saved_video
  return await acknowledge_saved_video(service,rid,body)
 @app.post('/local-api/flow/simple/review/{rid}')
 async def review(rid:str,body:dict):return await service.review(rid,body)
 @app.post('/local-api/flow/simple/stop')
 async def stop(body:dict=None):return await service.stop()
 @app.post('/local-api/flow/simple/disconnect')
 async def disconnect(body:dict=None):
  await service.close();service.state='idle';service.message='Đã ngắt phiên; profile vẫn được giữ.';return service.status()
 @app.post('/local-api/flow/simple/mode')
 async def mode(body:dict):
  if service.account_bridge and body.get('mode')!='simple':raise HTTPException(409,'Veo dùng phiên đăng nhập web từ tab Tài khoản; không mở đường đăng nhập riêng.')
  if service.busy()or provider.tasks:raise HTTPException(409,'Hoàn tất hoặc dừng lượt đang chạy trước khi đổi đường kết nối.')
  if body.get('mode')not in ('simple','legacy'):raise HTTPException(400,'Đường kết nối không hợp lệ.')
  if body['mode']=='legacy':await service.disconnect_browser()
  vault.set_secret('flow-transport-v2',{'mode':body['mode']});return {'mode':body['mode']}
 return service
