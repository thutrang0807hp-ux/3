"""App-owned persistent profiles and stable native browser settings; no spoofing.

The identity ID is local bookkeeping, not an anti-detection fingerprint. Browser
updates and OS changes may still change the browser's real fingerprint.
"""
import asyncio,hashlib,json,os,re,secrets,shutil,threading
from pathlib import Path
from fastapi import HTTPException

SERVICES={'gemini_chat','muse','grok','chatgpt','meta'}
KEY=re.compile(r'^[a-f0-9]{24}$')
_MANAGERS={}
class Profiles:
 def __init__(self,vault,data):
  self.vault=vault;self.data=Path(data);self.root=self.data/'browser-profiles'/'accounts';self.lock=threading.RLock();self.leases={}
 def path(self,service,key):
  if service not in SERVICES or not isinstance(key,str)or not KEY.fullmatch(key):raise HTTPException(400,'Profile tài khoản không hợp lệ.')
  path=self.root/service/key
  for p in [self.data,self.data/'browser-profiles',self.root,self.root/service,path]:
   if p.is_symlink():raise HTTPException(409,'Thư mục profile không được là liên kết.')
  return path
 def registry(self):return self.vault.secret('account-browser-profiles-v1')or{}
 def reserve(self,service,aid=None):
  with self.lock:
   if aid:
    row=next((a for a in self.vault.rows('accounts')if a['id']==aid and a['service']==service),None)
    if not row:raise HTTPException(404,'Không có tài khoản của đúng dịch vụ.')
   old=self.registry().get(aid)if aid else None
   key=old['key']if old and old.get('service')==service else secrets.token_hex(12)
   entry={'service':service,'key':key};path=self.path(service,key);path.mkdir(parents=True,exist_ok=True,mode=0o700)
   if aid and not old:self.bind(entry,aid)
   return entry
 def settings(self,entry,executable=None):
  path=self.path(entry['service'],entry['key']);meta=path/'sceneforge-profile.json'
  with self.lock:
   if meta.is_symlink():raise HTTPException(409,'Metadata profile không hợp lệ.')
   if meta.exists():
    body=json.loads(meta.read_text(encoding='utf8'))
    if body.get('key')!=entry['key']or body.get('service')!=entry['service']:raise HTTPException(409,'Profile không khớp tài khoản.')
    if not Path(body['executable']).is_file():raise HTTPException(409,'Trình duyệt đã lưu cho profile không còn. Cài lại đúng trình duyệt trước khi mở phiên.')
    return body
   if not executable:
    from .google_login import installed_browser
    executable=installed_browser()
   body={**entry,'executable':str(Path(executable).resolve()),'viewport':{'width':1280,'height':800},'identity_id':hashlib.sha256((entry['key']+'|'+str(Path(executable).resolve())).encode()).hexdigest()[:16]}
   temp=meta.with_suffix('.tmp');temp.write_text(json.dumps(body),encoding='utf8');os.replace(temp,meta);return body
 def bind(self,entry,aid):
  with self.lock:
   saved=self.registry()
   # A profile is owned by one logical account only, even after account changes.
   for ident,old in list(saved.items()):
    if ident!=aid and old==entry:
     saved.pop(ident)
     row=next((r for r in self.vault.rows('accounts')if r['id']==ident),None)
     if row:row.pop('browser_profile_id',None);self.vault.put('accounts',row)
   saved[aid]=dict(entry);self.vault.set_secret('account-browser-profiles-v1',saved)
   row=next((r for r in self.vault.rows('accounts')if r['id']==aid),None)
   if row:row['browser_profile_id']=entry['key'][:8];row['browser_identity']='native-stable';self.vault.put('accounts',row)
 def lease(self,entry):return self.leases.setdefault((entry['service'],entry['key']),asyncio.Lock())
 async def native(self,entry,url,cookies=None):
  lease=self.lease(entry)
  if lease.locked():raise HTTPException(409,'Profile đang được dùng. Đợi cửa sổ hoặc công việc hiện tại kết thúc.')
  await lease.acquire()
  try:
   from .google_login import open_google_login
   cfg=self.settings(entry);login=await open_google_login(url,self.data,profile=self.path(entry['service'],entry['key']),keep_profile=True,executable=cfg['executable'])
   login.profile_release=lease.release
   marker=self.path(entry['service'],entry['key'])/'sceneforge-seeded'
   if cookies:
    try:
     await login.cookies();context=login.connection.contexts[0];await context.add_cookies(cookies)
     page=context.pages[0]if context.pages else await context.new_page();await page.goto(url,wait_until='domcontentloaded',timeout=45000);marker.write_text('1')
    except BaseException:
     await login.close();raise
   return login
  except BaseException:
   if lease.locked():lease.release()
   await self.discard(entry)
   raise
 async def discard(self,entry):
  if not entry:return
  with self.lock:
   if entry in self.registry().values():return
  await asyncio.to_thread(shutil.rmtree,self.path(entry['service'],entry['key']),True)
 def ensure_idle(self,aid):
  entry=self.registry().get(aid)
  if entry and self.lease(entry).locked():raise HTTPException(409,'Profile đang mở hoặc đang chạy. Đóng cửa sổ trước khi gỡ.')
 async def remove(self,aid):
  self.ensure_idle(aid);entry=self.registry().get(aid)
  if not entry:return
  lease=self.lease(entry);await lease.acquire()
  try:
   path=self.path(entry['service'],entry['key']);await asyncio.to_thread(shutil.rmtree,path,True)
   if path.exists():raise HTTPException(409,'Chưa xóa được profile trên ổ đĩa. Đóng trình duyệt rồi thử lại.')
   with self.lock:
    saved=self.registry();saved.pop(aid,None);self.vault.set_secret('account-browser-profiles-v1',saved)
  finally:lease.release()
 async def browser(self,entry,storage=None):
  # One real browser profile cannot be opened concurrently. Waiting is cancellable
  # and happens before any prompt is sent. Different accounts remain independent.
  lease=self.lease(entry);await lease.acquire();pw=None;context=None
  try:
   from playwright.async_api import async_playwright
   pw=await async_playwright().start()
   try:cfg=self.settings(entry)
   except HTTPException as error:
    if error.status_code!=503:raise
    cfg=self.settings(entry,pw.chromium.executable_path)
   path=self.path(entry['service'],entry['key']);marker=path/'sceneforge-seeded'
   context=await pw.chromium.launch_persistent_context(str(path),executable_path=cfg['executable'],headless=False,viewport=cfg['viewport'],args=['--disk-cache-size=67108864','--media-cache-size=33554432'])
   if storage:
    current={(c['domain'],c['path'],c['name'])for c in await context.cookies()}
    missing=[c for c in storage.get('cookies',[])if (c.get('domain'),c.get('path','/'),c.get('name'))not in current]
    if missing:await context.add_cookies(missing)
   if storage and not marker.exists():
    for origin in storage.get('origins',[]):
     page=await context.new_page();await page.goto(origin['origin'],wait_until='domcontentloaded',timeout=45000)
     await page.evaluate('(items)=>{for(const i of items)localStorage.setItem(i.name,i.value)}',origin.get('localStorage',[]));await page.close()
    marker.write_text('1')
   return pw,ProfileBrowser(context,pw,lease)
  except BaseException as error:
   try:
    if context:await context.close()
    if pw:await pw.stop()
   finally:lease.release()
   await self.discard(entry)
   if isinstance(error,(asyncio.CancelledError,HTTPException)):raise
   raise HTTPException(409,'Chưa mở được profile riêng. Đóng cửa sổ đang dùng profile này hoặc kiểm tra trình duyệt; phiên đã lưu vẫn được giữ.')from None
class ProfileBrowser:
 def __init__(self,context,pw,lease):self.context=context;self.pw=pw;self.lease=lease;self.closed=False
 async def new_context(self,**kwargs):return self.context
 async def close(self):
  if self.closed:return
  self.closed=True
  try:await self.context.close()
  finally:self.lease.release()

def profiles(vault,data):
 key=(id(vault),str(Path(data).resolve()))
 if key not in _MANAGERS:_MANAGERS[key]=Profiles(vault,data)
 return _MANAGERS[key]

def saved_cookies(session,service):
 """Convert only the selected service's encrypted saved session for migration."""
 value=session.get('cookies',session.get('cookies.json',[]))if isinstance(session,dict)else[]
 if isinstance(value,str):
  try:value=json.loads(value)if len(value)<=200000 else[]
  except ValueError:value=[]
 if isinstance(value,dict):
  domain='.google.com'if service=='gemini_chat'else'.muse.ai'
  value=[{'name':k,'value':v,'domain':domain,'path':'/','secure':True}for k,v in value.items()if isinstance(k,str)and isinstance(v,str)and not k.startswith('__Host-')]
 if not isinstance(value,list):return []
 domains=('google.com','gemini.google.com')if service=='gemini_chat'else('muse.ai',)
 return [c for c in value if isinstance(c,dict)and any(str(c.get('domain','')).lstrip('.')==d or str(c.get('domain','')).lstrip('.').endswith('.'+d)for d in domains)]
