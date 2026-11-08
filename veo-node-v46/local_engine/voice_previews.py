"""Explicit offline preparation and read-only playback of shared preset previews."""
import asyncio,hashlib,json,os,shutil
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse
from .local_tts import engine_root,tts_status,synthesize_isolated

def install_voice_previews(app,data,lock):
 task=None;error='';verified={}
 def info():
  state=tts_status(data);root=engine_root(data)
  try:fingerprint=hashlib.sha256((root/'runtime/model-status.json').read_bytes()+b'preview-v1').hexdigest()
  except OSError:fingerprint='unprepared'
  folder=root/'previews'/fingerprint
  return state,root,folder
 def entries(state,folder):
  found=[]
  for row in state.get('voices',[]):
   key=hashlib.sha256(row['id'].encode()).hexdigest();path=folder/(key+'.wav');marker=folder/(key+'.json')
   if path.is_file() and marker.is_file():
    try:
     receipt=json.loads(marker.read_text(encoding='utf-8'));stat=path.stat();signature=(str(path),stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,receipt.get('sha256'),receipt.get('id'),row['id'])
     valid=verified.get(signature)
     if valid is None:
      valid=receipt.get('id')==row['id'] and receipt.get('sha256')==hashlib.sha256(path.read_bytes()).hexdigest()
      if len(verified)>256:verified.clear()
      verified[signature]=valid
     if valid:found.append({'id':row['id'],'url':'/local-api/tts/previews/file/'+key})
    except (ValueError,OSError):pass
  return found
 @app.get('/local-api/tts/previews/status')
 async def status():
  state,_,folder=await asyncio.to_thread(info);ready=await asyncio.to_thread(entries,state,folder)
  return {'state':'running' if task and not task.done() else 'error' if error else 'ready' if state.get('voices') and len(ready)==len(state['voices']) else 'not-prepared','ready':ready,'total':len(state.get('voices',[])),'error':error}
 async def work(root,folder,voices):
  nonlocal error
  try:
   # Do not queue unseen expensive work behind a narration request.
   if lock.locked():raise RuntimeError('Đang tạo lời đọc. Chuẩn bị mẫu sau khi hoàn tất.')
   async with lock:
    folder.mkdir(parents=True,exist_ok=True)
    for voice in voices:
     state,_,_=await asyncio.to_thread(info)
     if any(r['id']==voice for r in await asyncio.to_thread(entries,state,folder)):continue
     result=await synthesize_isolated(data,folder,[{'id':'sample','text':'Xin chào, đây là giọng đọc thử cho video của bạn.'}],voice)
     key=hashlib.sha256(voice.encode()).hexdigest()
     source=folder/result['url'].rsplit('/',1)[-1];target=folder/(key+'.wav');marker=folder/(key+'.json')
     def commit():
      os.replace(source,target);tmp=marker.with_suffix('.tmp');tmp.write_text(json.dumps({'id':voice,'sha256':result['sha256']}),encoding='utf-8');os.replace(tmp,marker)
     await asyncio.to_thread(commit)
  except asyncio.CancelledError:raise
  except Exception as exc:error=str(exc)
 @app.post('/local-api/tts/previews/prepare')
 async def start(body:dict):
  nonlocal task,error
  if task and not task.done():return await status()
  state,root,folder=await asyncio.to_thread(info)
  if not state.get('model_ready'):raise HTTPException(409,'Model VieNeu chưa sẵn sàng.')
  if lock.locked():raise HTTPException(409,'Đang tạo lời đọc. Chờ hoàn tất trước khi chuẩn bị mẫu.')
  if shutil.disk_usage(root).free<64*1024**2:raise HTTPException(507,'Cần ít nhất 64 MB trống để chuẩn bị mẫu giọng.')
  if len(await asyncio.to_thread(entries,state,folder))==len(state['voices']):return await status()
  error='';task=asyncio.create_task(work(root,folder,[r['id'] for r in state['voices']]))
  return await status()
 @app.post('/local-api/tts/previews/cancel')
 async def cancel(body:dict):
  nonlocal task,error
  if task and not task.done():
   task.cancel()
   try:await task
   except asyncio.CancelledError:pass
  error='';return await status()
 @app.get('/local-api/tts/previews/file/{key}')
 async def file(key:str):
  if len(key)!=64 or any(c not in '0123456789abcdef' for c in key):raise HTTPException(404,'Không có mẫu giọng.')
  state,_,folder=await asyncio.to_thread(info)
  if not any(r['url'].endswith('/'+key) for r in await asyncio.to_thread(entries,state,folder)):raise HTTPException(404,'Mẫu chưa chuẩn bị. Không tự tạo giọng khi nghe.')
  return FileResponse(folder/(key+'.wav'),media_type='audio/wav')

 async def shutdown():
  if task and not task.done():
   task.cancel()
   try:await task
   except asyncio.CancelledError:pass
 return shutdown
