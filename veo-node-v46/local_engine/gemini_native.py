"""Thin launcher for the user's original Node/CDP Gemini connector (75f43c9).
Python maps account profiles to the original GeminiWorkspace; its create_image/request/start methods run unchanged.
"""
import asyncio,hashlib,json,os,shutil,tempfile,zipfile
from pathlib import Path
from fastapi import HTTPException

ROOT=Path(__file__).resolve().parents[1]

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
     for item in z.infolist():
      if os.name=='nt'or item.filename!='runtime/node.exe':z.extract(item,tmp)
    (Path(tmp)/'.ready').write_text(digest)
    if folder.exists():shutil.rmtree(folder)
    shutil.move(tmp,folder)
  return folder
 async def runtime(self):
  async with self.runtime_lock:
   if self.runtime_path is None:self.runtime_path=await asyncio.to_thread(self.unpack)
   return self.runtime_path
 async def context(self,aid):
  old=self.contexts.get(aid)
  if old and old['workspace'].browser is not None and old['workspace'].browser.poll()is None:return old
  if old:self.contexts.pop(aid);old['lease'].release()
  from .browser_profiles import profiles
  manager=profiles(self.service.vault,self.service.data);entry=manager.registry().get(aid)
  if not entry:raise HTTPException(409,'Đăng nhập Gemini trong Cài đặt trước khi tạo ảnh.')
  runtime=await self.runtime();lease=manager.lease(entry)
  if lease.locked():raise HTTPException(409,'Đóng cửa sổ đăng nhập Gemini do app mở trước khi chạy nền.')
  await lease.acquire()
  try:
   import importlib.util
   spec=importlib.util.spec_from_file_location('sceneforge_repo_'+hashlib.sha256(aid.encode()).hexdigest()[:12],runtime/'repo_bridge.py')
   repo=importlib.util.module_from_spec(spec);spec.loader.exec_module(repo)
   cfg=manager.settings(entry)
   repo.discover_chrome=lambda:Path(cfg['executable'])
   class Workspace(repo.GeminiWorkspace):
    references=();request_id='';request_ratio='9:16'
    def request(self,action,**values):
     if action in ('image','text'):values.update(references=list(self.references),request_id=self.request_id,ratio=self.request_ratio)
     return super().request(action,**values)
   folder=Path(self.service.data)/'gemini-repo-workspaces'/aid;folder.mkdir(parents=True,exist_ok=True)
   workspace=Workspace(folder);workspace.profile=manager.path(entry['service'],entry['key'])
   await asyncio.to_thread(workspace.start)
   row={'workspace':workspace,'port':workspace.port,'process':workspace.browser,'lease':lease};self.contexts[aid]=row;return row
  except BaseException:lease.release();raise
 async def close_account(self,aid):
  row=self.contexts.get(aid)
  if not row:return
  await asyncio.to_thread(row['workspace'].close)
  if row['workspace'].browser is not None and row['workspace'].browser.poll()is None:raise HTTPException(409,'Chrome riêng chưa đóng xong; thử lại sau.')
  self.contexts.pop(aid,None);row['lease'].release()
 async def close(self):
  for aid in list(self.contexts):
   try:await self.close_account(aid)
   except Exception:pass
 async def verify(self,aid):
  row=await self.context(aid)
  await asyncio.to_thread(row['workspace'].verify)
 def paths(self,rid):
  self.service.valid_id(rid)
  return self.receipts/(rid+'.json'),self.receipts/(rid+'.image')
 def retire(self,rid):
  for path in self.paths(rid):
   try:path.unlink(missing_ok=True)
   except OSError:pass
 async def generate(self,rid,aid,payload,output):
  _,cached=self.paths(rid);accepted=False;phase='open_profile'
  try:
   if cached.is_file():
    accepted=True
    from PIL import Image
    with Image.open(cached)as image:
     if image.format not in ('PNG','JPEG','WEBP')or image.width*image.height>40000000:raise ValueError('Invalid cached image')
     image.verify()
    await asyncio.to_thread(shutil.copyfile,cached,output);return {'ok':True,'download_variant':'repo-original-cache'}
   if payload.get('browser_receive'):return {'ok':False,'accepted':None,'code':'GEMINI_NATIVE_RECEIPT_MISSING'}
   row=await self.context(aid);workspace=row['workspace'];accepted=None;phase='repository_request'
   def invoke():
    workspace.references=payload.get('references',[]);workspace.request_id=rid;workspace.request_ratio=payload.get('ratio')or'9:16'
    try:return workspace.create_image(payload['prompt'])if payload['kind']=='image'else workspace.request('text',prompt=payload['prompt'])
    finally:workspace.references=()
   if payload['kind']=='image':
    data=await asyncio.to_thread(invoke)
    await asyncio.to_thread(cached.write_bytes,data)
    await asyncio.to_thread(shutil.copyfile,cached,output)
    return {'ok':True,'download_variant':'repo-original-create-image'}
   result=await asyncio.to_thread(invoke)
   return {'ok':True,'text':result.get('text','')}
  except Exception as exc:
   if type(exc).__name__=='WorkspaceError'and str(exc)=='GEMINI_BROWSER_ATTACH_FAILED':
    return {'ok':False,'accepted':False,'code':'GEMINI_BROWSER_ATTACH_FAILED','phase':'attach_references','error_type':'WorkspaceError','provider_message':'Chưa đính kèm đủ ảnh tham chiếu; prompt chưa được gửi.'}
   return {'ok':False,'accepted':accepted,'code':'GEMINI_NATIVE_FAILED','phase':phase,'error_type':type(exc).__name__,**({'provider_message':str(exc).splitlines()[0][:300]}if type(exc).__name__=='WorkspaceError'else{})}
