"""Same-origin loopback library endpoints. Credentials stay in the separate encrypted vault."""
from pathlib import Path
import asyncio,os,tempfile,zipfile,sqlite3
from fastapi import HTTPException,Request
from fastapi.responses import FileResponse
from .library import Library,Conflict

def install_library(app,data,busy=lambda:False):
 library=Library(data)
 async def call(fn,*args,**kwargs):
  try:return await asyncio.to_thread(fn,*args,**kwargs)
  except Conflict as e:raise HTTPException(409,str(e))
  except (ValueError,KeyError,TypeError)as e:raise HTTPException(400,str(e))
  except zipfile.BadZipFile:raise HTTPException(400,'ZIP bị hỏng hoặc không đúng định dạng.')
  except sqlite3.Error:raise HTTPException(503,'SQLite đang bận hoặc không đọc được. Dữ liệu trình duyệt vẫn được giữ.')
  except OSError as e:raise HTTPException(507,'Không hoàn tất ghi dữ liệu: '+str(e))
 def idle():
  if busy():raise HTTPException(409,'Đang có tác vụ trên máy. Đợi xong trước khi khôi phục/chuyển thư mục.')
 async def receive(request,limit):
  stage=Path(data)/'library-incoming';stage.mkdir(exist_ok=True)
  fd,name=tempfile.mkstemp(dir=stage);size=0
  try:
   with os.fdopen(fd,'wb')as f:
    async for chunk in request.stream():
     size+=len(chunk)
     if size>limit:raise HTTPException(413,'File vượt giới hạn '+str(limit//1024**2)+' MB.')
     f.write(chunk)
    f.flush();os.fsync(f.fileno())
   return Path(name)
  except BaseException:Path(name).unlink(missing_ok=True);raise
 @app.get('/local-api/library/status')
 async def status():return await call(library.status)
 @app.get('/local-api/library/snapshot')
 async def snapshot(verify:bool=False):
  snap=await call(library.snapshot)
  if verify:await call(library.verify,library.validate(snap['records'])[1])
  return snap
 @app.post('/local-api/library/snapshot')
 async def save(body:dict):return await call(library.commit,body.get('records'),body.get('revision'),mutation_id=body.get('mutation_id'))
 @app.post('/local-api/library/assets')
 async def upload(request:Request):
  tmp=await receive(request,2*1024**3)
  try:return await call(library.add_file,tmp,request.headers.get('content-type','application/octet-stream'),request.headers.get('x-content-sha256'))
  finally:tmp.unlink(missing_ok=True)
 @app.post('/local-api/library/assets/check')
 async def check_existing(body:dict):
  def check():
   h=body.get('hash');size=body.get('size');library.asset_path(h)
   if type(size)is not int or size<0:raise ValueError('Kích thước không hợp lệ.')
   with library.lock,library.db()as db:
    row=db.execute('SELECT size FROM asset WHERE hash=?',(h,)).fetchone()
    if not row or row[0]!=size:return {'exists':False}
    library.verify({h});library.lifecycle.revive(h,db)
    db.execute('INSERT OR REPLACE INTO upload_lease VALUES(?,?)',(h,__import__('time').time()+86400))
    return {'exists':True,'hash':h}
  return await call(check)
 @app.get('/local-api/library/assets/{hash}')
 async def asset(hash:str):
  try:p=library.read_asset_path(hash)
  except ValueError:raise HTTPException(400,'Mã file không hợp lệ.')
  if not p.is_file():raise HTTPException(404,'Không còn file trong kho.')
  await call(library.verify,{hash})
  return FileResponse(p,media_type='application/octet-stream')
 @app.get('/local-api/library/job-result/{rid}')
 async def saved_job_result(rid:str):
  if not getattr(library,'jobs_bridge',None):raise HTTPException(409,'Chưa có cầu nối tác vụ.')
  path=await call(library.jobs_bridge.file,rid)
  if not path:raise HTTPException(410,'Kết quả chưa được lưu hoặc đã được giải phóng.')
  with library.db()as db:row=db.execute('SELECT a.mime FROM asset a JOIN generation_job j ON j.result_hash=a.hash WHERE j.id=?',(rid,)).fetchone()
  mime=row[0]if row else'application/octet-stream';ext={'video/mp4':'.mp4','video/webm':'.webm','audio/wav':'.wav','image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}.get(mime,'.bin')
  return FileResponse(path,media_type=mime,filename='ket-qua-'+rid+ext)
 @app.get('/local-api/library/timeline-assets')
 async def timeline_assets():
  def protected():
   with library.lock,library.db()as db:return {'hashes':[r[0]for r in db.execute("SELECT DISTINCT hash FROM asset_ref WHERE db='sceneforge-editor-local' UNION SELECT hash FROM pin")]}
  return await call(protected)
 @app.post('/local-api/library/release-compacted')
 async def release_compacted(body:dict):idle();return await call(library.release_compacted,body.get('room_id'),body.get('revision'))
 @app.get('/local-api/library/storage-limits')
 async def storage_limits():
  if not getattr(library,'jobs_bridge',None):raise HTTPException(409,'Chưa có cầu nối kho.')
  return {**library.jobs_bridge.limits(),'temporary_bytes':await call(library.jobs_bridge.temporary_bytes),'free_bytes':__import__('shutil').disk_usage(library.root).free}
 @app.post('/local-api/library/storage-limits')
 async def set_storage_limits(body:dict):
  minimum=body.get('minimum_free_mb');budget=body.get('temporary_budget_mb')
  if type(minimum)is not int or not 128<=minimum<=1024*1024 or type(budget)is not int or not 0<=budget<=100*1024*1024:raise HTTPException(400,'Dung lượng trống tối thiểu 128–1048576 MB; giới hạn media từ 0 đến 104857600 MB.')
  def save():
   with library.lock,library.db()as db:db.execute("INSERT OR REPLACE INTO meta VALUES('storage_limits',?)",(__import__('json').dumps({'minimum_free_mb':minimum,'temporary_budget_mb':budget}),))
  await call(save);return {'minimum_free_mb':minimum,'temporary_budget_mb':budget}
 @app.post('/local-api/library/lifecycle/plan')
 async def lifecycle_plan(body:dict):
  idle()
  if getattr(library,'jobs_bridge',None):await call(library.jobs_bridge.sync)
  plan=await call(library.lifecycle.plan,body.get('room_id'),body.get('mode'),body.get('revision'),body.get('days',7),body.get('published',False))
  return {k:v for k,v in plan.items()if k!='records'}
 @app.post('/local-api/library/lifecycle/execute')
 async def lifecycle_execute(body:dict):
  idle()
  if getattr(library,'jobs_bridge',None):await call(library.jobs_bridge.sync)
  return await call(library.lifecycle.execute,body)
 @app.post('/local-api/library/lifecycle/approve')
 async def lifecycle_approve(body:dict):
  idle()
  if body.get('confirm')is not True:raise HTTPException(400,'Cần thao tác duyệt để dọn bản cũ.')
  if getattr(library,'jobs_bridge',None):await call(library.jobs_bridge.sync)
  def approve_versions():
   with library.lock:
    plan=library.lifecycle.plan(body.get('room_id'),'approved',body.get('revision'),0,False,body.get('targets'))
    return library.lifecycle.execute({**plan,'confirm':True,'mutation_id':body.get('mutation_id')})
  return await call(approve_versions)
 @app.get('/local-api/library/lifecycle/status')
 async def lifecycle_status(room_id:str|None=None):
  if getattr(library,'jobs_bridge',None):await call(library.jobs_bridge.adopt_receipts)
  def read():
   with library.db()as db:
    ops=[dict(zip(('op_id','room_id','mode','state','created','due','freed_bytes','errors'),r))for r in db.execute('SELECT id,room_id,mode,state,created,due,freed_bytes,errors FROM purge_op ORDER BY created DESC LIMIT 100')]
    query='SELECT id,provider,room_id,scene_id,kind,state,result_hash FROM generation_job';params=()
    if room_id is None:query+=" WHERE state NOT IN ('imported','discarded','failed','not_submitted')"
    if room_id is not None:query+=" WHERE room_id=? OR (room_id='' AND provider IN ('flow','muse','gemini-chat'))";params=(room_id,)
    query+=' ORDER BY created DESC LIMIT 1000'
    jobs=[dict(zip(('id','provider','room_id','scene_id','kind','state','result_hash'),r))for r in db.execute(query,params)]
    return {'operations':ops,'jobs':jobs,'free_bytes':__import__('shutil').disk_usage(library.root).free}
  return await call(read)
 @app.get('/local-api/library/lifecycle/detail/{op_id}')
 async def lifecycle_detail(op_id:str):return await call(library.lifecycle.operation_detail,op_id)
 @app.post('/local-api/library/lifecycle/release-backup-file')
 async def lifecycle_release_backup_file(body:dict):
  idle()
  return await call(library.lifecycle.release_backup_file,body.get('op_id'),body.get('hash'),body.get('token'),body.get('confirm'))
 @app.post('/local-api/library/lifecycle/expedite')
 async def lifecycle_expedite(body:dict):
  idle();return await call(library.lifecycle.expedite,body.get('op_id'),body.get('confirm'))
 @app.post('/local-api/library/lifecycle/cancel')
 async def lifecycle_cancel(body:dict):
  idle();return await call(library.lifecycle.cancel_delete,body.get('op_id'),body.get('confirm'))
 @app.post('/local-api/library/lifecycle/resume')
 async def lifecycle_resume(body:dict):
  idle()
  return {'operations':await call(library.lifecycle.resume)}
 @app.post('/local-api/library/lifecycle/discard')
 async def lifecycle_discard(body:dict):
  if not getattr(library,'jobs_bridge',None):raise HTTPException(409,'Chưa có cầu nối tác vụ.')
  return await call(library.jobs_bridge.discard,body.get('request_id'),body.get('confirm'))
 @app.post('/local-api/library/pin')
 async def pin(body:dict):await call(library.set_pin,body.get('hash',''),bool(body.get('pinned')),body.get('note',''));return {'ok':True}
 @app.post('/local-api/library/backup')
 async def backup():return {'name':await call(library.backup)}
 @app.post('/local-api/library/restore')
 async def restore(body:dict):idle();return await call(library.restore,body.get('name',''),body.get('revision'),body.get('allow_partial')is True)
 @app.get('/local-api/library/bundle')
 async def bundle(room_id:str|None=None,file:str|None=None):
  if file:
   if Path(file).name!=file or not file.startswith(('phong-','thu-vien-','trinh-duyet-'))or not file.endswith('.zip'):raise HTTPException(400,'Tên ZIP không hợp lệ.')
   p=library.root/('sao-luu'if file.startswith('trinh-duyet-')else 'cache')/file
   if not p.is_file():raise HTTPException(404,'ZIP không còn trong cache.')
  else:p=await call(library.bundle,room_id)
  return FileResponse(p,filename=p.name,media_type='application/zip')
 @app.post('/local-api/library/browser-bundle')
 async def browser_bundle(body:dict):
  records=body.get('records');await call(library.validate,records)
  p=await call(library.bundle,snapshot={'format':'SceneForge-library-1','revision':0,'records':records,'pins':[]})
  dest=library.root/'sao-luu'/('trinh-duyet-'+str(__import__('time').time_ns())+'.zip');os.replace(p,dest)
  return {'name':dest.name,'url':'/local-api/library/bundle?file='+dest.name,'bytes':dest.stat().st_size}
 @app.post('/local-api/library/import')
 async def import_bundle(request:Request):
  idle()
  try:revision=int(request.headers.get('x-library-revision','-1'))
  except ValueError:raise HTTPException(400,'Thiếu phiên bản thư viện.')
  tmp=await receive(request,4*1024**3)
  try:return await call(library.import_bundle,tmp,revision)
  finally:tmp.unlink(missing_ok=True)
 @app.get('/local-api/library/cleanup')
 async def plan():return await call(library.cleanup_plan)
 @app.post('/local-api/library/cleanup')
 async def clean(body:dict):idle();return await call(library.cleanup,body.get('token'))
 @app.post('/local-api/library/output')
 async def output(body:dict):return await call(library.set_output,body.get('path',''))
 @app.post('/local-api/library/open-root')
 async def open_root(body:dict):
  import sys,subprocess
  folder=library.root
  try:
   if os.name=='nt':os.startfile(str(folder))
   elif sys.platform=='darwin':subprocess.Popen(['open',str(folder)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   else:subprocess.Popen(['xdg-open',str(folder)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  except OSError:raise HTTPException(409,'Chưa mở được thư mục: '+str(folder))
  return {'path':str(folder)}
 @app.post('/local-api/library/open-export')
 async def open_export(body:dict):
  import sys,subprocess
  folder=await call(library.export_folder,str(body.get('room_id','')))
  try:
   if os.name=='nt':os.startfile(str(folder))
   elif sys.platform=='darwin':subprocess.Popen(['open',str(folder)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   else:subprocess.Popen(['xdg-open',str(folder)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  except OSError:raise HTTPException(409,'Chưa mở được cửa sổ thư mục. Đường dẫn: '+str(folder))
  return {'path':str(folder)}
 @app.get('/local-api/library/cache')
 async def cache_plan():return await call(library.cache_plan)
 @app.post('/local-api/library/cache')
 async def cache_clean(body:dict):idle();return await call(library.clean_cache,body.get('token'))
 @app.post('/local-api/library/relocate')
 async def relocate(body:dict):idle();return await call(library.relocate,body.get('path',''),body.get('revision'))
 return library
