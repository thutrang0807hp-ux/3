"""Bridge durable submission ledger to library ownership, leases and result imports."""
import base64,hashlib,json,os,shutil,tempfile,time
from pathlib import Path
from .storage_lifecycle import owner,SAFE_JOBS

def acknowledge_imports(lib,records=None,records_revision=None):
 from .library import hashes
 with lib.lock,lib.db()as db:
  if not db.execute("SELECT 1 FROM generation_job WHERE state='done' LIMIT 1").fetchone():return
  revision=db.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0]
  cached=getattr(lib,'_import_index',None)
  if cached and cached[0]==revision:by_room,ids,exports=cached[1:]
  else:
   rows=records if records is not None and str(records_revision)==str(revision) else[dict(db=d,store=s,key=json.loads(k),value=json.loads(v))for d,s,k,v in db.execute('SELECT db,store,key,data FROM record')]
   by_room={};ids={};exports={}
   for row in rows:
    room=owner(row)
    if not room:continue
    by_room.setdefault(room,set()).update(hashes(row['value']))
    value=row['value']
    if row['db']=='sceneforge-workflows' or row['db']=='sceneforge-app-shell' and row['store']=='rooms':
     if row['db']=='sceneforge-app-shell':value=value.get('photoDraft')or{}
     for key in ('cloudJobs','referencePromptJobs','flowJobs','museJobs','geminiJobs'):
      for j in value.get(key,[])or[]:
       if j.get('state')in {'imported','applied'}:ids[j.get('id')]=(room,j.get('state'))
     photo_voice=value.get('voice')or{}
     if photo_voice.get('requestId'):ids[photo_voice['requestId']]=(room,'imported')
     voice=value.get('voiceOver')or{}
     for version in voice.get('versions',[]):
      if version.get('requestId'):ids[version['requestId']]=(room,'imported')
     request=(value.get('analysis')or{}).get('aiRequest')or{}
     for j in request.get('batches',[request]if request else[]):
      if j.get('state')in {'received','applied'}:
       raw=j.get('id')or j.get('request_id','');ids[raw if raw.startswith('gchat-')else'gchat-'+raw]=(room,'received')
   for row in rows:
    if row['db']=='sceneforge-app-shell'and row['store']=='files'and str(row['key']).endswith(':export'):exports[str(row['key'])[:-7]]=set(hashes(row['value']))
   lib._import_index=(revision,by_room,ids,exports)
  for rid,room,kind,h in db.execute("SELECT id,room_id,kind,result_hash FROM generation_job WHERE state='done'").fetchall():
   export_saved=kind=='export'and h in exports.get(room,set())
   if export_saved or ids.get(rid,(None,))[0]==room and (kind=='text'or h and h in by_room.get(room,set())):
    db.execute("UPDATE generation_job SET state='imported',imported_at=? WHERE id=?",(time.time(),rid))

class StorageJobs:
 def __init__(self,lib,ledger,data):
  self.lib,self.ledger,self.data=lib,ledger,Path(data);self.minimum_free=256*1024**2
  with lib.db()as db:db.execute("UPDATE generation_job SET state='unknown' WHERE provider='vieneu' AND state='submitted'")
 def limits(self):
  with self.lib.db()as db:row=db.execute("SELECT value FROM meta WHERE key='storage_limits'").fetchone()
  return json.loads(row[0])if row else {'minimum_free_mb':256,'temporary_budget_mb':0}
 def temporary_bytes(self):
  from .library import hashes
  with self.lib.lock,self.lib.db()as db:
   revision=db.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0];pins=tuple(db.execute('SELECT hash FROM pin ORDER BY hash'))
   key=(revision,pins);cached=getattr(self,'_permanent_cache',None)
   if cached and cached[0]==key:permanent=cached[1]
   else:
    permanent={h for h, in pins}
    for d,s,k,v in db.execute('SELECT db,store,key,data FROM record'):
     row={'db':d,'store':s,'key':json.loads(k),'value':json.loads(v)}
     if owner(row)is None or s=='files'and str(row['key']).endswith((':export',':export:srt')):permanent.update(hashes(row['value']))
    self._permanent_cache=(key,permanent)
   return sum(size for h,size in db.execute('SELECT hash,size FROM asset')if h not in permanent)
 def reserve_download(self,rid,size=8*1024**2):
  with self.lib.db()as db:pending=db.execute("SELECT kind FROM generation_job WHERE state='submitted' AND id!=?",(rid,)).fetchall()
  self.check_budget(max(0,int(size)),sum((500 if k=='video'else 32)*1024**2 for(k,)in pending))
 def check_budget(self,required,reserved):
  reserved+=max(0,int(getattr(self,'external_reserved',lambda:0)()))
  from fastapi import HTTPException
  limits=self.limits();floor=limits['minimum_free_mb']*1024**2
  free=min(shutil.disk_usage(self.lib.root).free,shutil.disk_usage(self.data).free)
  if free<required+reserved+floor:
   with self.lib.db()as db:ids=[r[0]for r in db.execute("SELECT id FROM generation_job WHERE state='submitted' LIMIT 8")]
   raise HTTPException(507,'Chưa đủ dung lượng: trống '+str(round(free/1024**2))+' MB; cần thêm '+str(round(required/1024**2))+' MB; đang dự phòng '+str(round(reserved/1024**2))+' MB cho việc đang gửi/chạy; giữ trống '+str(round(floor/1024**2))+' MB. '+('Job: '+', '.join(ids)if ids else'')+' Chưa gửi việc mới.')
  cap=limits['temporary_budget_mb']*1024**2
  if cap and self.temporary_bytes()+required+reserved>cap:raise HTTPException(507,'Kho media trung gian đã gần giới hạn bạn đặt. Dọn bản thừa hoặc tăng giới hạn trước; chưa gửi việc mới.')
 def reserve(self,payload):
  from fastapi import HTTPException
  with self.lib.db()as db:
   if db.execute('SELECT 1 FROM deleted_room WHERE room_id=?',(payload.get('room_id')or'',)).fetchone():raise HTTPException(409,'Dự án đã xóa; không nhận việc mới cho mã cũ.')
   pending=db.execute("SELECT kind FROM generation_job WHERE state='submitted'").fetchall()
  required=(500 if payload.get('kind')=='video'else 32)*1024**2
  committed=sum((500 if k=='video'else 32)*1024**2 for(k,)in pending)
  self.check_budget(required,committed)
 def reserve_local(self,required=32*1024**2):
  from fastapi import HTTPException
  with self.lib.db()as db:pending=db.execute("SELECT kind FROM generation_job WHERE state='submitted'").fetchall()
  reserved=sum((500 if kind=='video'else 32)*1024**2 for(kind,)in pending)
  self.check_budget(required,reserved)
 def register(self,rid,payload):
  from fastapi import HTTPException
  if payload.get('room_id')in (None,'None','null'):payload={**payload,'room_id':''}
  provider='flow'if rid.startswith('flow-')else'muse'if rid.startswith('muse-')else'gemini-chat'if rid.startswith('gchat-')else'vieneu'if rid.startswith('tts-')else'web-images'if rid.startswith('webimage-')else'other'
  inputs=[]
  for ref in payload.get('references',[])or[]:
   if not isinstance(ref,dict)or not isinstance(ref.get('data'),str):continue
   raw=base64.b64decode(ref['data'],validate=True)
   with tempfile.NamedTemporaryFile(dir=self.lib.data,delete=False)as f:f.write(raw);tmp=Path(f.name)
   try:inputs.append(self.lib.add_file(tmp,ref.get('mime_type','image/png'))['hash'])
   finally:tmp.unlink(missing_ok=True)
  with self.lib.lock,self.lib.db()as db:
   if db.execute('SELECT 1 FROM deleted_room WHERE room_id=?',(payload.get('room_id')or'',)).fetchone():raise HTTPException(409,'Dự án đã xóa; không gửi tạo mới.')
   db.execute('INSERT OR IGNORE INTO generation_job(id,provider,room_id,scene_id,kind,state,inputs,created) VALUES(?,?,?,?,?,?,?,?)',(rid,provider,payload.get('room_id')or'',payload.get('scene_id')or'',payload.get('kind')or('video'if provider in ('flow','muse')else'image'if provider=='other'else'text'),'submitted',json.dumps(inputs),time.time()))
 def capture(self,rid,result):
  if not result or not result.get('file'):return None
  if Path(result['file']).name!=result['file']:raise ValueError('Invalid result filename')
  folder='flow-results'if rid.startswith('flow-')else'muse-results'if rid.startswith('muse-')else'gemini-chat-results'if rid.startswith('gchat-')else'media'if rid.startswith('tts-')else'web-image-results'if rid.startswith('webimage-')else'batch-images'if result.get('origin')=='gemini'else None
  if not folder:return None
  path=self.data/folder/result['file']
  if not path.is_file():return None
  self.reserve_download(rid,path.stat().st_size)
  marker=self.lib.add_file(path,result.get('mime_type','application/octet-stream'))
  variants=[]
  if rid.startswith('webimage-'):
   for index,image in enumerate(result.get('images',[])):
    name=image.get('file','');expected={rid+(''if index==0 else'.'+str(index))+ext for ext in ('.png','.jpg','.webp')}
    if name not in expected:raise ValueError('Invalid image filename')
    source=self.data/folder/name
    if not source.is_file():raise ValueError('Missing generated image')
    extra=marker if index==0 else self.lib.add_file(source,image['mime_type'])
    variants.append((source,extra['hash']))
  with self.lib.db()as db:
   db.execute('UPDATE generation_job SET result_hash=? WHERE id=?',(marker['hash'],rid))
   db.execute('INSERT OR REPLACE INTO backend_alias VALUES(?,?,?)',(str(path.relative_to(self.data)),rid,marker['hash']))
   if variants:
    row=db.execute('SELECT inputs FROM generation_job WHERE id=?',(rid,)).fetchone();inputs=json.loads(row[0])if row else[]
    # Retain all results until their batch records have been imported or explicitly released.
    db.execute('UPDATE generation_job SET inputs=? WHERE id=?',(json.dumps(list(dict.fromkeys(inputs+[h for _,h in variants]))),rid))
    for source,h in variants:db.execute('INSERT OR REPLACE INTO backend_alias VALUES(?,?,?)',(str(source.relative_to(self.data)),rid,h))
  for image,(_,h)in zip(result.get('images',[]),variants):image['result_hash']=h
  result['result_hash']=marker['hash'];return path
 def capture_export(self,job_id,room,path):
  rid='export-'+job_id
  marker=self.lib.add_file(path,'video/mp4')
  with self.lib.db()as db:
   db.execute("INSERT OR IGNORE INTO generation_job(id,provider,room_id,kind,state,inputs,created) VALUES(?, 'ffmpeg',?, 'export','done','[]',?)",(rid,room,time.time()))
   db.execute('UPDATE generation_job SET result_hash=? WHERE id=?',(marker['hash'],rid))
   db.execute('INSERT OR REPLACE INTO backend_alias VALUES(?,?,?)',(str(Path(path).relative_to(self.data)),rid,marker['hash']))
  acknowledge_imports(self.lib)
  try:Path(path).unlink(missing_ok=True)
  except OSError:pass
  return {'result_hash':marker['hash'],'request_id':rid}
 def finished(self,rid,state):
  with self.lib.db()as db:db.execute("UPDATE generation_job SET state=? WHERE id=? AND state NOT IN ('imported','discarded')",(state,rid))
  acknowledge_imports(self.lib)
 def file(self,rid):
  with self.lib.db()as db:row=db.execute('SELECT result_hash FROM generation_job WHERE id=?',(rid,)).fetchone()
  if not row or not row[0]:return None
  path=self.lib.read_asset_path(row[0]);return path if path.is_file()else None
 def voice_file(self,filename):
  # Older Windows captures stored Path strings with backslashes. Read both
  # forms so existing generated WAVs remain available after migration.
  with self.lib.db()as db:row=db.execute('SELECT hash FROM backend_alias WHERE path IN (?,?)',('media/'+filename,'media\\'+filename)).fetchone()
  if row:
   path=self.lib.read_asset_path(row[0]);return path if path.is_file()else None
  return None
 def sync(self):
  with self.ledger.connect()as db:
   rows=db.execute('SELECT r.id,r.state,r.result,m.metadata FROM request r LEFT JOIN request_meta m ON m.id=r.id').fetchall()
  for rid,state,result,metadata in rows:
   if state in ('not_submitted','preparing'):
    with self.lib.db()as db:db.execute("UPDATE generation_job SET state='not_submitted' WHERE id=? AND state IN ('submitted','unknown')",(rid,))
    continue
   with self.lib.db()as db:exists=db.execute('SELECT 1 FROM generation_job WHERE id=?',(rid,)).fetchone()
   data=json.loads(metadata)if metadata else{}
   if result:
    completed=json.loads(result)
    for key in ('room_id','scene_id','kind','account_id','model'):
     if not data.get(key)and completed.get(key):data[key]=completed[key]
   if not exists:self.register(rid,data)
   # Adopt legacy result files only after a verified canonical copy and durable catalogue update.
   if result:
    result=json.loads(result)
    with self.lib.db()as check:
     released=check.execute("SELECT 1 FROM generation_job j JOIN room_release r ON r.room_id=j.room_id AND r.hash=j.result_hash WHERE j.id=? AND (r.retain_until<=? OR r.mode LIKE 'now%')",(rid,time.time())).fetchone()
    if self.file(rid)is None and not released:
     try:
      original=self.capture(rid,result)
      if original:
       with self.ledger.connect()as out:out.execute('UPDATE request SET result=? WHERE id=?',(json.dumps(result),rid))
       original.unlink(missing_ok=True)
     except (OSError,ValueError):pass
   self.finished(rid,state)
   if data.get('manual_release')and not self.lib.lifecycle.active_job(rid):self.discard(rid,True)
  self.adopt_receipts()
  self.adopt_legacy_voices()
 def adopt_legacy_voices(self):
  from .library import hashes
  rooms={}
  for row in self.lib.snapshot()['records']:
   for h in hashes(row['value']):rooms.setdefault(h,set()).add(owner(row))
  with self.lib.db()as db:sizes={n for h,n in db.execute('SELECT hash,size FROM asset')if h in rooms}
  for source in (self.data/'media').glob('*.wav'):
   if source.is_symlink()or source.stat().st_size not in sizes:continue
   with source.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
   if h not in rooms:continue
   self.lib.verify({h});rid='legacy-voice-'+source.stem;owned=next(iter(rooms[h]))if len(rooms[h])==1 else''
   with self.lib.lock,self.lib.db()as db:
    db.execute("INSERT OR IGNORE INTO generation_job(id,provider,room_id,kind,state,result_hash,inputs,created) VALUES(?,'legacy-vieneu',?,'audio','imported',?,'[]',?)",(rid,owned or'',h,time.time()))
    db.execute('INSERT OR REPLACE INTO backend_alias VALUES(?,?,?)',(str(source.relative_to(self.data)),rid,h))
   try:source.unlink(missing_ok=True)
   except OSError:pass
 def adopt_receipts(self):
  # Restored projects may contain receipts whose separate request ledger was not moved.
  # Register them for explicit review/discard; never invent a generation or replay one.
  for record in self.lib.snapshot()['records']:
   if record['db']=='sceneforge-workflows':value=record['value']
   elif record['db']=='sceneforge-app-shell'and record['store']=='rooms':value=record['value'].get('photoDraft')or{}
   else:continue
   room=str(record['key']);request=(value.get('analysis')or{}).get('aiRequest')or{}
   candidates=[j for key in ('cloudJobs','referencePromptJobs','flowJobs','museJobs','geminiJobs')for j in value.get(key,[])or[]]+list(request.get('batches',[request]if request else[]))
   for job in candidates:
    rid=job.get('id')or job.get('request_id')
    if not isinstance(rid,str)or not rid:continue
    if job.get('source')=='gemini_chat'and not rid.startswith('gchat-'):rid='gchat-'+rid
    state=job.get('state','unknown');state='imported'if state in ('applied','received','imported')else state if state in SAFE_JOBS else'unknown'
    with self.lib.db()as db:db.execute('INSERT OR IGNORE INTO generation_job(id,provider,room_id,scene_id,kind,state,inputs,created) VALUES(?,?,?,?,?,?,?,?)',(rid,job.get('provider')or job.get('source')or'legacy',room,job.get('sceneId')or'',job.get('kind')or'text',state,'[]',time.time()))
 def discard(self,rid,confirm=False):
  if not isinstance(rid,str)or not 1<=len(rid)<=128:raise ValueError('Mã công việc không hợp lệ.')
  if confirm is not True:raise ValueError('Xác nhận đã đối soát và bỏ kết quả; không hủy tác vụ/hoàn credit.')
  if self.lib.lifecycle.active_job(rid):raise ValueError('Việc vẫn đang chạy trong app; chưa thể bỏ.')
  with self.lib.lock,self.lib.db()as db:
   row=db.execute('SELECT room_id,result_hash FROM generation_job WHERE id=?',(rid,)).fetchone()
   if not row:raise ValueError('Không có công việc.')
   db.execute("UPDATE generation_job SET state='discarded',discarded_at=? WHERE id=?",(time.time(),rid))
   if row[1]:db.execute('DELETE FROM upload_lease WHERE hash=?',(row[1],))
  return {'id':rid,'state':'discarded','generation_requested':False,'cancelled':False}
