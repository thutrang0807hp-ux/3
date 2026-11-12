"""Transactional deletion intent, quarantine, room-scoped release and safe restore.

All mutations are explicit or resume previously authorized operations. No provider calls.
"""
import hashlib,json,os,sqlite3,time,uuid
from pathlib import Path

SCHEMA='''
CREATE TABLE IF NOT EXISTS asset_lifecycle(hash TEXT PRIMARY KEY,state TEXT NOT NULL,op_id TEXT);
CREATE TABLE IF NOT EXISTS upload_lease(hash TEXT PRIMARY KEY,expires REAL NOT NULL);
CREATE TABLE IF NOT EXISTS generation_job(id TEXT PRIMARY KEY,provider TEXT,room_id TEXT,scene_id TEXT,kind TEXT,state TEXT,result_hash TEXT,inputs TEXT NOT NULL DEFAULT '[]',created REAL,imported_at REAL,discarded_at REAL);
CREATE TABLE IF NOT EXISTS purge_op(id TEXT PRIMARY KEY,room_id TEXT,mode TEXT,state TEXT,created REAL,due REAL,items TEXT,freed_bytes INTEGER NOT NULL DEFAULT 0,errors TEXT NOT NULL DEFAULT '[]',restore_data TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS room_release(room_id TEXT,hash TEXT,retain_until REAL,mode TEXT,PRIMARY KEY(room_id,hash));
CREATE TABLE IF NOT EXISTS purge_item(op_id TEXT,hash TEXT,state TEXT,size INTEGER,PRIMARY KEY(op_id,hash));
CREATE TABLE IF NOT EXISTS backend_alias(path TEXT PRIMARY KEY,job_id TEXT,hash TEXT);
CREATE TABLE IF NOT EXISTS purge_copy(op_id TEXT,room_id TEXT,hash TEXT,path TEXT,size INTEGER,state TEXT,PRIMARY KEY(op_id,path));
CREATE TABLE IF NOT EXISTS deleted_room(room_id TEXT PRIMARY KEY,deleted_at REAL);
'''
SAFE_JOBS={'imported','discarded','failed','not_submitted','abandoned','cancelled','applied'}

def owner(row):
 d,s,k=row['db'],row['store'],str(row['key'])
 if d in ('sceneforge-workflows','sceneforge-editor-local'):return k
 if d=='sceneforge-app-shell':
  if s=='rooms':return k
  if s=='jobs':return (row.get('value')or{}).get('roomId')
  if s=='files'and not k.startswith(('bank:','cache:','batch:','shared:','library:')):
   if k.startswith('voice:'):return k.split(':',2)[1]
   if ':'in k:return k.split(':',1)[0]
 return None

def collect_strings(v,out=None):
 out=set()if out is None else out
 if isinstance(v,str):
  if len(v)<500:out.add(v)
 elif isinstance(v,dict):
  for x in v.values():collect_strings(x,out)
 elif isinstance(v,list):
  for x in v:collect_strings(x,out)
 return out

def shared_file_keys(records):
 references={}
 for row in records:
  room=owner(row)
  for key in collect_strings(row['value']):references.setdefault(key,set()).add(room)
 return {str(row['key'])for row in records if row['store']=='files'and any(room!=owner(row)for room in references.get(str(row['key']),set()))}

def text_only(v):
 if isinstance(v,dict):
  if '$sf'in v:return None
  return {k:text_only(x)for k,x in v.items()if k not in {'asset','assetId','images','assetEntries','media','thumbs','evidence_frames','sourceFrame','frames','clips','localHistory','local','pendingAI','musicLibrary','music','poster','image','tail','wave','chosen','approvedFrame','plan'}}
 if isinstance(v,list):return [text_only(x)for x in v]
 if isinstance(v,str)and v.startswith(('data:image/','data:video/','data:audio/','blob:')):return None
 return v

def workflow_blockers(value):
 out=[]
 for key in ('cloudJobs','referencePromptJobs','flowJobs','museJobs','geminiJobs'):
  for job in value.get(key,[])or[]:
   if job.get('state')not in SAFE_JOBS:out.append(job.get('id')or key)
 analysis=value.get('analysis')or{};request=analysis.get('aiRequest')or{}
 for job in request.get('batches',[request]if request else[]):
  if job.get('state')not in SAFE_JOBS|{'received','planned'}:out.append(job.get('id')or job.get('request_id')or'analysis')
 return out

class Lifecycle:
 def __init__(self,library):self.lib=library;self.active_job=lambda rid:False;self._backup_protection={}
 def policies(self,db=None):
  if db is None:
   with self.lib.db()as conn:return self.policies(conn)
  return ({(r,h):(due,mode)for r,h,due,mode in db.execute('SELECT room_id,hash,retain_until,mode FROM room_release')},{r[0]for r in db.execute('SELECT room_id FROM deleted_room')})
 def restore_records(self,records,db=None):
  from .library import hashes
  release,deleted=self.policies(db);now=time.time();out=[];affected=set();shared=shared_file_keys(records)
  for row in records:
   room=owner(row)
   if row['store']=='files'and str(row['key'])in shared:
    out.append(row);continue
   if room in deleted:continue
   def clean(v):
    if isinstance(v,dict):
     h=v.get('hash')
     if v.get('$sf')in ('blob','file','dataurl')and (room,h)in release:
      due,mode=release[room,h]
      # Present/quarantined retained files remain recoverable until the release deadline.
      if mode.startswith('now')or due<=now:
       affected.add(room);return {'$sf':'released','hash':h,'reason':'User released intermediate media'}
     return {k:clean(x)for k,x in v.items()}
    if isinstance(v,list):return [clean(x)for x in v]
    return v
   out.append({**row,'value':clean(row['value'])})
  for row in out:
   room=owner(row)
   if room not in affected:continue
   if row['db']=='sceneforge-app-shell'and row['store']=='rooms':
    row['value'].update(restoredReleased=True,needsAttention=True,restoreWarning='Một số tư liệu đã được chủ động giải phóng; kiểm tra phần còn lại.')
    if any(r==room and mode.endswith(':compact')for (r,h),(due,mode)in release.items()):row['value'].update(archiveState='final-only',sourceCleaned=True,editorInitialized=False)
  for row in out:
   if owner(row)not in affected:continue
   value=row['value']
   if row['db']=='sceneforge-workflows':
    gone={a for a,b in value.get('assetEntries',[])if isinstance(b,dict)and b.get('$sf')=='released'}
    value['assetEntries']=[[a,b]for a,b in value.get('assetEntries',[])if a not in gone]
    for scene in value.get('scenes',[]):
     scene['clips']=[c for c in scene.get('clips',[])if c.get('asset')not in gone]
     scene['frames']=[f for f in scene.get('frames',[])if not(isinstance(f.get('image'),dict)and f['image'].get('$sf')=='released')]
     clips={c['id']for c in scene['clips']};frames={f['id']for f in scene['frames']}
     scene['chosen']={k:v for k,v in (scene.get('chosen')or{}).items()if v in clips}
     if scene.get('approvedFrame')not in frames|{'source',None}:scene['approvedFrame']=None
    voice=value.get('voiceOver')or{}
    voice['versions']=[v for v in voice.get('versions',[])if v.get('assetId')not in gone]
    if voice.get('assetId')in gone:voice['assetId']=None
   if row['db']=='sceneforge-editor-local':
    gone={m['id']for m in value.get('media',[])if isinstance(m.get('file'),dict)and m['file'].get('$sf')=='released'}
    value['media']=[m for m in value.get('media',[])if m.get('id')not in gone]
    payload=value.get('payload')or{}
    payload['assets']=[a for a in payload.get('assets',[])if a.get('id')not in gone]
    payload['items']=[i for i in payload.get('items',[])if i.get('assetId')not in gone]
  return [row for row in out if not(row['db']=='sceneforge-editor-local'and owner(row)in affected and any(r==owner(row)and mode.endswith(':compact')for (r,h),(due,mode)in release.items()))]
 def protected(self,db=None,backups=True):
  from .library import hashes
  if db is None:
   with self.lib.db()as conn:return self.protected(conn,backups)
  protected={r[0]for r in db.execute('SELECT hash FROM asset_ref UNION SELECT hash FROM pin')}
  protected.update(h for h, in db.execute('SELECT hash FROM upload_lease WHERE expires>?',(time.time(),)))
  for state,result,inputs in db.execute('SELECT state,result_hash,inputs FROM generation_job'):
   if state not in SAFE_JOBS:
    if result:protected.add(result)
    protected.update(json.loads(inputs))
  if backups:
   policy=repr(self.policies(db))
   paths=list((self.lib.root/'sao-luu').glob('*.sqlite'))+list((self.lib.root/'schema-backups').glob('*.sqlite'));active=set()
   for path in paths:
    stat=path.stat();key=(str(path),stat.st_mtime_ns,stat.st_ctime_ns,stat.st_size,policy);active.add(key)
    cached=self._backup_protection.get(key)
    if cached is None:
     b=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
     try:
      rows=[dict(db=d,store=s,key=json.loads(k),value=json.loads(v))for d,s,k,v in b.execute('SELECT db,store,key,data FROM record')]
      cached={h for row in self.restore_records(rows,db)for h in hashes(row['value'])}
      cached.update(r[0]for r in b.execute('SELECT hash FROM pin'))
     finally:b.close()
     if len(cached)*160<=32*1024**2:
      while self._backup_protection and sum(len(v)*160 for v in self._backup_protection.values())+len(cached)*160>32*1024**2:self._backup_protection.pop(next(iter(self._backup_protection)))
      self._backup_protection[key]=cached
    protected.update(cached)
   self._backup_protection={k:v for k,v in self._backup_protection.items()if k in active}
  return protected
 def revive(self,h,db,cancel=True):
  row=db.execute('SELECT state,op_id FROM asset_lifecycle WHERE hash=?',(h,)).fetchone()
  if not row or row[0]=='present'and not row[1]:return
  original=self.lib.asset_path(h);pending=self.lib.root/'kho'/'.cho-xoa'/row[1]/h
  if not original.exists()and pending.is_file():original.parent.mkdir(exist_ok=True);os.replace(pending,original)
  if original.is_file():
   if cancel:db.execute("UPDATE purge_item SET state='revived' WHERE op_id=? AND hash=? AND state!='done'",(row[1],h))
   db.execute("UPDATE asset_lifecycle SET state='present',op_id=? WHERE hash=?",(None if cancel else row[1],h))
   # A new reference overrides the former release for this byte-identical asset.
   # Existing room-scoped release consent remains; a new live reference protects the hash.
 def owned_records(self,room):return [r for r in self.lib.snapshot()['records']if owner(r)==room]
 def guard(self,room,records,db=None):
  with self.lib.db()as check:
   unowned=check.execute("SELECT id FROM generation_job WHERE room_id='' AND provider IN ('flow','muse','gemini-chat') AND state NOT IN ('imported','discarded','failed','not_submitted') LIMIT 1").fetchone()
   if unowned:raise ValueError('Job chưa xác định dự án: '+unowned[0]+'. Mở Kết quả chờ nhận / đối soát để kiểm tra hoặc bỏ trước khi dọn.')
  if any(self.active_job(j[0])for j in self.job_rows(room,db)):raise ValueError('Dự án đang có tác vụ chạy; chưa thể dọn.')
  for row in records:
   if owner(row)!=room:continue
   if row['db']=='sceneforge-workflows' or row['db']=='sceneforge-app-shell' and row['store']=='rooms':
    value=row['value']if row['db']=='sceneforge-workflows'else row['value'].get('photoDraft')or{}
    discarded={j for j,state in self.job_rows(room,db)if state=='discarded'}
    if any(j not in discarded and 'gchat-'+j not in discarded for j in workflow_blockers(value)):raise ValueError('Dự án còn kết quả chờ nhận hoặc tác vụ chưa rõ. Đối soát / bỏ kết quả trước.')
   if row['store']=='jobs'and row['value'].get('status')not in {'done','failed','error','cancelled','abandoned'}:raise ValueError('Hàng chờ dự án chưa kết thúc.')
  if any(j[1]not in SAFE_JOBS for j in self.job_rows(room,db)):raise ValueError('Backend còn job chờ nhận/chưa rõ kết quả; chưa dọn.')
 def job_rows(self,room,db=None):
  if db is None:
   with self.lib.db()as c:return self.job_rows(room,c)
  return db.execute('SELECT id,state FROM generation_job WHERE room_id=?',(room,)).fetchall()
 def plan(self,room,mode,revision,days=7,published=False,targets=None):
  from .library import hashes,Conflict
  if not isinstance(room,str)or not room or ':'in room or room in {'bank','cache','batch','voice','shared','library'}:raise ValueError('Mã dự án không hợp lệ.')
  if mode not in {'unused','compact','delete','approved'}:raise ValueError('Chế độ dọn không hợp lệ.')
  if type(days)is not int or not 0<=days<=3650:raise ValueError('Chọn 0–3650 ngày.')
  with self.lib.lock:
   snap=self.lib.snapshot()
   if snap['revision']!=revision:raise Conflict('Thư viện đã thay đổi; xem lại kế hoạch.')
   records=snap['records'];target=next((r for r in records if r['db']=='sceneforge-app-shell'and r['store']=='rooms'and r['key']==room),None)
   if target is None:raise ValueError('Không tìm thấy dự án.')
   if mode!='approved':self.guard(room,records)
   if target['value'].get('archivePolicy',{}).get('pinned'):raise ValueError('Bỏ ghim dự án trước khi dọn/xóa.')
   changed=json.loads(json.dumps(records));own=[r for r in changed if owner(r)==room];before=set().union(*(set(hashes(r['value']))for r in own))if own else set()
   if mode=='approved':
    if days!=0 or published:raise ValueError('Duyệt chỉ dọn ngay bản cũ trong ô đã chọn.')
    from .version_approval import prune_approved
    prune_approved(changed,room,targets)
   elif mode=='delete':
    shared=shared_file_keys(records)
    changed=[r for r in changed if owner(r)!=room or r['store']=='files'and str(r['key'])in shared]
   elif mode=='compact':
    exported=next((r for r in own if r['store']=='files'and r['key']==room+':export'),None)
    if not exported:raise ValueError('Chưa có video thành phẩm đã lưu vào kho máy.')
    self.lib.verify(set(hashes(exported['value'])))
    if not exported['value'].get('type','').startswith('video/'):raise ValueError('Thành phẩm không phải file video.')
    import subprocess,math
    final_path=self.lib.read_asset_path(exported['value']['hash'])
    try:
     probe=subprocess.run(['ffprobe','-v','error','-protocol_whitelist','file,pipe','-show_streams','-show_format','-of','json',str(final_path)],capture_output=True,timeout=30)
     info=json.loads(probe.stdout)
     if probe.returncode or not any(s.get('codec_type')=='video'and s.get('width',0)>0 for s in info.get('streams',[]))or not math.isfinite(float(info['format']['duration']))or float(info['format']['duration'])<=0:raise ValueError()
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired):raise ValueError('Chưa đọc được video thành phẩm bằng ffprobe; chưa dọn tư liệu.')from None

    workflow=next((r['value']for r in own if r['db']=='sceneforge-workflows'),{})
    editor=next((r['value']for r in own if r['db']=='sceneforge-editor-local'),{})
    shell=target['value'];final={**text_only(shell),'poster':shell.get('poster'),'archiveState':'final-only','archived':True,'compactedAt':shell.get('compactedAt')or shell.get('exportedAt')or 1,'sourceCleaned':True,'editorInitialized':False,'archiveText':{'workflow':text_only(workflow),'photo':text_only(shell.get('photoDraft')),'timelineCaptions':text_only([i for i in editor.get('payload',{}).get('items',[])if i.get('kind')=='text'])},'archivePolicy':{**shell.get('archivePolicy',{}),'paused':True}}
    used=set()
    for other in records:
     if owner(other)!=room:collect_strings(other['value'],used)
    changed=[r for r in changed if owner(r)!=room or r['store']=='files'and(r['key']in (room+':export',room+':export:srt')or str(r['key'])in used)]
    changed.append({**target,'value':final})
    if workflow:changed.append({'db':'sceneforge-workflows','store':'projects','key':room,'value':{**text_only(workflow),'id':room,'compacted':True,'assetEntries':[]}})
   else:
    # Only version rows positively identified as unused are removed. Timelines/history/shared refs remain protective.
    for row in changed:
     if owner(row)!=room or row['db']!='sceneforge-workflows':continue
     value=row['value'];editor=next((r['value']for r in own if r['db']=='sceneforge-editor-local'),{})
     timeline_hashes=set(hashes(editor));kept_assets=set()
     for scene in value.get('scenes',[]):
      chosen=set((scene.get('chosen')or{}).values());clips=[]
      for clip in scene.get('clips',[]):
       marker=next((b for a,b in value.get('assetEntries',[])if a==clip.get('asset')),None)
       if clip.get('id')in chosen or set(hashes(marker))&timeline_hashes:clips.append(clip)
      scene['clips']=clips
      frames=set([scene.get('approvedFrame'),scene.get('frameSelectionId')]+[c.get('frameId')for c in clips])
      if scene.get('frames'):frames.add(scene['frames'][-1].get('id'))
      scene['frames']=[f for f in scene.get('frames',[])if f.get('id')in frames or set(hashes(f))&timeline_hashes]
     entries=value.pop('assetEntries',[]);strings=collect_strings(value)
     value['assetEntries']=[[a,b]for a,b in entries if a in strings or set(hashes(b))&timeline_hashes]
    # Photo Studio keeps version metadata in the room; retire only explicit file keys.
    photo=next((r['value'].get('photoDraft')for r in changed if r['db']=='sceneforge-app-shell'and r['store']=='rooms'and r['key']==room),None)
    if isinstance(photo,dict):
     editor=next((r['value']for r in own if r['db']=='sceneforge-editor-local'),{})
     timeline_hashes=set(hashes(editor));files={str(r['key']):r['value']for r in own if r['store']=='files'};retired=set()
     protected_ids=collect_strings(photo.get('plan',[]))
     def keep_versions(items,selected):
      kept=[]
      for item in items or[]:
       key=item.get('key');ident=item.get('id')
       if item.get('pinned')or ident in selected or ident in protected_ids or key in protected_ids or set(hashes(files.get(key)))&timeline_hashes:kept.append(item)
       elif key:retired.add(key)
       else:kept.append(item) # Unidentified legacy media is retained.
      return kept
     for beat in photo.get('beats',[])or[]:
      latest_by_part={c.get('part','a'):c.get('id')for c in beat.get('clips',[])or[]}
      selected=set((beat.get('chosenParts')or{}).values())|{beat.get('chosenClip')}|set(latest_by_part.values())
      beat['clips']=keep_versions(beat.get('clips'),selected)
      frames=beat.get('frames')or[]
      if frames:beat['frames']=keep_versions(frames,{beat.get('approvedFrame'),beat.get('frameSelectionId'),frames[-1].get('id')})
     images=photo.get('storyboardImages')or[]
     if images:photo['storyboardImages']=keep_versions(images,{photo.get('storyboardImage'),images[-1].get('id')})
     still_used=set()
     for row in changed:
      if row['store']!='files':collect_strings(row['value'],still_used)
     changed=[r for r in changed if not(owner(r)==room and r['store']=='files'and str(r['key'])in retired-still_used)]
   after=set().union(*(set(hashes(r['value']))for r in changed))if changed else set();own_after=set().union(*(set(hashes(r['value']))for r in changed if owner(r)==room))if any(owner(r)==room for r in changed)else set();candidates=before-own_after
   with self.lib.db()as db:
    old=next((r['value'].get('archiveRetiredHashes',[])for r in own if r['store']=='rooms'),[])
    if mode!='approved':candidates.update(h for h in old if h not in after)
    for h, in db.execute('SELECT hash FROM room_release WHERE room_id=?',(room,)):
     if mode!='approved'and h not in after:candidates.add(h)
    job_hashes={h for h, in db.execute('SELECT result_hash FROM generation_job WHERE room_id=? AND state IN (\'imported\',\'discarded\')',(room,))if h}
    if mode!='approved':candidates.update(job_hashes-own_after)
    for inputs, in db.execute("SELECT inputs FROM generation_job WHERE room_id=? AND state IN ('imported','discarded','failed')",(room,)):
     if mode!='approved':candidates.update(set(json.loads(inputs))-own_after)
    sizes={h:n for h,n in db.execute('SELECT hash,size FROM asset')}
   published_files=[]
   if mode=='delete'and published:
    with self.lib.db()as db:
     for h,path in db.execute('SELECT hash,path FROM published WHERE room_id=?',(room,)):
      actual=Path(path)if Path(path).is_absolute()else self.lib.root/path
      if actual.is_file():published_files.append({'hash':h,'path':path,'size':actual.stat().st_size})
   token_data={'published_files':published_files,'revision':revision,'room_id':room,'mode':mode,'days':days,'published':bool(published),'records':changed,'candidates':sorted(candidates),**({'targets':targets}if mode=='approved'else{})}
   token=hashlib.sha256(json.dumps(token_data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
   return {**token_data,'token':token,'candidate_bytes':sum(sizes.get(h,0)for h in candidates),'candidate_files':len(candidates),'warning':'File dùng chung, bản ghim, file vừa tải lên chờ lưu và kết quả chưa nhận vẫn được giữ. Khu chờ xóa chưa giải phóng dung lượng. Bản sao ngoài app không bị xóa.'}
 def execute(self,body):
  from .library import hashes,Conflict
  if body.get('confirm')is not True:raise ValueError('Cần xác nhận phạm vi xóa.')
  with self.lib.lock:
   mutation_id=body.get('mutation_id')or body.get('token')
   if not isinstance(mutation_id,str)or not __import__('re').fullmatch(r'[A-Za-z0-9_-]{8,128}',mutation_id):raise ValueError('Mã thao tác dọn không hợp lệ.')
   with self.lib.db()as check:prior=check.execute("SELECT operation_id FROM mutation_receipt WHERE id=? AND kind='cleanup'",(mutation_id,)).fetchone()
   if prior:return {**self.process(prior[0]),'snapshot':self.lib.snapshot()}
   plan=self.plan(body['room_id'],body['mode'],body['revision'],body.get('days',7),body.get('published',False),body.get('targets'))
   if body.get('token')!=plan['token']:raise Conflict('Kế hoạch đã thay đổi; xem lại trước khi xóa.')
   original_records=self.lib.snapshot()['records']
   with self.lib.db()as before:prior_release=before.execute('SELECT hash,retain_until,mode FROM room_release WHERE room_id=?',(body['room_id'],)).fetchall()
   restore_data=json.dumps({'records':[r for r in original_records if owner(r)==body['room_id']],'release_before':prior_release},ensure_ascii=False)
   op=uuid.uuid4().hex;now=time.time();due=now+plan['days']*86400
   for record in plan['records']:
    if plan['mode']=='compact'and record['store']=='rooms'and record['key']==body['room_id']:record['value']['compactedAt']=now
   rows,refs=self.lib.validate(plan['records']);self.lib.verify(refs)
   with self.lib.db()as db:
    db.execute('BEGIN IMMEDIATE');actual=int(db.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0])
    if actual!=body['revision']:raise Conflict('Thư viện đã thay đổi.')
    if plan['mode']=='delete':db.execute('INSERT OR REPLACE INTO deleted_room VALUES(?,?)',(body['room_id'],now))
    for h in plan['candidates']:db.execute('INSERT OR REPLACE INTO room_release VALUES(?,?,?,?)',(body['room_id'],h,due,('now:'if not plan['days']else'retain:')+plan['mode']))
    db.execute('DELETE FROM asset_ref');db.execute('DELETE FROM record');db.execute('DELETE FROM room_index')
    for d,s,k,v in rows:
     db.execute('INSERT INTO record VALUES(?,?,?,?)',(d,s,k,v))
     data=json.loads(v)
     for h in set(hashes(data)):db.execute('INSERT OR IGNORE INTO asset_ref VALUES(?,?,?,?)',(d,s,k,h))
     if d=='sceneforge-app-shell'and s=='rooms':db.execute('INSERT INTO room_index VALUES(?,?,?,?,?,?)',(str(json.loads(k)),data.get('productId'),data.get('name'),data.get('stage'),bool(data.get('archived')),bool(data.get('trashedAt'))))
    db.execute("UPDATE meta SET value=? WHERE key='revision'",(str(actual+1),))
    for h in plan['candidates']:
     size=db.execute('SELECT size FROM asset WHERE hash=?',(h,)).fetchone()
     db.execute("INSERT INTO purge_item VALUES(?,?,'pending',?)",(op,h,size[0]if size else 0))
    for copy in plan['published_files']:db.execute("INSERT INTO purge_copy VALUES(?,?,?,?,?,'pending')",(op,body['room_id'],copy['hash'],copy['path'],copy['size']))
    db.execute('INSERT INTO purge_op(id,room_id,mode,state,created,due,items,restore_data) VALUES(?,?,?,?,?,?,?,?)',(op,body['room_id'],plan['mode'],'intent',now,due,json.dumps(plan['candidates']),restore_data))
    self.lib.record_mutation(db,mutation_id,'cleanup',actual,actual+1,plan['token'],op)
   result=self.process(op)
   # A storage mutation changes the canonical revision. Browser must hydrate that exact snapshot.
   return {**result,'snapshot':self.lib.snapshot()}
 def process(self,op_id):
  from .library import sync_parent
  with self.lib.lock,self.lib.db()as db:
   row=db.execute('SELECT due,items,freed_bytes,room_id FROM purge_op WHERE id=?',(op_id,)).fetchone()
   if not row:raise ValueError('Không có lượt dọn.')
   due,items,freed,room=row;initial_freed=freed;protected=self.protected(db);current=self.protected(db,backups=False);errors=[];waiting=0;held=0
   for h in json.loads(items):
    item=db.execute('SELECT state FROM purge_item WHERE op_id=? AND hash=?',(op_id,h)).fetchone()
    if item and item[0]=='revived':continue
    canonical_done=bool(item and item[0]=='done')
    state=db.execute('SELECT state,op_id FROM asset_lifecycle WHERE hash=?',(h,)).fetchone()
    if state and state[1]not in (None,op_id):held+=1;continue
    # Leases, live refs, pins and unresolved jobs override an authorized release.
    # Before retention expires, backup protection is expected; use current refs to allow quarantine only.
    if h in current or time.time()>=due and h in protected:
     self.revive(h,db,cancel=False);held+=1;continue
    for alias, in db.execute('SELECT a.path FROM backend_alias a JOIN generation_job j ON j.id=a.job_id WHERE a.hash=? AND j.room_id=?',(h,room)).fetchall():
     original_alias=self.lib.data/alias
     try:
      if self.lib.data.resolve()not in original_alias.resolve().parents:raise OSError('Alias path outside backend')
      if original_alias.is_file():
       with original_alias.open('rb')as f:verified=hashlib.file_digest(f,'sha256').hexdigest()==h
       if not verified:raise OSError('Backend alias changed; retained')
       alias_size=original_alias.stat().st_size;original_alias.unlink();freed+=alias_size
       db.execute('UPDATE purge_op SET freed_bytes=? WHERE id=?',(freed,op_id));db.commit()
     except OSError as error:errors.append({'path':alias,'error':str(error)})
    if canonical_done:continue
    asset=db.execute('SELECT size FROM asset WHERE hash=?',(h,)).fetchone()
    if not asset:
     db.execute("UPDATE purge_item SET state='done' WHERE op_id=? AND hash=?",(op_id,h));continue
    original=self.lib.asset_path(h);folder=self.lib.root/'kho'/'.cho-xoa'/op_id;folder.mkdir(parents=True,exist_ok=True);pending=folder/h
    db.execute("INSERT OR REPLACE INTO asset_lifecycle VALUES(?,'deleting',?)",(h,op_id));db.commit()
    try:
     if original.is_file():os.replace(original,pending);sync_parent(original);sync_parent(pending)
     db.execute("UPDATE asset_lifecycle SET state='quarantined' WHERE hash=?",(h,));db.commit()
     if time.time()<due:waiting+=1;continue
     existed=pending.exists();pending.unlink(missing_ok=True);sync_parent(pending)
     db.execute('DELETE FROM asset WHERE hash=?',(h,));db.execute('DELETE FROM asset_lifecycle WHERE hash=?',(h,));db.execute('DELETE FROM upload_lease WHERE hash=?',(h,))
     # A missing quarantined file after intent is a recoverable interrupted deletion.
     if existed:freed+=asset[0]
     db.execute("UPDATE purge_item SET state='done' WHERE op_id=? AND hash=?",(op_id,h))
     db.execute('UPDATE purge_op SET freed_bytes=? WHERE id=?',(freed,op_id));db.commit()
    except OSError as error:errors.append({'hash':h,'error':str(error)})
   for path,h,size,copy_state in db.execute("SELECT path,hash,size,state FROM purge_copy WHERE op_id=? AND state!='done'",(op_id,)).fetchall():
    if time.time()<due:waiting+=1;continue
    if db.execute('SELECT 1 FROM published WHERE path=? AND room_id!=?',(path,room)).fetchone():held+=1;continue
    actual=Path(path)if Path(path).is_absolute()else self.lib.root/path
    # Only a catalogued output under the configured output root, still byte-identical.
    if self.lib.output_root().resolve()not in actual.resolve().parents:
     errors.append({'path':path,'error':'Output location changed; inspect before deletion'});continue
    try:
     if actual.exists():
      with actual.open('rb')as stream:matches=hashlib.file_digest(stream,'sha256').hexdigest()==h
      if not matches:errors.append({'path':path,'error':'Output modified outside app; kept'});continue
     db.execute("UPDATE purge_copy SET state='deleting' WHERE op_id=? AND path=?",(op_id,path));db.commit()
     actual.unlink(missing_ok=True)
     freed+=size
     db.execute("UPDATE purge_copy SET state='done' WHERE op_id=? AND path=?",(op_id,path));db.execute('DELETE FROM published WHERE room_id=? AND path=?',(room,path));db.execute('UPDATE purge_op SET freed_bytes=? WHERE id=?',(freed,op_id));db.commit()
    except OSError as error:errors.append({'path':path,'error':str(error)})
   state='waiting'if waiting else'blocked'if held else'retry'if errors else'done'
   db.execute('UPDATE purge_op SET state=?,errors=? WHERE id=?',(state,json.dumps(errors),op_id))
   if time.time()>=due:db.execute("UPDATE purge_op SET restore_data='{}' WHERE id=?",(op_id,))
   return {'op_id':op_id,'state':state,'freed_bytes':freed,'freed_this_attempt':freed-initial_freed,'waiting_files':waiting,'protected_files':held,'errors':errors}
 def operation_detail(self,op_id):
  """Explain actual holders, not a generic list of possible protections."""
  from .library import hashes
  with self.lib.lock,self.lib.db()as db:
   op=db.execute('SELECT room_id,mode,state,items,due FROM purge_op WHERE id=?',(op_id,)).fetchone()
   if not op:raise ValueError('Không có lượt dọn.')
   names={r:n for r,n in db.execute('SELECT id,name FROM room_index')}
   wanted=json.loads(op[3]);files=[];backup_reasons={h:[] for h in wanted[:200]}
   # Read each backup once, even when many candidate files are shown.
   for folder in ('sao-luu','schema-backups'):
    for path in (self.lib.root/folder).glob('*.sqlite'):
     backup=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
     try:
      records=[dict(db=d,store=store,key=json.loads(key),value=json.loads(value))for d,store,key,value in backup.execute('SELECT db,store,key,data FROM record')]
      by_hash={};shared=shared_file_keys(records)
      for row in self.restore_records(records,db):
       for digest in set(hashes(row['value']))&backup_reasons.keys():by_hash.setdefault(digest,[]).append(row)
      pinned_hashes={row[0]for row in backup.execute('SELECT hash FROM pin')}
      for digest in (by_hash.keys()|pinned_hashes)&backup_reasons.keys():
       rows=by_hash.get(digest,[]);pinned=digest in pinned_hashes
       owners=sorted({owner(row)for row in rows if owner(row)})
       releasable=bool(rows)and not pinned and all(owner(row) and not(row['store']=='files'and str(row['key'])in shared)for row in rows)
       backup_reasons[digest].append({'type':'backup','name':path.name,'folder':folder,'pinned':pinned,'room_ids':owners,'can_release':releasable})
     finally:backup.close()
   for h in wanted[:200]:
    size=db.execute('SELECT size,mime FROM asset WHERE hash=?',(h,)).fetchone()
    if not size:continue
    reasons=[]
    for d,store,key,value in db.execute('SELECT r.db,r.store,r.key,r.data FROM record r JOIN asset_ref a ON a.db=r.db AND a.store=r.store AND a.key=r.key WHERE a.hash=?',(h,)):
     row={'db':d,'store':store,'key':json.loads(key),'value':json.loads(value)};room=owner(row)
     reasons.append({'type':'project'if room else'library_reference','room_id':room,'name':names.get(room,room or 'Tư liệu dùng chung'),'store':store,'key':row['key']})
    for note, in db.execute('SELECT note FROM pin WHERE hash=?',(h,)):reasons.append({'type':'pin','note':note})
    for expires, in db.execute('SELECT expires FROM upload_lease WHERE hash=? AND expires>?',(h,time.time())):reasons.append({'type':'upload_lease','expires':expires})
    for jid,room,state,result,inputs in db.execute('SELECT id,room_id,state,result_hash,inputs FROM generation_job'):
     if state not in SAFE_JOBS and (result==h or h in json.loads(inputs)):reasons.append({'type':'job','request_id':jid,'room_id':room,'name':names.get(room,room),'state':state})
    state=db.execute('SELECT op_id FROM asset_lifecycle WHERE hash=?',(h,)).fetchone()
    if state and state[0]not in (None,op_id):reasons.append({'type':'other_operation','op_id':state[0]})
    reasons.extend(backup_reasons.get(h,[]))
    actual=self.lib.read_asset_path(h)
    eligible=op[2] not in ('done','cancelled')and op[4]<=time.time()and bool(reasons)and all(r['type']=='backup'and r['can_release']for r in reasons)
    files.append({'hash':h,'path':str(actual),'bytes':size[0],'mime':size[1],'exists':actual.is_file(),'reasons':reasons,'can_release_backup':eligible})
   report={'op_id':op_id,'room_id':op[0],'mode':op[1],'state':op[2],'due':op[4],'files':files,'truncated':len(wanted)>200}
   report['token']=hashlib.sha256(json.dumps(report,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
   return report
 def release_backup_file(self,op_id,h,token,confirm=False):
  """Explicitly retire only backup-only copies; never bypass a live holder."""
  from .library import Conflict
  if confirm is not True:raise ValueError('Cần xác nhận mất khả năng khôi phục tệp này từ sao lưu.')
  with self.lib.lock:
   detail=self.operation_detail(op_id)
   if detail['token']!=token:raise Conflict('Nơi giữ tệp đã thay đổi; xem lại trước khi xóa.')
   item=next((row for row in detail['files']if row['hash']==h),None)
   if not item or not item['can_release_backup']:raise ValueError('Tệp còn nơi giữ đang hoạt động hoặc bản ghim; chưa được xóa.')
   owners={room for reason in item['reasons']for room in reason['room_ids']}
   with self.lib.db()as db:
    for room in owners:db.execute('INSERT OR REPLACE INTO room_release VALUES(?,?,?,?)',(room,h,time.time(),'now:unused'))
    db.execute("UPDATE purge_op SET due=?,restore_data='{}' WHERE id=?",(time.time(),op_id))
   # Existing release policies are persisted and honored when restoring old backups.
   result=self.process(op_id)
   return {**result,'detail':self.operation_detail(op_id)}
 def expedite(self,op_id,confirm=False):
  if confirm is not True:raise ValueError('Xác nhận xóa ngay; không còn lấy lại được file đã xóa.')
  with self.lib.lock,self.lib.db()as db:
   op=db.execute('SELECT room_id,mode,items FROM purge_op WHERE id=?',(op_id,)).fetchone()
   if not op:raise ValueError('Không có lượt dọn.')
   for h in json.loads(op[2]):db.execute("UPDATE room_release SET retain_until=?,mode=? WHERE room_id=? AND hash=?",(time.time(),'now:'+op[1],op[0],h))
   db.execute("UPDATE purge_op SET due=?,restore_data='{}' WHERE id=?",(time.time(),op_id));db.commit()
   return self.process(op_id)
 def cancel_delete(self,op_id,confirm=False):
  from .library import hashes,Conflict
  if confirm is not True:raise ValueError('Xác nhận lấy lại dự án đang chờ xóa.')
  with self.lib.lock,self.lib.db()as db:
   row=db.execute('SELECT room_id,mode,due,restore_data,created,state FROM purge_op WHERE id=?',(op_id,)).fetchone()
   if not row or row[1]!='delete'or row[2]<=time.time()or row[5]=='cancelled':raise ValueError('Chỉ lấy lại dự án còn trong thời hạn chờ xóa.')
   room,_,_,saved,created,_=row
   if db.execute('SELECT 1 FROM purge_op WHERE room_id=? AND created>?',(room,created)).fetchone():raise Conflict('Có thao tác mới hơn; chưa khôi phục đè.')
   data=json.loads(saved);original=data.get('records',[])
   current=self.lib.snapshot();existing={(r['db'],r['store'],str(r['key'])):r for r in current['records']}
   for record in original:
    key=(record['db'],record['store'],str(record['key']))
    if key in existing and existing[key]!=record:raise Conflict('Dữ liệu đã thay đổi; chưa khôi phục đè.')
    existing[key]=record
   rows,refs=self.lib.validate(list(existing.values()))
   for h in refs:self.revive(h,db)
   db.commit();self.lib.verify(refs)
   db.execute('BEGIN IMMEDIATE')
   actual=int(db.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0])
   if actual!=current['revision']:raise Conflict('Thư viện đã thay đổi.')
   db.execute('DELETE FROM deleted_room WHERE room_id=?',(room,));db.execute('DELETE FROM room_release WHERE room_id=?',(room,))
   for h,due,mode in data.get('release_before',[]):db.execute('INSERT INTO room_release VALUES(?,?,?,?)',(room,h,due,mode))
   db.execute('DELETE FROM asset_ref');db.execute('DELETE FROM record');db.execute('DELETE FROM room_index')
   for d,s,k,v in rows:
    db.execute('INSERT INTO record VALUES(?,?,?,?)',(d,s,k,v))
    for h in set(hashes(json.loads(v))):db.execute('INSERT OR IGNORE INTO asset_ref VALUES(?,?,?,?)',(d,s,k,h))
    if d=='sceneforge-app-shell'and s=='rooms':
     v=json.loads(v);db.execute('INSERT INTO room_index VALUES(?,?,?,?,?,?)',(str(json.loads(k)),v.get('productId'),v.get('name'),v.get('stage'),bool(v.get('archived')),bool(v.get('trashedAt'))))
   db.execute("UPDATE meta SET value=? WHERE key='revision'",(str(actual+1),))
   db.execute("UPDATE purge_op SET state='cancelled',items='[]',errors='[]',restore_data='{}' WHERE id=?",(op_id,));db.execute("UPDATE purge_copy SET state='done' WHERE op_id=?",(op_id,));db.commit()
   return {'snapshot':self.lib.snapshot(),'restored_room':room}
 def resume(self):
  with self.lib.lock,self.lib.db()as db:
   db.execute("UPDATE purge_op SET restore_data='{}' WHERE due<=?",(time.time(),))
   ids=[r[0]for r in db.execute("SELECT id FROM purge_op WHERE state NOT IN ('done','cancelled')")]
  return [self.process(i)for i in ids]
