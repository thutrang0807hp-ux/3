"""Thin launcher for the user's original Node/CDP Gemini connector (75f43c9).
Python owns profiles/receipts only. Sending and downloading run in gemini.mjs.
"""
import asyncio,base64,hashlib,io,json,os,shutil,subprocess,tempfile,time,zipfile
from pathlib import Path
from http.client import HTTPConnection
from fastapi import HTTPException

ROOT=Path(__file__).resolve().parents[1]

def browser_port(metadata):
 try:
  port_text,socket_path,*_=metadata.read_text().splitlines();port=int(port_text)
  if not 1024<=port<=65535 or not socket_path.startswith('/devtools/browser/'):return None
  connection=HTTPConnection('127.0.0.1',port,timeout=1)
  try:
   connection.request('GET','/json/version');response=connection.getresponse()
   if response.status!=200:return None
   endpoint=json.loads(response.read(8192))['webSocketDebuggerUrl']
  finally:connection.close()
  if endpoint==f'ws://127.0.0.1:{port}{socket_path}':return port
 except Exception:pass
 return None

class NativeGemini:
 def __init__(self,service):
  self.service=service;self.contexts={};self.runtime_lock=asyncio.Lock();self.runtime_path=None
  self.receipts=Path(service.root)/'native-turns';self.receipts.mkdir(exist_ok=True,mode=0o700)
 def unpack(self):
  archive=ROOT/'vendor/gemini-native-node.zip';meta=json.loads((ROOT/'vendor/gemini-native-node.json').read_text())
  digest=hashlib.sha256(archive.read_bytes()).hexdigest()
  if digest!=meta['sha256']:raise ValueError('Bộ kết nối Gemini không đúng mã kiểm tra. Cài lại bản cập nhật.')
  folder=Path(self.service.data)/'engines'/('gemini-native-node-'+digest[:16]);marker=folder/'.ready'
  if not marker.is_file():
   folder.parent.mkdir(parents=True,exist_ok=True)
   with tempfile.TemporaryDirectory(dir=folder.parent,prefix='native-unpack-')as tmp:
    with zipfile.ZipFile(archive)as z:
     for item in z.infolist():
      if not (Path(tmp)/item.filename).resolve().is_relative_to(Path(tmp).resolve()):raise ValueError('Runtime path invalid')
     z.extractall(tmp)
    (Path(tmp)/'.ready').write_text(digest)
    if folder.exists():shutil.rmtree(folder)
    shutil.move(tmp,folder)
  return folder
 async def runtime(self):
  async with self.runtime_lock:
   if self.runtime_path is None:self.runtime_path=await asyncio.to_thread(self.unpack)
   return self.runtime_path
 async def call(self,port,request,timeout=360):
  runtime=await self.runtime();node=str(runtime/'node.exe')if os.name=='nt'else shutil.which('node')
  if not node:raise RuntimeError('Thiếu Node runtime của bộ kết nối Gemini.')
  process=await asyncio.create_subprocess_exec(node,str(runtime/'gemini.mjs'),cwd=runtime,stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,**({'creationflags':0x08000000}if os.name=='nt'else{}))
  try:
   stdout,_=await asyncio.wait_for(process.communicate(json.dumps({'port':port,'request':request}).encode()),timeout)
   response=json.loads(stdout)
   if not isinstance(response,dict):raise ValueError('Invalid response')
   return response
  except BaseException:
   if process.returncode is None:
    process.kill();await process.wait()
   raise
 async def context(self,aid):
  old=self.contexts.get(aid)
  if old and old['process'].poll()is None:return old
  if old:self.contexts.pop(aid);old['lease'].release()
  from .browser_profiles import profiles
  manager=profiles(self.service.vault,self.service.data);entry=manager.registry().get(aid)
  if not entry:raise HTTPException(409,'Đăng nhập lại Gemini để tạo hồ sơ riêng chạy ẩn.')
  await self.runtime();lease=manager.lease(entry)
  if lease.locked():raise HTTPException(409,'Đóng cửa sổ đăng nhập Gemini do app mở trước khi chạy nền.')
  await lease.acquire();process=None
  try:
   cfg=manager.settings(entry);profile=manager.path(entry['service'],entry['key']);metadata=profile/'DevToolsActivePort'
   if await asyncio.to_thread(browser_port,metadata):raise HTTPException(409,'Hồ sơ Gemini còn mở từ phiên trước. Thoát app cũ trước khi kết nối lại.')
   metadata.unlink(missing_ok=True)
   args=[cfg['executable'],f'--user-data-dir={profile}','--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--headless=new','--no-first-run','--no-default-browser-check','--disable-background-mode','about:blank']
   if os.name!='nt'and hasattr(os,'getuid')and os.getuid()==0:args.insert(-1,'--no-sandbox')
   process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**({'creationflags':0x08000000}if os.name=='nt'else{}))
   deadline=time.monotonic()+18
   while time.monotonic()<deadline:
    port=await asyncio.to_thread(browser_port,metadata)
    if port and process.poll()is None:
     row={'port':port,'process':process,'lease':lease};self.contexts[aid]=row;return row
    if process.poll()is not None:break
    await asyncio.sleep(.25)
   raise RuntimeError('Không khởi chạy được Chrome riêng của Gemini.')
  except BaseException:
   if process and process.poll()is None:
    process.terminate()
    try:await asyncio.to_thread(process.wait,timeout=5)
    except subprocess.TimeoutExpired:pass
   lease.release();raise
 async def close_account(self,aid):
  row=self.contexts.get(aid)
  if not row:return
  if row['process'].poll()is None:
   await self.call(row['port'],{'action':'shutdown'},timeout=20)
   await asyncio.to_thread(row['process'].wait,timeout=5)
  self.contexts.pop(aid,None);row['lease'].release()
 async def close(self):
  for aid in list(self.contexts):
   try:await self.close_account(aid)
   except Exception:pass
 async def verify(self,aid):
  row=await self.context(aid);response=await self.call(row['port'],{'action':'verify'})
  if not response.get('result',{}).get('signedIn'):raise HTTPException(409,'Gemini chưa nhận phiên đăng nhập. Đăng nhập lại trong cửa sổ riêng của app.')
 def paths(self,rid):
  self.service.valid_id(rid)
  return self.receipts/(rid+'.json'),self.receipts/(rid+'.image')
 def retire(self,rid):
  for path in self.paths(rid):path.unlink(missing_ok=True)
 async def generate(self,rid,aid,payload,output):
  receipt,cached=self.paths(rid);accepted=False;phase='open_profile'
  try:
   if cached.is_file():
    from PIL import Image
    with Image.open(cached)as image:
     if image.format not in ('PNG','JPEG','WEBP')or image.width*image.height>40000000:raise ValueError('Invalid cached image')
     image.verify()
    if not 0<cached.stat().st_size<=24*1024**2:raise ValueError('Invalid cached image')
    await asyncio.to_thread(shutil.copyfile,cached,output);return {'ok':True,'download_variant':'original-node-cdp-cache'}
   receive=bool(payload.get('browser_receive'))
   if receipt.exists()and not receive:return {'ok':False,'accepted':None,'code':'GEMINI_BROWSER_OUTCOME_UNKNOWN'}
   if receive and not receipt.exists():return {'ok':False,'accepted':None,'code':'GEMINI_NATIVE_RECEIPT_MISSING'}
   row=await self.context(aid)
   request={'action':'receive'if receive else 'image'if payload['kind']=='image'else'text','prompt':payload.get('prompt',''),'references':payload.get('references',[]),'request_id':rid,'receipt':str(receipt),'output':str(cached)}
   response=await self.call(row['port'],request)
   accepted=True if receive else None if receipt.exists()else False
   if response.get('error'):return {'ok':False,'accepted':accepted,'code':'GEMINI_NATIVE_FAILED','phase':response.get('phase','node'),'error_type':response.get('error_type','Error')}
   result=response.get('result',{})
   if payload['kind']=='image':
    if not result.get('saved')or not cached.is_file():raise ValueError('Missing image')
    await asyncio.to_thread(shutil.copyfile,cached,output)
    return {'ok':True,'download_variant':'original-node-cdp'}
   return {'ok':True,'text':result.get('text','')}
  except Exception as exc:
   return {'ok':False,'accepted':None if receipt.exists()else accepted,'code':'GEMINI_NATIVE_FAILED','phase':phase,'error_type':type(exc).__name__}
