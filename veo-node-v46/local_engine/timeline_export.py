"""Offline timeline rendering. All inputs are uploaded bytes; never accept source paths/URLs."""
import asyncio, json, math, re, shutil, time, uuid
from pathlib import Path
from .local_jobs import LocalJobs,JobRegistry,job_room
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse

LIMIT=512*1024*1024
FILTER_FILE_MODE={}

def unsupported_filter_option(error,option):
 text=error.decode(errors='replace')
 return ("Unrecognized option '"+option.lstrip('-')+"'")in text or ("Option not found: "+option.lstrip('-'))in text

def number(obj,key,default,lo,hi):
 value=obj.get(key,default)
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not lo<=value<=hi:
  raise ValueError('Giá trị '+key+' không hợp lệ.')
 return value

def validate(body):
 if not isinstance(body,dict):raise ValueError('Timeline phải là một đối tượng.')
 w=number(body,'width',1080,240,1920);h=number(body,'height',1920,240,1920)
 if int(w)!=w or int(h)!=h or w%2 or h%2:raise ValueError('Kích thước khung phải là số chẵn.')
 fps=number(body,'fps',30,30,60)
 if fps not in (30,60):raise ValueError('Chỉ nhận 30 hoặc 60 fps.')
 rows=body.get('clips')
 if not isinstance(rows,list) or not 1<=len(rows)<=120:raise ValueError('Cần từ 1 đến 120 mục trên timeline.')
 clean=[]
 for row in rows:
  if not isinstance(row,dict):raise ValueError('Mục timeline không hợp lệ.')
  r={};r['kind']=row.get('kind')
  if r['kind'] not in ('video','audio','image'):raise ValueError('Chữ phải được đóng gói thành lớp ảnh trong suốt.')
  key=row.get('asset')
  if not isinstance(key,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',key):raise ValueError('Mã tư liệu không hợp lệ.')
  r['asset']=key;r['track']=str(row.get('track',''))[:80]
  for k,d,lo,hi in [('start',0,0,600),('duration',1,.02,600),('mediaIn',0,0,36000),('speed',1,.25,3),('opacity',1,0,1),('scale',1,.1,4),('rotation',0,-360,360),('x',0,-100,100),('y',0,-100,100),('volume',1,0,20),('fadeIn',0,0,600),('fadeOut',0,0,600),('transitionDuration',.5,.01,5)]:r[k]=number(row,k,d,lo,hi)
  r['transition']=row.get('transition','none')
  if r['transition'] not in ('none','fade','dissolve','slide','wipe'):raise ValueError('Chuyển cảnh chưa được hỗ trợ bởi FFmpeg.')
  r['direction']=row.get('direction','left')
  if r['direction'] not in ('left','right','up','down'):raise ValueError('Hướng chuyển cảnh không hợp lệ.')
  if row.get('easing','linear')!='linear':raise ValueError('FFmpeg chưa hỗ trợ đường cong chuyển cảnh này. Chọn Tuyến tính hoặc dùng bản ghi trình duyệt.')
  if row.get('keyframes'):raise ValueError('FFmpeg chưa hỗ trợ keyframe. Dùng bản ghi trình duyệt để giữ chuyển động.')
  if row.get('look','none')!='none' or any(row.get(k,d)!=d for k,d in [('brightness',100),('contrast',100),('saturation',100),('temperature',0),('blur',0)]):raise ValueError('FFmpeg chưa khớp bộ lọc màu này. Dùng bản ghi trình duyệt để giữ màu hiện tại.')
  if row.get('audioBypass',True) is False:raise ValueError('FFmpeg chưa khớp bộ effect âm thanh nâng cao. Dùng bản ghi trình duyệt hoặc tắt effect trên clip.')
  r['fit']='cover' if row.get('fit')=='cover' else 'contain'
  for k in ('flipX','flipY','muted'):r[k]=bool(row.get(k,False))
  r['preservePitch']=row.get('preservePitch',True) is not False
  r['bytes']=int(number(row,'bytes',0,12,LIMIT))
  clean.append(r)
 end=max(r['start']+r['duration'] for r in clean)
 duration=number(body,'duration',end,end,600)
 if duration>600:raise ValueError('Bản dựng FFmpeg hiện hỗ trợ tối đa 10 phút.')
 expected={}
 for r in clean:
  if r['asset'] in expected and expected[r['asset']]!=r['bytes']:raise ValueError('Kích thước tư liệu không nhất quán.')
  expected[r['asset']]=r['bytes']
 if sum(expected.values())>LIMIT:raise ValueError('Tổng tư liệu vượt 512 MB.')
 return {'width':int(w),'height':int(h),'fps':fps,'clips':clean,'duration':duration,'expected':expected,'normalize':body.get('normalize',True) is not False}

async def probe(path):
 p=await asyncio.create_subprocess_exec(shutil.which('ffprobe'),'-v','error','-protocol_whitelist','file,pipe','-show_streams','-show_format','-of','json',str(path),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
 try:out,_=await asyncio.wait_for(p.communicate(),20)
 finally:
  if p.returncode is None:p.kill();await p.wait()
 if p.returncode:raise ValueError('FFmpeg không đọc được tư liệu đã gửi.')
 data=json.loads(out)
 for s in data.get('streams',[]):
  if s.get('codec_type')=='video' and s.get('width',0)*s.get('height',0)>33_600_000:raise ValueError('Tư liệu vượt giới hạn 33,6 triệu điểm ảnh.')
 return data

def graph(model,metas):
 """Composite around original cut positions: transitions never shorten the timeline."""
 w,h,fps,duration=[model[k]for k in ('width','height','fps','duration')];rows=model['clips'];filters=[f'color=c=0x090a0c:s={w}x{h}:r={fps}:d={duration}[base]'];base='base';audios=[]
 for n,r in enumerate(rows):
  if r['kind']=='audio':continue
  before=after=None
  for x in rows:
   if x['kind']=='audio' or x['track']!=r['track'] or x is r:continue
   if abs(x['start']+x['duration']-r['start'])<.001:before=x
   if abs(r['start']+r['duration']-x['start'])<.001:after=x
  incoming=before and before['transition'] in ('dissolve','slide','wipe');outgoing=after and r['transition'] in ('dissolve','slide','wipe')
  pre=min(before['transitionDuration'],before['duration'],r['duration'])/2 if incoming else 0
  post=min(r['transitionDuration'],r['duration'],after['duration'])/2 if outgoing else 0
  begin=r['start']-pre;length=r['duration']+pre+post;source=r['mediaIn']-pre*r['speed'];pad=max(0,-source/r['speed'])
  # Retain a hidden guard frame past the enabled interval so EOF cannot drop
  # the last visible frame. Keep EOF repetition off for finite base timelines.
  chain=[f'trim=start={max(0,source)}',f'setpts=(PTS-STARTPTS)/{r["speed"]}',f'fps={fps}',f'tpad=start_mode=clone:start_duration={pad}:stop_mode=clone:stop_duration={length}',f'trim=duration={length+1/fps}']
  fit='increase' if r['fit']=='cover' else 'decrease'
  chain+=[f'scale={w}:{h}:force_original_aspect_ratio={fit}:force_divisible_by=2', 'setsar=1','format=rgba']
  if r['fit']=='cover':chain+=[f'crop={w}:{h}']
  else:chain+=[f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black@0']
  chain+=[f'scale=trunc(iw*{r["scale"]}/2)*2:trunc(ih*{r["scale"]}/2)*2']
  if r['flipX']:chain+=['hflip']
  if r['flipY']:chain+=['vflip']
  if r['rotation']:chain+=[f'rotate={r["rotation"]}*PI/180:ow=rotw({r["rotation"]}*PI/180):oh=roth({r["rotation"]}*PI/180):c=black@0']
  if r['opacity']!=1:chain+=[f'colorchannelmixer=aa={r["opacity"]}']
  x=f'(W-w)/2+W*{r["x"]}/100';y=f'(H-h)/2+H*{r["y"]}/100'
  if incoming and before['transition']=='dissolve':chain+=[f'fade=t=in:st=0:d={pre*2}:alpha=1']
  if before and before['transition']=='fade':chain+=[f'fade=t=in:st=0:d={min(before["transitionDuration"],before["duration"],r["duration"])/2}:alpha=1']
  if after and r['transition']=='fade':
   d=min(r['transitionDuration'],r['duration'],after['duration'])/2;chain+=[f'fade=t=out:st={length-d}:d={d}:alpha=1']
  if incoming and before['transition']=='wipe':
   p=f'min(1,max(0,T/{pre*2}))';direction=before['direction'];cond={'left':f'gte(X,W*(1-({p})))','right':f'lte(X,W*({p}))','up':f'gte(Y,H*(1-({p})))','down':f'lte(Y,H*({p}))'}[direction]
   chain+=[f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*({cond})'"]
  if incoming and before['transition']=='slide':
   p=f'min(1,max(0,(t-{begin})/{pre*2}))';axis='x' if before['direction'] in ('left','right')else 'y';offset=f'{"W"if axis=="x"else"H"}*(1-({p}))*{1 if before["direction"]in ("left","up")else -1}'
   if axis=='x':x+='+'+offset
   else:y+='+'+offset
  if outgoing and r['transition']=='slide':
   d=post*2;p=f'min(1,max(0,(t-{r["start"]+r["duration"]-post})/{d}))';axis='x'if r['direction']in ('left','right')else'y';offset=f'{"W"if axis=="x"else"H"}*({p})*{-1 if r["direction"]in ("left","up")else 1}'
   if axis=='x':x+='+'+offset
   else:y+='+'+offset
  chain+=[f'setpts=PTS+{begin}/TB'];filters.append(f'[{n}:v]'+','.join(chain)+f'[v{n}]')
  filters.append(f"[{base}][v{n}]overlay=x='{x}':y='{y}':enable='gte(t,{begin-1e-7})*lt(t,{begin+length-1e-7})':eof_action=pass:repeatlast=0:format=auto[b{n}]");base=f'b{n}'
 for n,r in enumerate(rows):
  if r['kind']not in ('audio','video')or r['muted']or not r['volume']or not any(s.get('codec_type')=='audio'for s in metas[r['asset']].get('streams',[])):continue
  chain=[f'atrim=start={r["mediaIn"]}:duration={r["duration"]*r["speed"]}','asetpts=PTS-STARTPTS','aresample=48000']
  speed=r['speed']
  if r['preservePitch']:
   while speed<.5:chain+=['atempo=0.5'];speed/=.5
   while speed>2:chain+=['atempo=2'];speed/=2
   chain+=[f'atempo={speed}']
  else:chain+=[f'asetrate=48000*{speed}','aresample=48000']
  chain+=[f'apad=pad_dur={r["duration"]}',f'atrim=duration={r["duration"]}',f'volume={r["volume"]}']
  if r['fadeIn']:chain+=[f'afade=t=in:d={min(r["fadeIn"],r["duration"])}']
  if r['fadeOut']:
   d=min(r['fadeOut'],r['duration']);chain+=[f'afade=t=out:st={r["duration"]-d}:d={d}']
  # Same linear crossfade used by preview for paired transition sources.
  neighbours=[x for x in rows if x['track']==r['track']and x['kind']!='audio']
  before=next((x for x in neighbours if abs(x['start']+x['duration']-r['start'])<.001),None)
  after=next((x for x in neighbours if abs(r['start']+r['duration']-x['start'])<.001),None)
  if (before and before['transition']in ('dissolve','slide','wipe'))or(after and r['transition']in ('dissolve','slide','wipe')):
   raise ValueError('Chuyển cảnh có tiếng gốc: hãy tắt tiếng clip và dùng track âm thanh riêng để xuất FFmpeg đúng bản xem.')
  chain+=[f'adelay={round(r["start"]*1000)}:all=1'];filters.append(f'[{n}:a]'+','.join(chain)+f'[a{n}]');audios.append(f'[a{n}]')
 filters.append(f'[{base}]format=yuv420p[outv]')
 if audios:
  mix=f'amix=inputs={len(audios)}:duration=longest:normalize=0,apad,atrim=duration={duration}'
  if model['normalize']:mix+=',loudnorm=I=-16:TP=-1.5:LRA=11'
  filters.append(''.join(audios)+mix+'[outa]')
 return ';\n'.join(filters),bool(audios)

def install_timeline_exports(app,data,lock=None,store=None):
 folder=Path(data)/'timeline-exports';folder.mkdir(exist_ok=True);jobs=JobRegistry(store or LocalJobs(data),'timeline');lock=lock or asyncio.Lock()
 for p in folder.iterdir():
  if p.is_dir()and re.fullmatch('[0-9a-f]{32}',p.name)and time.time()-p.stat().st_mtime>86400:shutil.rmtree(p)
 for j in jobs.values():
  j.update(dir=folder/j['id'],received=set(),inflight=set())
  if j['state']=='done'and not(j['dir']/'output.mp4').is_file()and not(j.get('result')or{}).get('result_hash'):j.update(state='error',error='MP4 tạm không còn trên máy. Timeline và bản đã lưu trong thư viện vẫn giữ nguyên.')
 def public(j):
  elapsed=time.monotonic()-j.get('started',time.monotonic());progress=j['progress']
  return {k:j.get(k)for k in ('id','state','progress','error','bytes','duration')}|{'eta_seconds':round(elapsed*(100-progress)/progress)if j['state']=='running'and progress>0 else None,'received':list(j['received'])}
 def get(id):
  if id not in jobs:raise HTTPException(404,'FFmpeg: không còn lượt xuất này.')
  return jobs[id]
 async def render(j):
  try:
   async with lock:
    if j['state']=='cancelled':return
    j.update(state='running',started=time.monotonic());model=j['model'];metas={}
    for key in model['expected']:
     metas[key]=await probe(j['dir']/(key+'.media'))
    args=[shutil.which('ffmpeg'),'-hide_banner','-loglevel','error','-nostdin','-filter_complex_threads','1']
    for r in model['clips']:
     meta=metas[r['asset']];v=next((s for s in meta.get('streams',[])if s.get('codec_type')=='video'),None)
     if r['kind']!='audio'and not v:raise ValueError('Tư liệu hình không có luồng video/ảnh.')
     if r['kind']=='image':args+=['-loop','1','-framerate',str(model['fps'])]
     args+=['-protocol_whitelist','file,pipe','-i',str(j['dir']/(r['asset']+'.media'))]
    filters,audio=graph(model,metas);script=j['dir']/'filters.txt';script.write_text(filters)
    output_args=['-map','[outv]']
    if audio:output_args+=['-map','[outa]','-c:a','aac','-b:a','192k']
    output_args+=['-t',str(j['duration']),'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-r',str(model['fps']),'-movflags','+faststart','-progress','pipe:1','-nostats','-y',str(j['dir']/'output.part.mp4')]
    # Modern FFmpeg removed -filter_complex_script. Both file forms avoid the
    # Windows command-line length limit; retry only an unrecognized option,
    # never an encoding, source, codec or filter-graph failure.
    binary=args[0];preferred=FILTER_FILE_MODE.get(binary,'-/filter_complex')
    modes=[preferred]+[mode for mode in ('-/filter_complex','-filter_complex_script')if mode!=preferred]
    for mode in modes:
     p=await asyncio.create_subprocess_exec(*args,mode,str(script),*output_args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE);j['process']=p
     async def progress():
      while line:=await p.stdout.readline():
       if line.startswith(b'out_time_us='):
        try:j['progress']=min(99,max(0,round(float(line.split(b'=')[1])/1e6/j['duration']*100)))
        except ValueError:pass
     _,err,_=await asyncio.wait_for(asyncio.gather(progress(),p.stderr.read(),p.wait()),3600)
     if j['state']=='cancelled':return
     if not p.returncode:
      FILTER_FILE_MODE[binary]=mode;break
     if not unsupported_filter_option(err,mode):break
    if j['state']=='cancelled':return
    if p.returncode:raise ValueError('FFmpeg: không mã hóa được timeline. '+err.decode(errors='replace')[-1200:].replace(str(j['dir']),'[thư mục tạm]'))
    output=j['dir']/'output.part.mp4'
    if not output.is_file()or output.stat().st_size<500:raise ValueError('FFmpeg: không tạo được MP4 hợp lệ.')
    verified=await probe(output);video=next((s for s in verified.get('streams',[])if s.get('codec_type')=='video'),None)
    if not video or video.get('codec_name')!='h264' or video.get('width')!=model['width']or video.get('height')!=model['height']:raise ValueError('FFmpeg: tệp xuất không đúng khung/codec, chưa công bố kết quả.')
    output.replace(j['dir']/'output.mp4');output_bytes=(j['dir']/'output.mp4').stat().st_size
    if hasattr(jobs,'storage')and j.get('room_id'):j['result']=jobs.storage.capture_export(j['id'],j['room_id'],j['dir']/'output.mp4')
    j.update(state='done',progress=100,bytes=output_bytes)
  except asyncio.CancelledError:j['state']='cancelled';raise
  except Exception as e:
   if j['state']!='cancelled':j.update(state='error',error=str(e)if isinstance(e,ValueError)else 'FFmpeg: xuất thất bại; kiểm tra dung lượng ổ đĩa và động cơ.')
  finally:
   p=j.pop('process',None)
   if p and p.returncode is None:p.kill();await p.wait()
   for f in j['dir'].iterdir():
    if f.name!='output.mp4':f.unlink(missing_ok=True)
 @app.post('/local-api/export/timeline')
 async def create(request:Request):
  if not shutil.which('ffmpeg')or not shutil.which('ffprobe'):raise HTTPException(409,'FFmpeg: chưa cài FFmpeg/ffprobe.')
  if sum(j['state']in ('uploading','queued','running')for j in jobs.values())>=2:raise HTTPException(409,'FFmpeg: đang có hai lượt xuất.')
  for old_id,old in list(jobs.items()):
   if old['state']not in ('queued','running')and time.time()-old['created']>86400:
    shutil.rmtree(old['dir'],ignore_errors=True);jobs.pop(old_id,None)
  raw=bytearray()
  async for chunk in request.stream():
   raw.extend(chunk)
   if len(raw)>512*1024:raise HTTPException(413,'Timeline quá lớn.')
  try:
   body=json.loads(raw);model=validate(body);room_id=job_room(body.get('room_id'))
  except (ValueError,TypeError,OverflowError)as e:raise HTTPException(400,'FFmpeg: '+str(e))
  if sum(j['state']in ('uploading','queued','running')for j in jobs.values())>=2:raise HTTPException(409,'FFmpeg: đang có hai lượt xuất.')
  if shutil.disk_usage(folder).free<sum(model['expected'].values())*2+256*1024*1024:raise HTTPException(507,'FFmpeg: ổ đĩa không đủ chỗ.')
  id=uuid.uuid4().hex;directory=folder/id;directory.mkdir();j={'id':id,'dir':directory,'model':model,'received':set(),'inflight':set(),'state':'uploading','progress':0,'duration':model['duration'],'created':time.time(),'room_id':room_id};j=jobs.create(j);return public(j)
 @app.put('/local-api/export/timeline/{id}/assets/{key}')
 async def upload(id:str,key:str,request:Request):
  j=get(id)
  if j['state']!='uploading' or key not in j['model']['expected'] or key in j['received']or key in j['inflight']:raise HTTPException(409,'FFmpeg: tư liệu không nằm trong lượt nhận này.')
  j['inflight'].add(key)
  expected=j['model']['expected'][key];temp=j['dir']/(key+'.part');size=0
  try:
   with temp.open('xb')as f:
    async for chunk in request.stream():
     if j['state']!='uploading':raise HTTPException(409,'FFmpeg: đã hủy nhận tư liệu.')
     size+=len(chunk)
     if size>expected:raise HTTPException(413,'FFmpeg: tư liệu vượt kích thước khai báo.')
     f.write(chunk)
   if size!=expected:raise HTTPException(400,'FFmpeg: tư liệu truyền chưa đủ.')
   with temp.open('rb') as f:magic=f.read(12)
   if not (magic.startswith(b'\x89PNG\r\n\x1a\n')or magic[:3]==b'\xff\xd8\xff'or magic[:4]==b'RIFF'and magic[8:12]in (b'WAVE',b'WEBP')or magic[:4]==b'\x1aE\xdf\xa3'or magic[4:8]==b'ftyp'or magic[:3]==b'ID3'or len(magic)>1 and magic[0]==255 and magic[1]&224==224):
    raise HTTPException(400,'FFmpeg: chỉ nhận video MP4/WebM, ảnh PNG/JPEG/WebP hoặc âm thanh WAV/MP3/M4A. Không nhận playlist, URL hay đường dẫn.')
   temp.replace(j['dir']/(key+'.media'));j['received'].add(key);return public(j)
  except BaseException:temp.unlink(missing_ok=True);raise
  finally:
   j['inflight'].discard(key)
   if j['state']=='cancelled':temp.unlink(missing_ok=True)
 @app.post('/local-api/export/timeline/{id}/start')
 async def start(id:str):
  j=get(id)
  if j['state']!='uploading' or set(j['model']['expected'])!=j['received']:raise HTTPException(409,'FFmpeg: chưa nhận đủ tư liệu hoặc đã bắt đầu.')
  j['state']='queued';j['task']=asyncio.create_task(render(j));return public(j)
 @app.get('/local-api/export/timeline/{id}')
 async def status(id:str):return public(get(id))
 @app.post('/local-api/export/timeline/{id}/cancel')
 async def cancel(id:str):
  j=get(id)
  if j['state']not in ('done','error','cancelled'):
   j['state']='cancelled'
   if j.get('task'):
    j['task'].cancel()
    try:await j['task']
    except asyncio.CancelledError:pass
   for f in j['dir'].iterdir():
    try:f.unlink(missing_ok=True)
    except PermissionError:pass # The active upload closes/removes its own .part on Windows.
  return public(j)
 def resolve_export_file(id):
  j=get(id)
  if j['state']!='done':raise HTTPException(409,'FFmpeg: MP4 chưa xong.')
  if hasattr(jobs,'storage')and j.get('room_id'):
   stored=jobs.storage.file('export-'+id)
   if stored is None and (j['dir']/'output.mp4').is_file():j['result']=jobs.storage.capture_export(id,j['room_id'],j['dir']/'output.mp4');stored=jobs.storage.file('export-'+id)
   if stored:return stored
  if not(j['dir']/'output.mp4').is_file():
   j.update(state='error',error='MP4 tạm đã hết hạn hoặc bị chuyển khỏi máy.')
   raise HTTPException(410,j['error'])
  return j['dir']/'output.mp4'
 @app.get('/local-api/export/timeline/{id}/file')
 async def download(id:str):return FileResponse(resolve_export_file(id),media_type='video/mp4',filename='sceneforge.mp4')
 from .export_save_as import install_export_save_as
 install_export_save_as(app,resolve_export_file)
 return jobs
