"""Bounded public video intake. Downloads are temporary until the browser checkpoints them."""
import asyncio, hashlib, ipaddress, json, math, re, shutil, socket, time, uuid
from pathlib import Path
from urllib.parse import urlsplit, urljoin, urlunsplit
import httpx
from fastapi import HTTPException
from fastapi.responses import FileResponse

MAX_BYTES=500*1024**2
# Inputs plus merged output can coexist during muxing.
TEMP_BYTES=2*MAX_BYTES
PLATFORMS=('youtube.com','youtu.be','tiktok.com','instagram.com','facebook.com','fb.watch','douyin.com')

def checked_url(value):
 if not isinstance(value,str) or len(value)>4096:raise ValueError('Link video không hợp lệ.')
 p=urlsplit(value.strip())
 if p.scheme not in ('https','http') or not p.hostname or p.username or p.password or p.port not in (None,80,443):raise ValueError('Chỉ nhận link HTTP/HTTPS công khai, không kèm tài khoản.')
 return urlunsplit((p.scheme,p.netloc,p.path,p.query,''))

async def public_url(value):
 value=checked_url(value);p=urlsplit(value)
 try:rows=await asyncio.get_running_loop().getaddrinfo(p.hostname,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM)
 except OSError:raise ValueError('Không tìm thấy máy chủ video.') from None
 if not rows or any(not ipaddress.ip_address(row[4][0]).is_global for row in rows):raise ValueError('Không nhận link vào mạng nội bộ hoặc máy cục bộ.')
 return value

def tiktok_watermark_kind(fmt):
 """Extractor evidence only; never claim to have inspected video pixels."""
 note=str(fmt.get('format_note')or'').lower();fid=str(fmt.get('format_id')or'').lower()
 if fmt.get('has_watermark')is True:return 'watermarked'
 if re.search(r'\bwatermarked\b',note)and not re.search(r'(?:no|not|without)[ -]+watermark',note):return 'watermarked'
 if fmt.get('has_watermark')is False:return 'declared_unwatermarked'
 if fid=='play'or fid.startswith('play_addr')or 'direct video'in note or 'playback video'in note:return 'playback'
 return 'unknown'

def supported_video_size(fmt):
 """1080p landscape or portrait; unknown dimensions are checked after download."""
 try:w,h=float(fmt.get('width')or 0),float(fmt.get('height')or 0)
 except (TypeError,ValueError):return False
 if not math.isfinite(w)or not math.isfinite(h)or min(w,h)<0:return False
 return min(w,h)<=1080 and max(w,h)<=1920

def video_format_sets(pool):
 limited=[f for f in pool if supported_video_size(f)]
 muxed=[f for f in limited if f.get('vcodec')not in (None,'none')and f.get('acodec')not in (None,'none')]
 videos=[f for f in limited if f.get('vcodec')not in (None,'none')and f.get('acodec')=='none']
 audios=[f for f in pool if f.get('acodec')not in (None,'none')and f.get('vcodec')=='none']
 incomplete=[f for f in limited if f.get('vcodec')!='none'and f.get('acodec')!='none'and(not f.get('vcodec')or not f.get('acodec'))]
 return muxed,videos,audios,incomplete

class PublicNetwork:
 """Pin every TCP connection to a checked public address, including redirects."""
 def __init__(self):
  from httpcore._backends.auto import AutoBackend
  self.backend=AutoBackend()
 async def connect_tcp(self,host,port,timeout=None,local_address=None,socket_options=None):
  name=host.decode() if isinstance(host,bytes) else host
  rows=await asyncio.get_running_loop().getaddrinfo(name,port,type=socket.SOCK_STREAM)
  if not rows or any(not ipaddress.ip_address(r[4][0]).is_global for r in rows):raise ValueError('Không tải từ mạng nội bộ.')
  return await self.backend.connect_tcp(rows[0][4][0],port,timeout,local_address,socket_options)
 async def connect_unix_socket(self,*args,**kwargs):raise ValueError('Không nhận socket nội bộ.')
 async def sleep(self,seconds):await asyncio.sleep(seconds)

def public_transport():
 import httpcore
 transport=httpx.AsyncHTTPTransport(retries=0)
 transport._pool=httpcore.AsyncConnectionPool(network_backend=PublicNetwork())
 return transport

class VideoImport:
 def __init__(self,root,budget=None):
  self.budget=budget
  self.root=Path(root)/'video-import';self.root.mkdir(parents=True,exist_ok=True)
  self.jobs={};self.tasks={};self.processes={}
  # Files from an interrupted import have no live browser consumer.
  for p in self.root.iterdir():
   if p.is_file():p.unlink(missing_ok=True)
 @property
 def reserved_bytes(self):return sum(max(0,TEMP_BYTES-self.jobs[jid].get('bytes',0))for jid in self.tasks if jid in self.jobs)
 def cleanup(self):
  for jid,j in list(self.jobs.items()):
   if jid not in self.tasks and time.time()-j['at']>3600:
    self.remove_files(jid);self.jobs.pop(jid,None)
 def path(self,jid):return self.root/(jid+'.video')
 def remove_files(self,jid):
  for suffix in ('.video','.picture','.audio','.merged'):(self.root/(jid+suffix)).unlink(missing_ok=True)
 def get(self,jid):
  self.cleanup()
  if jid not in self.jobs:raise HTTPException(404,'Lượt nhập đã hết hạn; chọn lại nguồn.')
  return self.jobs[jid]
 async def create(self,body):
  self.cleanup()
  try:url=await public_url(body.get('url'))
  except (ValueError,TypeError):raise HTTPException(400,'Cần link video HTTP/HTTPS công khai, không phải địa chỉ nội bộ.') from None
  if not shutil.which('ffprobe') or not shutil.which('ffmpeg'):raise HTTPException(409,'Cần cài FFmpeg/ffprobe trong động cơ local trước khi tải video. Vẫn có thể chọn file trên máy.')
  key=hashlib.sha256(url.encode()).hexdigest()
  for j in self.jobs.values():
   if j['url_key']==key and j['state'] in ('queued','running','done'):return dict(j)
  if len(self.tasks)>=2:raise HTTPException(409,'Đang nhập hai video. Chờ xong rồi nhập tiếp.')
  if sum(self.path(jid).stat().st_size for jid in self.jobs if self.path(jid).exists())>MAX_BYTES*2:raise HTTPException(409,'Lưu hoặc bỏ các video đã tải trước khi nhập thêm.')
  if shutil.disk_usage(self.root).free<TEMP_BYTES+256*1024**2:raise HTTPException(507,'Cần ít nhất 1,3 GB trống để tải video an toàn.')
  if self.budget:self.budget(TEMP_BYTES)
  jid=str(uuid.uuid4());j={'id':jid,'state':'queued','phase':'Chờ đọc link','bytes':0,'at':time.time(),'url_key':key};self.jobs[jid]=j
  self.tasks[jid]=asyncio.create_task(self.run(jid,url));return dict(j)
 async def subprocess(self,jid,*args):
  proc=await asyncio.create_subprocess_exec(*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL);self.processes[jid]=proc
  try:
   stdout,_=await asyncio.wait_for(proc.communicate(),75)
   if proc.returncode or len(stdout)>8*1024**2:raise ValueError('Không đọc được video công khai. Trang có thể yêu cầu đăng nhập; hãy tải file rồi nhập vào app.')
   return stdout
  finally:
   if proc.returncode is None:
    proc.kill();await proc.wait()
   self.processes.pop(jid,None)
 async def resolve(self,jid,url):
  p=urlsplit(url);host=p.hostname.lower()
  if p.path.lower().endswith(('.mp4','.webm','.mov','.m4v')):return url,{},{}
  if not any(host==h or host.endswith('.'+h) for h in PLATFORMS):raise ValueError('Link này chưa hỗ trợ. Dùng link file MP4/WebM hoặc tải file rồi nhập.')
  import sys,importlib.util
  if not importlib.util.find_spec('yt_dlp'):raise ValueError('Thiếu yt-dlp. Chạy lại bước cài động cơ local; vẫn có thể nhập file.')
  raw=await self.subprocess(jid,sys.executable,'-m','yt_dlp','--ignore-config','--no-playlist','--skip-download','--dump-single-json','--no-cache-dir','--retries','0','--extractor-retries','0','--socket-timeout','15',url)
  info=json.loads(raw)
  if info.get('_type') in ('playlist','multi_video') or float(info.get('duration') or 0)>600:raise ValueError('Chọn một video tối đa 10 phút, không phải danh sách.')
  tiktok=host=='tiktok.com'or host.endswith('.tiktok.com')or str(info.get('extractor_key')or info.get('extractor')or'').lower().startswith('tiktok')
  formats=info.get('formats') or [info]
  # Some extractors omit codecs/protocol for an ordinary MP4 (notably TikTok).
  # Missing codec metadata is not the same as an explicit audio-only/video-only stream.
  if jid in self.jobs:
   self.jobs[jid]['source_diagnostics']={'extractor':str(info.get('extractor_key')or info.get('extractor')or'')[:80],'format_count':len(formats),'formats':[{'protocol':f.get('protocol'),'vcodec':f.get('vcodec'),'acodec':f.get('acodec'),'height':f.get('height'),'ext':f.get('ext'),'has_url':bool(f.get('url')),'has_drm':bool(f.get('has_drm')),'fragmented':bool(f.get('fragments')),'tiktok_source_kind':tiktok_watermark_kind(f)if tiktok else None}for f in formats[:30]]}
  direct=[f for f in formats if f.get('url') and (f.get('protocol')or urlsplit(f['url']).scheme) in ('http','https') and not f.get('has_drm') and not f.get('fragments') and not urlsplit(f['url']).path.lower().endswith(('.m3u8','.mpd')) and (f.get('filesize') or 0)<=MAX_BYTES]
  if tiktok:
   direct=[f for f in direct if f.get('vcodec')!='bytevc2' and 'unplayable'not in str(f.get('format_note')or'').lower()]
   audio_only=[f for f in direct if f.get('vcodec')=='none']
   preferred=[f for f in direct if tiktok_watermark_kind(f)in ('playback','declared_unwatermarked')]
   not_marked=[f for f in direct if tiktok_watermark_kind(f)!='watermarked']
   # Select a usable source tier before resolution; an HD download logo must not
   # outrank a lower-resolution playback file or a playback split stream.
   for pool in (preferred+audio_only,not_marked,direct):
    sets=video_format_sets(pool)
    if sets[0]or(sets[1]and sets[2])or sets[3]:direct=pool;break
  muxed,videos,audios,incomplete=video_format_sets(direct)
  def headers(f):
   # Extractor credentials must not be forwarded.
   return {k:v for k,v in (f.get('http_headers') or info.get('http_headers') or {}).items() if k.lower() in ('user-agent','referer')}
  meta={'title':str(info.get('title') or 'Video')[:160],'source_size_limit':'1080p'}
  if muxed:
   f=max(muxed,key=lambda x:(x.get('height') or 0,x.get('tbr') or 0))
  elif videos and audios:
   f=max(videos,key=lambda x:(x.get('height') or 0,x.get('tbr') or 0))
   audio=max(audios,key=lambda x:(x.get('abr') or 0,x.get('tbr') or 0))
   if (f.get('filesize') or 0)+(audio.get('filesize') or 0)>MAX_BYTES:raise ValueError('Video và âm thanh vượt tổng giới hạn 500 MB.')
   meta['_audio']={'url':await public_url(audio['url']),'headers':headers(audio)}
  elif incomplete:
   f=max(incomplete,key=lambda x:(x.get('height')or 0,x.get('tbr')or 0))
   meta['codec_metadata_incomplete']=True
   if jid in self.jobs:self.jobs[jid]['phase']='Nguồn thiếu thông tin codec · đang tải để kiểm tra tệp thật'
  else:raise ValueError('Chưa chọn được nguồn tải trong '+str(len(formats))+' định dạng. App chỉ nhận tệp HTTP hoàn chỉnh hoặc luồng hình/tiếng HTTP riêng; xem báo cáo nguồn để biết định dạng trả về.')
  if tiktok:
   kind=tiktok_watermark_kind(f);meta['tiktok_source_kind']=kind;meta['tiktok_source_policy']='playback-v1'
   meta['watermark_pixels_checked']=False
   if kind=='watermarked':meta['source_notice']='Nguồn TikTok chỉ có bản được đánh dấu có watermark. Video đã tải giữ logo; app chưa xóa logo khỏi hình.'
   elif kind=='unknown':meta['source_notice']='Chưa xác nhận được bản TikTok không logo; app giữ tệp nguồn tải được, chưa xóa logo khỏi hình.'
   if jid in self.jobs:
    self.jobs[jid]['source_diagnostics']['tiktok_source_kind']=kind
    fid=str(f.get('format_id')or'')
    self.jobs[jid]['source_diagnostics']['selected_format_id']=fid if re.fullmatch(r'[A-Za-z0-9_.:-]{0,80}',fid)else''
  meta['selected_height']=f.get('height')
  return await public_url(f['url']),headers(f),meta
 async def merge(self,jid,video,audio):
  self.jobs[jid].update(phase='Đang ghép hình và tiếng trên máy')
  for source in (video,audio):
   with source.open('rb') as stream:header=stream.read(32)
   if not(header[4:8]==b'ftyp' or header[:4]==b'\x1aE\xdf\xa3'):raise ValueError('Luồng tải về không phải tệp MP4/M4A/WebM thật.')
  output=self.root/(jid+'.merged')
  await self.subprocess(jid,'ffmpeg','-nostdin','-y','-v','error','-protocol_whitelist','file,pipe','-i',str(video),'-protocol_whitelist','file,pipe','-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-fs',str(MAX_BYTES+1),'-movflags','+faststart','-f','mp4',str(output))
  if not output.exists() or not 0<output.stat().st_size<=MAX_BYTES:raise ValueError('Video sau ghép vượt 500 MB hoặc ghép chưa thành công.')
  output.replace(self.path(jid))
  digest=hashlib.sha256()
  with self.path(jid).open('rb') as source:
   for chunk in iter(lambda:source.read(1024**2),b''):digest.update(chunk)
  return digest.hexdigest()
 async def download(self,jid,url,headers,destination=None):
  job=self.jobs[jid];digest=hashlib.sha256()
  async with httpx.AsyncClient(follow_redirects=False,trust_env=False,transport=public_transport(),timeout=httpx.Timeout(30,read=45)) as client:
   for _ in range(6):
    url=await public_url(url)
    async with client.stream('GET',url,headers=headers) as response:
     if response.status_code in (301,302,303,307,308):
      url=urljoin(url,response.headers.get('location',''));continue
     if response.status_code!=200:raise ValueError('Máy chủ không cho tải video. Hãy nhập file đã tải trên máy.')
     try:length=int(response.headers.get('content-length','0'))
     except ValueError:length=0
     if length>MAX_BYTES:raise ValueError('Video vượt 500 MB.')
     with (destination or self.path(jid)).open('wb') as out:
      async for chunk in response.aiter_bytes(256*1024):
       if job['bytes']+len(chunk)>MAX_BYTES:raise ValueError('Video vượt 500 MB.')
       if self.budget and job['bytes']//(16*1024**2)!=(job['bytes']+len(chunk))//(16*1024**2):self.budget(0)
       out.write(chunk);digest.update(chunk);job.update(bytes=job['bytes']+len(chunk),phase=job.get('download_phase','Đang tải video'),at=time.time())
     return digest.hexdigest()
   raise ValueError('Link chuyển hướng quá nhiều lần.')
 async def run(self,jid,url):
  j=self.jobs[jid];j.update(state='running',phase='Đang đọc nguồn công khai')
  try:
   async with asyncio.timeout(600):
    url,headers,meta=await self.resolve(jid,url)
    audio=meta.pop('_audio',None)
    if audio:
     video_path=self.root/(jid+'.picture');audio_path=self.root/(jid+'.audio')
     j['download_phase']='Đang tải phần hình';await self.download(jid,url,headers,video_path)
     j['download_phase']='Đang tải phần tiếng';await self.download(jid,audio['url'],audio['headers'],audio_path)
     digest=await self.merge(jid,video_path,audio_path)
     video_path.unlink(missing_ok=True);audio_path.unlink(missing_ok=True);j.pop('download_phase',None)
     j['merged_audio']=True
    else:digest=await self.download(jid,url,headers)
    with self.path(jid).open('rb')as source:header=source.read(32)
    if not(header[4:8]==b'ftyp' or header[:4]==b'\x1aE\xdf\xa3'):raise ValueError('Chỉ nhận tệp MP4/MOV/WebM thật, không phải trang web hoặc danh sách phát.')
    raw=await self.subprocess(jid,'ffprobe','-protocol_whitelist','file,pipe','-v','error','-show_format','-show_streams','-of','json',str(self.path(jid)))
    info=json.loads(raw);video=next((s for s in info.get('streams',[]) if s.get('codec_type')=='video'),None);seconds=float(info.get('format',{}).get('duration') or 0)
    if j.get('merged_audio') and not any(stream.get('codec_type')=='audio' for stream in info.get('streams',[])):raise ValueError('Video sau ghép chưa có tiếng.')
    if not video or not 0<seconds<=600:raise ValueError('Nguồn không phải video hợp lệ từ 0 đến 10 phút.')
    if meta.get('source_size_limit')and not supported_video_size(video):raise ValueError('Tệp thực tế vượt giới hạn 1080p: tối đa 1920×1080 hoặc 1080×1920.')
    ext='webm' if 'webm' in info.get('format',{}).get('format_name','') else 'mp4'
    j.update(state='done',phase='Đã tải · chờ lưu vào dự án',sha256=digest,duration=seconds,width=video.get('width'),height=video.get('height'),name='video-'+digest[:12]+'.'+ext,mime='video/webm' if ext=='webm' else 'video/mp4',**meta)
  except asyncio.CancelledError:j.update(state='cancelled',phase='Đã bỏ lượt tải');self.remove_files(jid)
  except Exception as e:
   j.update(state='error',phase='Chưa nhập được video',error=str(e.detail) if isinstance(e,HTTPException) else str(e) if isinstance(e,ValueError) else 'Tải video bị ngắt hoặc quá thời gian. Có thể chọn file trên máy.');self.remove_files(jid)
  finally:j['at']=time.time();self.tasks.pop(jid,None)
 async def release(self,jid):
  self.get(jid);task=self.tasks.get(jid)
  if task:
   task.cancel()
   try:await task
   except asyncio.CancelledError:pass
  self.tasks.pop(jid,None);self.remove_files(jid);self.jobs.pop(jid,None)
  return {'released':True}
 async def close(self):
  for jid in list(self.tasks):await self.release(jid)

def install_video_import(app,root,budget=None):
 service=VideoImport(root,budget)
 @app.post('/local-api/video-import/jobs')
 async def create(body:dict):return await service.create(body)
 @app.get('/local-api/video-import/jobs')
 async def listing():
  service.cleanup();return {'jobs':[dict(j) for j in service.jobs.values()]}
 @app.get('/local-api/video-import/jobs/{jid}')
 async def status(jid:str):return dict(service.get(jid))
 @app.get('/local-api/video-import/jobs/{jid}/file')
 async def file(jid:str):
  j=service.get(jid)
  if j['state']!='done' or not service.path(jid).is_file():raise HTTPException(409,'Video chưa tải xong.')
  return FileResponse(service.path(jid),media_type=j['mime'],filename=j['name'])
 @app.post('/local-api/video-import/jobs/{jid}/release')
 async def release(jid:str,body:dict):return await service.release(jid)
 return service
