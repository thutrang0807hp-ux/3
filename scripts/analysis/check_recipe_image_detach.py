"""Real SQLite/assets: detach only a recipe thumbnail, preserve text/other users."""
import importlib,sys,tempfile,zipfile,json,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
 with tempfile.TemporaryDirectory()as td:
  root=Path(td);pkg=root/'recipe_detach';pkg.mkdir();(pkg/'__init__.py').write_text('')
  with zipfile.ZipFile(ROOT/'downloads/v46-flow-cli-direct/SceneForge-v46.50-Full-Source.zip')as z:
   for name in ('library.py','library_lock.py','schema.py','storage_jobs.py','instance.py'):(pkg/name).write_bytes(z.read('SceneForge-v46.50/local_engine/'+name))
  (pkg/'storage_lifecycle.py').write_bytes((ROOT/'veo-node-v46/local_engine/storage_lifecycle.py').read_bytes());sys.path.insert(0,td)
  mod=importlib.import_module('recipe_detach.library');lib=mod.Library(root/'data')
  def add(content):
   p=root/'image.jpg';p.write_bytes(content);return lib.add_file(p,'image/jpeg')['hash']
  def marker(h):return {'$sf':'dataurl','hash':h,'type':'image/jpeg'}
  def room(id):return {'db':'sceneforge-app-shell','store':'rooms','key':id,'value':{'id':id,'name':id,'archivePolicy':{}}}
  def source(id,h):return {'db':'sceneforge-app-shell','store':'files','key':id+':source','value':marker(h)}
  def pref(value):return {'db':'sceneforge-app-shell','store':'prefs','key':'recipe-library','value':value}
  image,other=add(b'RECIPE POSTER'),add(b'OTHER IMAGE')
  recipe={'version':2,'items':[{'id':'r1','name':'Kịch bản bán hàng','sourcePoster':marker(image),'tips':'Giữ nguyên nội dung','beats':[{'name':'Cảnh 1','text':'Lời đọc giữ nguyên','image':marker(image)}]},{'id':'r2','name':'Khác','sourcePoster':marker(other)}],'trash':[{'id':'old','name':'Bản trong Thùng rác','poster':marker(image),'body':'Nội dung lưu trữ'}],'sources':{'source':{'signature':'KEEP'}}}
  snap=lib.commit([room('removed'),source('removed',image),pref(recipe)],0);backup=lib.backup()
  plan=lib.lifecycle.plan('removed','delete',snap['revision'],0);op=lib.lifecycle.execute({**plan,'confirm':True})['op_id']
  detail=lib.lifecycle.operation_detail(op);file=detail['files'][0];assert file['can_detach_recipe'] and not file['can_release_backup'],file
  reason=next(r for r in file['reasons']if r['type']=='recipe_library')
  assert {r['name']for r in reason['references']}=={'Kịch bản bán hàng','Bản trong Thùng rác'},reason
  try:lib.lifecycle.detach_recipe_image(op,image,detail['token'],str(uuid.uuid4()),False)
  except ValueError:pass
  else:raise AssertionError('Unconfirmed detach accepted')
  # Canonical revision/token changes if any script changes before confirmation.
  rows=lib.snapshot()['records'];rows[0]['value']['lastEdit']='new';lib.commit(rows,lib.snapshot()['revision'])
  try:lib.lifecycle.detach_recipe_image(op,image,detail['token'],str(uuid.uuid4()),True)
  except mod.Conflict:pass
  else:raise AssertionError('Stale detach consent accepted')
  detail=lib.lifecycle.operation_detail(op);result=lib.lifecycle.detach_recipe_image(op,image,detail['token'],str(uuid.uuid4()),True)
  assert result['state']=='done'and not lib.asset_path(image).exists(),result
  saved=next(r['value']for r in result['snapshot']['records']if r['key']=='recipe-library')
  assert saved['items'][0]['sourcePoster'] is None and saved['items'][0]['beats'][0]['image'] is None
  assert saved['items'][0]['tips']=='Giữ nguyên nội dung' and saved['items'][0]['beats'][0]['text']=='Lời đọc giữ nguyên'
  assert saved['trash'][0]['body']=='Nội dung lưu trữ'and saved['trash'][0]['poster'] is None
  assert saved['items'][1]==recipe['items'][1]and lib.asset_path(other).exists()
  restored=lib.restore(backup,lib.snapshot()['revision']);assert lib.status()['missingAssets']==0
  stored=next(r['value']for r in restored['records']if r['key']=='recipe-library')
  assert stored['items'][0]['sourcePoster']['$sf']=='released'and stored['items'][1]==recipe['items'][1]
  print('PASS exact recipe names, consent/stale-token guard, only target image removed, script text/other images preserved, file deletion and safe backup restore')
  # Removing a thumbnail must never remove another project's actual source image.
  shared=add(b'SHARED POSTER');rows=lib.snapshot()['records']
  rows=[r for r in rows if r['key']!='recipe-library']+[pref({'items':[{'id':'shared-recipe','name':'Shared script','sourcePoster':marker(shared),'body':'KEEP'}]}),room('remove2'),source('remove2',shared),room('active'),source('active',shared)]
  snap=lib.commit(rows,lib.snapshot()['revision']);plan=lib.lifecycle.plan('remove2','delete',snap['revision'],0);op=lib.lifecycle.execute({**plan,'confirm':True})['op_id']
  detail=lib.lifecycle.operation_detail(op);result=lib.lifecycle.detach_recipe_image(op,shared,detail['token'],str(uuid.uuid4()),True)
  assert result['protected_files']and lib.asset_path(shared).exists()
  assert any(r['key']=='active:source'and r['value']['hash']==shared for r in result['snapshot']['records'])
  assert next(r['value']for r in result['snapshot']['records']if r['key']=='recipe-library')['items'][0]['body']=='KEEP'
  assert lib.status()['missingAssets']==0
  print('PASS shared project source remains intact after recipe-only detach')
if __name__=='__main__':main()
