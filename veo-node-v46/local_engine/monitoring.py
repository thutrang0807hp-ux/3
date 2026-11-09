"""Read-only usage projection; never estimate costs, expose secrets or call providers."""
import asyncio,json,math,os,shutil,time
from pathlib import Path

def number(value):return isinstance(value,(int,float))and not isinstance(value,bool)and math.isfinite(value)
def snapshot(vault,ledger,library):
 with library.lock,library.db()as db:
  records=[(store,json.loads(key),json.loads(value))for store,key,value in db.execute("SELECT store,key,data FROM record WHERE db='sceneforge-app-shell' AND store IN ('rooms','products','prefs')")]
 rooms={str(k):v for store,k,v in records if store=='rooms'};products={str(k):v for store,k,v in records if store=='products'}
 batch=next((v for store,k,v in records if store=='prefs'and k=='batch-studio-v1'),{})
 batch_jobs={j.get('requestId'):j for j in batch.get('jobs',[])if isinstance(j,dict)and j.get('requestId')}
 with ledger.connect()as db:metadata={rid:json.loads(m or'{}')for rid,m in db.execute('SELECT id,metadata FROM request_meta')}
 accounts={a['id']:a for a in vault.rows('accounts')};logs=sorted(vault.rows('logs'),key=lambda l:l.get('at',0),reverse=True);truncated=len(logs)>20000;out=[]
 for raw in logs[:20000]:
  rid=str(raw.get('request_id')or raw.get('id')or'');meta=metadata.get(rid,{})
  room_id=str(raw.get('room_id')or meta.get('room_id')or'');room=rooms.get(room_id,{});product_id=str(raw.get('product_id')or room.get('productId')or(room_id if room_id in products else''));product=products.get(product_id,{})
  aid=str(raw.get('account_id')or meta.get('account_id')or'');account=accounts.get(aid,{})
  source=raw.get('service')or meta.get('provider')or account.get('service')or''
  if source=='web-images':source=meta.get('source')or account.get('service')or''
  kind=str(raw.get('kind')or'');low=kind.lower()
  if not source:source='gemini_api'if low.startswith('gemini')else'flow'if low.startswith('flow')else'muse'if low.startswith('muse')else'other'
  if source=='gemini-chat':source='gemini_chat'
  if source=='gemini':source='gemini_api'
  at=raw.get('at');at=at/1000 if number(at)and at>1e12 else at
  if not number(at):continue
  cost=raw.get('cost');unit=raw.get('cost_unit');verified=number(cost)and cost>=0 and unit in ('credit','VND','USD')
  batch_job=batch_jobs.get(rid,{})
  regen=raw.get('is_regeneration')is True or bool(raw.get('regenerated_from'))or bool(meta.get('regenerated_from'))or bool(batch_job.get('regeneratedFrom'))
  out.append({'id':str(raw.get('id')or rid)[:160],'request_id':rid[:160],'at':at,'source':str(source)[:40],
   'kind':kind[:150],'media_kind':str(raw.get('media_kind')or meta.get('kind')or('image'if'image'in low or'ảnh'in low else'video'if'video'in low or'clip'in low else'text'))[:20],
   'state':str(raw.get('state')or'unknown')[:40],'code':str(raw.get('code')or'')[:100],'http_status':raw.get('http_status')if isinstance(raw.get('http_status'),int)else None,
   'room_id':room_id[:160],'room_name':str(room.get('name')or raw.get('room_name')or'')[:200],'scene_id':str(raw.get('scene_id')or meta.get('scene_id')or'')[:100],
   'product_id':product_id[:160],'product_name':str(product.get('name')or'')[:100],'account_id':aid[:160],'account_name':str(account.get('name')or'')[:100],
   'model':str(raw.get('model')or meta.get('model')or'')[:150],'cost':cost if verified else None,'cost_unit':unit if verified else None,'is_regeneration':regen,'regeneration_known':regen or raw.get('is_regeneration')is False})
 exports=[{'id':rid,'product_id':str(r.get('productId')or''),'name':str(r.get('name')or'')[:200],'at':r['exportedAt']/1000}for rid,r in rooms.items()if number(r.get('exportedAt'))and r['exportedAt']>0]
 # Return only balance evidence already stored by an account check, never fetch remote balance.
 balances=[{'id':a['id'],'name':str(a.get('name',''))[:100],'source':a.get('service'),'credit':a.get('credit')if number(a.get('credit'))and a['credit']>=0 else None,'active':bool(a.get('active')),'checked_at':a.get('checked_at')if number(a.get('checked_at'))else None}for a in accounts.values()]
 return {'at':time.time(),'rows':out,'products':[{'id':pid,'name':str(p.get('name')or'')[:100]}for pid,p in products.items()],
  'exports':exports,'balances':balances,'truncated':truncated,'limit':20000,'provider_requests':0,'note':'Chỉ số có trong nhật ký. Phí không có đơn vị/số đã ghi nhận để trống; không suy phí hoặc lý do tạo lại từ việc có nhiều lượt trên một cảnh.'}

def project_usage(library,sizes,mimes):
 # Logical project references are deduplicated within each project, not across
 # projects. This is never a prediction of how many bytes deletion will free.
 from .library import hashes
 from .storage_lifecycle import owner
 records=library.snapshot()['records'];owned={};users={};room_ids=set()
 for row in records:
  rid=owner(row)
  if row['db']=='sceneforge-app-shell'and row['store']=='rooms':room_ids.add(str(row['key']))
  found=set(hashes(row['value']))
  if rid:owned.setdefault(str(rid),set()).update(found)
  for h in found:users.setdefault(h,set()).add(str(rid)if rid else '__shared__')
 out=[]
 for rid in sorted(room_ids):
  hs=owned.get(rid,set());present=hs&sizes.keys()
  out.append({'id':rid,'bytes':sum(sizes[h]for h in present),'files':len(present),
   'images':sum(mimes.get(h,'').startswith('image/')for h in present),
   'videos':sum(mimes.get(h,'').startswith('video/')for h in present),
   'audio':sum(mimes.get(h,'').startswith('audio/')for h in present),
   'shared_bytes':sum(sizes[h]for h in present if len(users.get(h,set()))>1),
   'missing_files':len(hs-present)})
 return out

def storage_breakdown(library,data):
 from .local_tts import engine_root
 started=time.monotonic();seen=set();entries=0;complete=True;errors=0;counts={k:dict(files=0,images=0,videos=0,audio=0)for k in ('projects','exports','cache','models','working')};asset_sizes={};mimes={}
 def size(paths,category):
  nonlocal entries,complete,errors
  total=0
  for root in paths:
   root=Path(root)
   if root.is_symlink():continue
   iterator=[root]if root.is_file()else root.rglob('*')if root.is_dir()else[]
   for p in iterator:
    entries+=1
    if entries>50000 or time.monotonic()-started>5:complete=False;return total
    try:
     if p.is_symlink()or not p.is_file():continue
     st=p.stat();
     if p.name in mimes:asset_sizes[p.name]=st.st_size
     key=(st.st_dev,st.st_ino)if st.st_ino else str(p.resolve())
     if key in seen:continue
     seen.add(key);total+=st.st_size;counts[category]['files']+=1
     mime=mimes.get(p.name,'');ext=p.suffix.lower()
     kind='images'if mime.startswith('image/')or ext in ('.jpg','.jpeg','.png','.webp','.gif','.avif')else'videos'if mime.startswith('video/')or ext in ('.mp4','.mov','.mkv','.webm','.avi')else'audio'if mime.startswith('audio/')or ext in ('.wav','.mp3','.m4a','.ogg','.flac')else None
     if kind:counts[category][kind]+=1
    except OSError:errors+=1;complete=False
  return total
 with library.lock,library.db()as db:
  exports={h for key,h in db.execute("SELECT key,hash FROM asset_ref WHERE store='files'")if str(json.loads(key)).endswith((':export',':export:srt'))}
  mimes={h:m or''for h,m in db.execute('SELECT hash,mime FROM asset')}
  assets=[(h,library.read_asset_path(h))for h in mimes]
  output=library.output_root()
  exported=size([p for h,p in assets if h in exports],'exports')+size([output],'exports')
  project=size([p for h,p in assets if h not in exports],'projects')+size([library.path,Path(str(library.path)+'-wal'),Path(str(library.path)+'-shm'),library.root/'sao-luu',library.root/'schema-backups'],'projects')
  cache=size([library.root/'cache'],'cache')
  working=size([Path(data)/name for name in ('media','timeline-exports','exports','cpu-analysis')],'working')
  models=size([Path(data)/'models',engine_root(Path(data))/'runtime/offline'],'models')
  room_usage=project_usage(library,asset_sizes,mimes)
  cache_plan=library.cache_plan();limits=library.jobs_bridge.limits()if getattr(library,'jobs_bridge',None)else{}
 return {'at':time.time(),'root':str(library.root),'output_root':str(output),'models_root':str(Path(data)/'models'),'voice_models_root':str(engine_root(Path(data))/'runtime/offline'),
  'counts':counts,'room_usage':room_usage,'categories':{'projects':project,'exports':exported,'models':models,'cache':cache,'working':working},'total_bytes':project+exported+models+cache+working,'complete':complete,'errors':errors,
  'free_bytes':min(shutil.disk_usage(library.root).free,shutil.disk_usage(data).free),'safe_cache_bytes':cache_plan['bytes'],'limits':limits,
  'note':'Đo các vùng được app quản lý, không phải toàn bộ ổ hay dung lượng gói cài. Gồm kho, sao lưu, bản xuất, model và tệp làm việc media/ghép/phân tích. File đã lưu tùy ý bên ngoài không được quét. Không đi theo symlink; cache chỉ xóa qua kế hoạch đã kiểm tra.'}

def install_monitoring(app,vault,ledger,library,data):
 @app.get('/local-api/monitoring')
 async def usage():return await asyncio.to_thread(snapshot,vault,ledger,library)
 @app.get('/local-api/library/storage-breakdown')
 async def breakdown():return await asyncio.to_thread(storage_breakdown,library,data)
