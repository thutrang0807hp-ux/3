"""Real library/SQLite files: diagnose protection and release backup-only assets."""
import importlib,json,sys,tempfile,time,zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
def main():
 with tempfile.TemporaryDirectory()as td:
  root=Path(td);pkg=root/'holders_runtime';pkg.mkdir();(pkg/'__init__.py').write_text('')
  with zipfile.ZipFile(ROOT/'downloads/v46-flow-cli-direct/SceneForge-v46.50-Full-Source.zip')as z:
   for name in ('library.py','library_lock.py','schema.py','storage_jobs.py','instance.py'):(pkg/name).write_bytes(z.read('SceneForge-v46.50/local_engine/'+name))
  (pkg/'storage_lifecycle.py').write_bytes((ROOT/'veo-node-v46/local_engine/storage_lifecycle.py').read_bytes())
  sys.path.insert(0,td);mod=importlib.import_module('holders_runtime.library');lib=mod.Library(root/'data')
  def room(name):return {'db':'sceneforge-app-shell','store':'rooms','key':name,'value':{'id':name,'name':'Project '+name,'archivePolicy':{}}}
  def source(name,h):return {'db':'sceneforge-app-shell','store':'files','key':name+':source','value':{'$sf':'blob','hash':h,'type':'video/mp4'}}
  p=root/'video.bin';p.write_bytes(b'CONTENT'*400);h=lib.add_file(p,'video/mp4')['hash']
  snap=lib.commit([room('old'),source('old',h)],0);backup=lib.backup()
  snap=lib.commit([room('removed'),source('removed',h)],snap['revision'])
  plan=lib.lifecycle.plan('removed','delete',snap['revision'],0);result=lib.lifecycle.execute({**plan,'confirm':True})
  assert result['protected_files'] and lib.asset_path(h).exists()
  detail=lib.lifecycle.operation_detail(result['op_id']);file=next(f for f in detail['files']if f['hash']==h)
  assert file['path']==str(lib.asset_path(h)) and file['can_release_backup'],file
  assert all(r['type']=='backup'for r in file['reasons']) and any(r['name']==backup for r in file['reasons'])
  try:lib.lifecycle.release_backup_file(result['op_id'],h,detail['token'],False)
  except ValueError:pass
  else:raise AssertionError('Unconfirmed deletion accepted')
  # A new live owner invalidates the previous token and cannot be forcibly deleted.
  snap=lib.commit([room('live'),source('live',h)],lib.snapshot()['revision'])
  try:lib.lifecycle.release_backup_file(result['op_id'],h,detail['token'],True)
  except mod.Conflict:pass
  else:raise AssertionError('Stale consent accepted')
  held=lib.lifecycle.operation_detail(result['op_id']);assert any(r.get('name')=='Project live'for r in held['files'][0]['reasons'])
  assert not held['files'][0]['can_release_backup']
  try:lib.lifecycle.release_backup_file(result['op_id'],h,held['token'],True)
  except ValueError:pass
  else:raise AssertionError('Live file released')
  assert lib.asset_path(h).exists()
  # Once no current owner exists, explicit retirement covers the listed old backups.
  lib.commit([],lib.snapshot()['revision']);detail=lib.lifecycle.operation_detail(result['op_id'])
  released=lib.lifecycle.release_backup_file(result['op_id'],h,detail['token'],True)
  assert released['state']=='done' and not lib.asset_path(h).exists(),released
  repeated=lib.lifecycle.process(result['op_id']);assert repeated['freed_this_attempt']==0 and repeated['freed_bytes']==released['freed_bytes']
  restored=lib.restore(backup,lib.snapshot()['revision']);assert any(r['value'].get('restoredReleased')for r in restored['records']if r['store']=='rooms')
  assert lib.status()['missingAssets']==0
  print('PASS named backup holders, exact paths, consent, stale-token rejection, live-owner protection, actual delete and safe old-backup restore')
  # Fresh upload and pinned media remain protected; no generic force endpoint.
  p.write_bytes(b'PINNED');h2=lib.add_file(p)['hash'];snap=lib.commit([room('pin'),source('pin',h2)],lib.snapshot()['revision']);lib.set_pin(h2,True,'keep me');lib.add_file(p)
  plan=lib.lifecycle.plan('pin','delete',snap['revision'],0);result=lib.lifecycle.execute({**plan,'confirm':True})
  detail=lib.lifecycle.operation_detail(result['op_id']);file=detail['files'][0]
  assert {'pin','upload_lease'}<={r['type']for r in file['reasons']} and not file['can_release_backup']
  assert any(r.get('note')=='keep me'for r in file['reasons']) and lib.asset_path(h2).exists()
  with lib.db()as db:db.execute("INSERT INTO generation_job(id,provider,room_id,state,result_hash,inputs,created) VALUES(?,?,?,?,?,?,?)",('pending-job','flow','pin','running',h2,json.dumps([h2]),time.time()))
  detail=lib.lifecycle.operation_detail(result['op_id']);assert any(r.get('request_id')=='pending-job'and r.get('state')=='running'for r in detail['files'][0]['reasons'])
  assert not detail['files'][0]['can_release_backup']
  print('PASS pin note, exact upload expiry and unresolved job identity; protected file retained')
  # A future-retention operation is never shortened by the per-file backup action.
  lib.set_pin(h2,False,'')
  with lib.db()as db:db.execute('DELETE FROM upload_lease WHERE hash=?',(h2,))
  with lib.db()as db:db.execute('UPDATE purge_op SET due=? WHERE id=?',(time.time()+86400,result['op_id']))
  assert not lib.lifecycle.operation_detail(result['op_id'])['files'][0]['can_release_backup']
  print('PASS per-file action cannot shorten another retention plan')
if __name__=='__main__':main()
