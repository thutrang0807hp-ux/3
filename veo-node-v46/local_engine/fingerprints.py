"""Explicit per-profile device parameters. Not a login guarantee or stealth layer."""
import asyncio,hashlib,json,os,re,secrets,threading
import httpx
from pathlib import Path
from fastapi import HTTPException
_LOCK=threading.RLock()
SIZES={(1280,800),(1366,768),(1440,900)}
def read_config(path):
 file=Path(path)/'sceneforge-fingerprint.json'
 if not file.exists():return {'enabled':False,'cores':8,'memory':8,'width':1280,'height':800,'id':None}
 if file.is_symlink():raise HTTPException(409,'Metadata fingerprint không hợp lệ.')
 body=json.loads(file.read_text(encoding='utf8'))
 validate(body)
 return body
def validate(body):
 if type(body.get('enabled'))is not bool or type(body.get('cores'))is not int or body['cores']not in (4,8,12,16)or type(body.get('memory'))is not int or body['memory']not in (4,8,16)or type(body.get('width'))is not int or type(body.get('height'))is not int or(body['width'],body['height'])not in SIZES:raise HTTPException(400,'Thông số fingerprint không hợp lệ.')
def write_config(path,body):
 validate(body);path=Path(path)
 if not path.is_dir()or path.is_symlink():raise HTTPException(409,'Chưa có profile được lưu.')
 file=path/'sceneforge-fingerprint.json'
 with _LOCK:
  old=read_config(path);seed=old.get('seed')or secrets.token_hex(16)
  fields={k:body[k]for k in ('enabled','cores','memory','width','height')}
  ident=hashlib.sha256((seed+json.dumps(fields,sort_keys=True)).encode()).hexdigest()[:16]
  result={**fields,'seed':seed,'id':ident}
  temp=file.with_suffix('.tmp');temp.write_text(json.dumps(result),encoding='utf8');os.replace(temp,file)
 return {k:v for k,v in result.items()if k!='seed'}
def init_script(cfg):
 if not cfg.get('enabled'):return None
 # Deliberately leave UA, language, timezone, Canvas, WebGL and webdriver intact.
 # This is a limited custom device profile, not an anti-detection browser.
 values=json.dumps({k:cfg[k]for k in ('cores','memory','width','height')})
 return '''(()=>{const c='''+values+''';const mark=Symbol.for('sceneforge.device-profile.v1');if(globalThis[mark])return;globalThis[mark]=true;const set=(p,k,v)=>{try{Object.defineProperty(p,k,{get:()=>v,configurable:true})}catch{}};set(Navigator.prototype,'hardwareConcurrency',c.cores);set(Navigator.prototype,'deviceMemory',c.memory);for(const [k,v]of Object.entries({width:c.width,height:c.height,availWidth:c.width,availHeight:c.height,colorDepth:24,pixelDepth:24}))set(Screen.prototype,k,v);})();'''
async def apply(context,cfg):
 script=init_script(cfg)
 if not script:return
 await context.add_init_script(script=script)
 for page in context.pages:
  await page.set_viewport_size({'width':cfg['width'],'height':cfg['height']})
  await page.evaluate(script)
def resolve_profile(vault,data,aid,create=False):
 account=next((a for a in vault.rows('accounts')if a['id']==aid),None)
 if not account:raise HTTPException(404,'Không còn tài khoản.')
 if account['service']=='flow':
  binding=(vault.secret('flow-managed-profiles')or{}).get(aid)
  if not binding:raise HTTPException(409,'Đăng nhập Flow trên web để tạo profile trước.')
  from .google_login import flow_profile_path
  return flow_profile_path(data,binding.get('profile_key'))
 from .browser_profiles import profiles
 manager=profiles(vault,data);entry=manager.registry().get(aid)
 if not entry and create:entry=manager.reserve(account['service'],aid)
 if not entry:raise HTTPException(409,'Bấm Mở phiên và lưu một lần để tạo profile trước.')
 if entry.get('service')!=account['service']:raise HTTPException(409,'Profile không khớp dịch vụ.')
 return manager.path(entry['service'],entry['key'])
def install_fingerprints(app,vault,data,busy):
 @app.get('/local-api/accounts/fingerprint-status')
 async def overview(service:str=''):
  out=[]
  for account in vault.rows('accounts'):
   if service and account['service']!=service:continue
   try:cfg=read_config(resolve_profile(vault,data,account['id']));out.append({'account_id':account['id'],'available':True,'enabled':cfg['enabled']})
   except HTTPException as error:
    # Other services can lazily create their owned profile on the first toggle.
    out.append({'account_id':account['id'],'available':account['service']!='flow'and error.status_code==409,'enabled':False,'note':error.detail})
   except (OSError,ValueError):out.append({'account_id':account['id'],'available':False,'enabled':False,'note':'Chưa đọc được cấu hình profile này.'})
  return {'accounts':out}
 @app.post('/local-api/accounts/fingerprint/{aid}/toggle')
 async def toggle(aid:str,body:dict):
  if set(body)!={'enabled'}or type(body.get('enabled'))is not bool:raise HTTPException(400,'Chỉ nhận trạng thái bật/tắt.')
  path=resolve_profile(vault,data,aid,create=True)
  def perform():
   with _LOCK:
    cfg=read_config(path);cfg['enabled']=body['enabled'];return write_config(path,cfg)
  # Only change disk configuration. Running pages keep their captured settings;
  # the switch takes effect on the next browser launch, never mid-generation.
  return {**await asyncio.to_thread(perform),'apply_next_open':True}

 @app.get('/local-api/accounts/fingerprint/{aid}')
 async def get(aid:str):
  cfg=read_config(resolve_profile(vault,data,aid));return {k:v for k,v in cfg.items()if k!='seed'}
 @app.post('/local-api/accounts/fingerprint/{aid}')
 async def save(aid:str,body:dict):
  if set(body)!={'enabled','cores','memory','width','height'}:raise HTTPException(400,'Chỉ nhận thông số fingerprint được hỗ trợ.')
  validate(body)
  if busy(aid):raise HTTPException(409,'Tài khoản đang chạy hoặc mở đăng nhập. Đóng cửa sổ và đợi việc xong trước khi đổi fingerprint.')
  path=resolve_profile(vault,data,aid)
  # A prior app instance may still own a native profile browser.
  portfile=path/'DevToolsActivePort'
  if portfile.is_file():
   try:
    rows=portfile.read_text().splitlines();port=int(rows[0]);instance=rows[1]
    if 0<port<65536 and re.fullmatch(r'/devtools/browser/[a-zA-Z0-9-]+',instance):
     async with httpx.AsyncClient(trust_env=False,timeout=1)as client:r=await client.get(f'http://127.0.0.1:{port}/json/version')
     if r.status_code==200 and str(r.json().get('webSocketDebuggerUrl','')).endswith(instance):raise HTTPException(409,'Đóng cửa sổ trình duyệt của profile này trước khi đổi fingerprint.')
   except HTTPException:raise
   except (OSError,ValueError,IndexError,httpx.HTTPError):pass
  return await asyncio.to_thread(write_config,path,body)
