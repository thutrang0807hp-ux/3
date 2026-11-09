"""Conservative maintenance of disposable Chromium caches in app-owned profiles."""
import asyncio,hashlib,json,os,re,stat,subprocess,time
from pathlib import Path
from fastapi import HTTPException
GATE=asyncio.Lock()
CACHE_ARGS=['--disk-cache-size=33554432','--media-cache-size=16777216']
CACHE_DIRS=('Cache','Code Cache','GPUCache','ShaderCache','GrShaderCache','DawnCache','DawnGraphiteCache','DawnWebGPUCache','GraphiteDawnCache')
KEY=re.compile(r'^[a-f0-9]{24}$')
def linked(p):
 try:return p.is_symlink()or bool(getattr(p.lstat(),'st_file_attributes',0)&0x400)
 except FileNotFoundError:return False

def profile_roots(data):
 root=Path(data).absolute()/'browser-profiles';out=[]
 if any(linked(p)for p in (Path(data),root)):return []
 def add(path,label):
  if path.is_dir()and not linked(path):out.append((path,label))
 add(root/'flow-web','Flow')
 parent=root/'simple-flow'
 if parent.is_dir()and not linked(parent):
  for channel in ('msedge','chrome'):add(parent/channel,'Flow · '+channel)
 parent=root/'flow-accounts'
 if parent.is_dir()and not linked(parent):
  for p in parent.iterdir():
   if KEY.fullmatch(p.name):add(p,'Flow · '+p.name[:8])
 parent=root/'accounts'
 if parent.is_dir()and not linked(parent):
  for service in ('gemini_chat','muse','grok','chatgpt','meta'):
   folder=parent/service
   if folder.is_dir()and not linked(folder):
    for p in folder.iterdir():
     if KEY.fullmatch(p.name):add(p,service+' · '+p.name[:8])
 return out

def browser_commands():
 """None means inspection unavailable: do not delete anything."""
 if os.name=='nt':
  script="$ErrorActionPreference='Stop'; Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(chrome|msedge|chromium)\\.exe$'} | Select-Object Name,CommandLine | ConvertTo-Json -Compress"
  try:
   r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],capture_output=True,text=True,timeout=8,creationflags=0x08000000)
   if r.returncode:return None
   rows=json.loads(r.stdout)if r.stdout.strip()else[];rows=rows if isinstance(rows,list)else[rows]
   return [row['CommandLine'] for row in rows]if all(row.get('CommandLine')for row in rows)else None
  except (OSError,ValueError,subprocess.TimeoutExpired):return None
 out=[]
 try:
  for p in Path('/proc').iterdir():
   if not p.name.isdigit():continue
   try:
    comm=(p/'comm').read_text().strip().lower()
    if not any(n in comm for n in ('chrome','chromium','msedge')):continue
    raw=(p/'cmdline').read_bytes()
    if not raw:
     if any(line.startswith('State:')and 'Z' in line for line in (p/'status').read_text().splitlines()):continue
     return None
    out.append(raw.decode(errors='replace').replace('\0',' '))
   except FileNotFoundError:continue
   except (OSError,PermissionError):return None
  return out
 except OSError:return None

def keep_lite(relative):
 parts=relative.parts
 if len(parts)==1:return parts[0]in {'Local State','Last Version','sceneforge-fingerprint.json','sceneforge-profile.json','sceneforge-browser.json','sceneforge-seeded'}
 if parts[0]!='Default'and not re.fullmatch(r'Profile [0-9]+',parts[0]):return False
 tail='/'.join(parts[1:])
 return tail in {'Preferences','Secure Preferences','Cookies','Cookies-wal','Cookies-shm','Cookies-journal','Network/Cookies','Network/Cookies-wal','Network/Cookies-shm','Network/Cookies-journal'}

def scan(data,busy=False,commands=None,lean=False):
 commands=browser_commands()if commands is None else commands;started=time.monotonic();rows=[];files=[];complete=True;entries=0
 for root,label in profile_roots(data):
  blocked=busy or commands is None or any(str(root).lower()in c.lower()for c in commands)or any(os.path.lexists(root/n)for n in ('SingletonLock','SingletonCookie','SingletonSocket'))
  cache=0;retained=0;count=0
  stack=[(root,False)]
  while stack:
   folder,disposable=stack.pop()
   try:
    for p in folder.iterdir():
     entries+=1
     if entries>50000 or time.monotonic()-started>5:complete=False;stack=[];break
     if linked(p):continue
     st=p.lstat()
     if stat.S_ISDIR(st.st_mode):
      # Only exact known cache dirs at profile root or Default/Profile N.
      parent_ok=folder==root or folder.parent==root and(folder.name=='Default'or re.fullmatch(r'Profile [0-9]+',folder.name))
      stack.append((p,disposable or bool(parent_ok and p.name in CACHE_DIRS)))
     elif stat.S_ISREG(st.st_mode):
      eligible=not keep_lite(p.relative_to(root))if lean else disposable
      if eligible:
       cache+=st.st_size;count+=1
       if not blocked:files.append((p,st.st_size,st.st_mtime_ns,st.st_ino))
      else:retained+=st.st_size
   except OSError:complete=False
  rows.append({'profile':label,'cache_bytes':cache,'retained_bytes':retained,'files':count,'busy':bool(blocked)})
  if not complete:break
 token=hashlib.sha256(json.dumps([lean,[(str(p),n,t,i)for p,n,t,i in files]],separators=(',',':')).encode()).hexdigest()
 return {'profiles':rows,'bytes':sum(n for _,n,_,_ in files),'token':token,'complete':complete,'mode':'cookie-fingerprint'if lean else'cache'},files

def clean(data,busy=False,token=None,lean=False):
 plan,files=scan(data,busy,lean=lean)
 if not plan['complete']:raise HTTPException(409,'Chưa quét đủ profile; chưa dọn. Đóng trình duyệt rồi thử lại.')
 if token is not None and token!=plan['token']:raise HTTPException(409,'Cache hoặc trạng thái trình duyệt đã đổi. Quét lại trước khi dọn.')
 freed=0;count=0;errors=0
 for p,n,mtime,inode in files:
  try:
   # Recheck every ancestor: do not follow symlinks or Windows junctions.
   if any(linked(q)for q in (p,*p.parents)):errors+=1;continue
   st=p.lstat()
   if not stat.S_ISREG(st.st_mode)or(st.st_size,st.st_mtime_ns,st.st_ino)!=(n,mtime,inode):errors+=1;continue
   p.unlink();freed+=n;count+=1
  except OSError:errors+=1
 return {'bytes':freed,'files':count,'errors':errors,'skipped_profiles':sum(r['busy']for r in plan['profiles'])}

def install_profile_cache(app,vault,data,busy):
 def occupied():return any(busy(a['id'])for a in vault.rows('accounts'))
 @app.get('/local-api/accounts/profile-cache')
 async def plan():
  async with GATE:return(await asyncio.to_thread(scan,data,occupied()))[0]
 @app.post('/local-api/accounts/profile-cache')
 async def clear(body:dict):
  if not isinstance(body.get('token'),str):raise HTTPException(400,'Cần quét cache trước khi dọn.')
  async with GATE:return await asyncio.to_thread(clean,data,occupied(),body['token'])
 @app.get('/local-api/accounts/profile-lite')
 async def lite_plan():
  async with GATE:return(await asyncio.to_thread(scan,data,occupied(),lean=True))[0]
 @app.post('/local-api/accounts/profile-lite')
 async def lite_clear(body:dict):
  if not isinstance(body.get('token'),str):raise HTTPException(400,'Cần quét profile trước khi dọn.')
  async with GATE:return await asyncio.to_thread(clean,data,occupied(),body['token'],lean=True)
 async def maintain():
  await asyncio.sleep(15)
  while True:
   async with GATE:
    try:
     if not occupied():await asyncio.to_thread(clean,data,lean=True)
    except (OSError,HTTPException):pass
   await asyncio.sleep(60)
 @app.on_event('startup')
 async def start():app.state.profile_cache_task=asyncio.create_task(maintain())
 @app.on_event('shutdown')
 async def stop():
  task=getattr(app.state,'profile_cache_task',None)
  if task:task.cancel()
