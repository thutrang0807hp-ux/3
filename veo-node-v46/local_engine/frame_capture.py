"""Bounded local-only single-frame decoding when browser capture fails."""
import asyncio,math,shutil,tempfile,time
from pathlib import Path
from fastapi import HTTPException,Request
from fastapi.responses import Response

MAX_BYTES=500*1024**2

def install_frame_capture(app,data):
 gate=asyncio.Lock();root=Path(data)/'frame-capture-temp';root.mkdir(exist_ok=True)
 for old in root.glob('capture-*'):
  try:
   if old.is_dir()and not old.is_symlink()and time.time()-old.stat().st_mtime>3600:shutil.rmtree(old)
  except OSError:pass
 async def command(*args,timeout=30):
  proc=await asyncio.create_subprocess_exec(*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
  try:
   out,err=await asyncio.wait_for(proc.communicate(),timeout)
   if proc.returncode:raise HTTPException(422,'FFmpeg không đọc được khung từ video này. Chưa gửi AI.')
   return out
  except BaseException:
   if proc.returncode is None:proc.kill();await proc.wait()
   raise
 @app.post('/local-api/analysis/frame-capture')
 async def capture(request:Request):
  if request.headers.get('X-SceneForge-Local')!='1':raise HTTPException(403,'Chỉ dùng trong ứng dụng cục bộ.')
  if not shutil.which('ffmpeg')or not shutil.which('ffprobe'):raise HTTPException(503,'Thiếu FFmpeg/ffprobe trên máy; chưa trích được khung.')
  try:at=float(request.headers.get('X-Frame-Time',''))
  except ValueError:raise HTTPException(422,'Mốc khung không hợp lệ.')
  if not math.isfinite(at)or at<0 or at>600:raise HTTPException(422,'Mốc khung ngoài giới hạn.')
  async with gate:
   with tempfile.TemporaryDirectory(prefix='capture-',dir=root)as folder:
    source=Path(folder)/'source';size=0
    async def upload():
     nonlocal size
     with source.open('xb')as out:
      async for chunk in request.stream():
       size+=len(chunk)
       if size>MAX_BYTES:raise HTTPException(413,'Video vượt 500 MB; chưa gửi AI.')
       if shutil.disk_usage(root).free<64*1024**2:raise HTTPException(507,'Ổ đĩa còn quá ít chỗ để trích khung; chưa gửi AI.')
       out.write(chunk)
    try:await asyncio.wait_for(upload(),90)
    except asyncio.TimeoutError:raise HTTPException(408,'Đọc video cục bộ quá lâu; chưa gửi AI.')
    if not size:raise HTTPException(422,'Không có video nguồn.')
    import json
    try:
     meta=json.loads(await command(shutil.which('ffprobe'),'-v','error','-protocol_whitelist','file,pipe','-show_entries','stream=codec_type,width,height:format=duration','-of','json',str(source)))
     duration=float(meta['format']['duration']);video=next(s for s in meta['streams']if s.get('codec_type')=='video');w,h=int(video['width']),int(video['height'])
    except (ValueError,KeyError,StopIteration):raise HTTPException(422,'Không đọc được thông số video nguồn.')
    if not math.isfinite(duration)or duration<=0 or duration>600 or not 0<=at<duration or min(w,h)<=0 or w*h>33554432:raise HTTPException(422,'Video hoặc mốc khung ngoài giới hạn.')
    out=await command(shutil.which('ffmpeg'),'-v','error','-nostdin','-threads','1','-protocol_whitelist','file,pipe','-ss',str(at),'-i',str(source),'-frames:v','1','-an','-vf',"scale=w='min(1920,iw)':h='min(1920,ih)':force_original_aspect_ratio=decrease",'-c:v','mjpeg','-q:v','2','-threads','1','-f','image2pipe','pipe:1')
    if not out or len(out)>6*1024**2:raise HTTPException(422,'Khung trích ra rỗng hoặc vượt 6 MB.')
    import io
    from PIL import Image
    try:
     with Image.open(io.BytesIO(out))as image:image.verify()
    except Exception:raise HTTPException(422,'Khung trích ra không phải ảnh hợp lệ.')
    return Response(out,media_type='image/jpeg',headers={'Cache-Control':'no-store'})
