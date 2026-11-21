"""Actual shell storage: lost replies/new edits, disjoint projects, genuine conflicts."""
import asyncio,copy,json
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
s=(ROOT/'index.html').read_text();module=s[s.index('window.SceneForgeStorage=(()=>{'):s.index('let appBootReady=')]
fixture='<meta charset="utf-8"><script>window.SceneForgeCloseTrace={step:(name,fn)=>fn()};</script><script>'+module+'''</script><script>
window.putRow=async(key,value)=>{const db=await new Promise((ok,no)=>{const r=indexedDB.open('sceneforge-app-shell',1);r.onsuccess=()=>ok(r.result);r.onerror=()=>no(r.error)});try{await new Promise((ok,no)=>{const tx=db.transaction('rooms','readwrite');tx.objectStore('rooms').put(value,key);tx.oncomplete=ok;tx.onerror=()=>no(tx.error)})}finally{db.close()}};
window.storageReady=SceneForgeStorage.ready().then(()=>({ok:true}),e=>({ok:false,message:e.message}));
</script>'''
def row(key,name):return {'db':'sceneforge-app-shell','store':'rooms','key':key,'value':{'id':key,'name':name}}
async def main():
 remote={'library_id':'library-A','revision':1,'records':[row('original','base')],'mutations':[],'pins':[]};posts=[];archives=[];backups=[];lost=False;dropMerge=False;failBackup=False
 async with async_playwright()as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=await browser.new_context();page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  async def route(r):
   nonlocal lost,remote,dropMerge
   path=r.request.url.split('/local-api/library/')[-1]
   if '/local-api/library/'not in r.request.url:
    await r.fulfill(status=200,body=fixture,content_type='text/html');return
   if path=='status':data={'revision':remote['revision'],'root':'/test/library','backups':[]}
   elif path=='snapshot'and r.request.method=='POST':
    body=r.request.post_data_json;posts.append(copy.deepcopy(body));assert body['revision']==remote['revision'],'unsafe revision write'
    remote={**remote,'revision':remote['revision']+1,'records':body['records'],'mutations':[{'id':body['mutation_id'],'kind':'checkpoint','result_revision':remote['revision']+1}]}
    if lost:
     lost=False;await page.evaluate("putRow('original',{id:'original',name:'newer edit during save'})");await r.abort();return
    if dropMerge:dropMerge=False;await r.abort();return
    data=remote
   elif path.startswith('snapshot'):data=remote
   elif path=='backup':
    if failBackup:await r.fulfill(status=500,body=json.dumps({'detail':'backup failed'}),content_type='application/json');return
    backups.append(copy.deepcopy(remote));data={'name':'protected-backup.sqlite'}
   elif path=='browser-bundle':archives.append(r.request.post_data_json);data={'ok':True}
   else:raise AssertionError(path)
   await r.fulfill(status=200,body=json.dumps(data),content_type='application/json')
  await page.route('**/*',route);await page.goto('http://127.0.0.1/storage-test');assert (await page.evaluate('storageReady'))['ok']
  other=await page.context.new_page();await other.route('**/*',route);await other.goto('http://127.0.0.1/storage-test');assert not(await other.evaluate('storageReady'))['ok']
  refused=await other.evaluate('SceneForgeStorage.recoverWorkingCopy().then(()=>null,e=>e.message)');assert 'cửa sổ khác'in refused and not posts;await other.close()
  await page.evaluate("putRow('original',{id:'original',name:'first edit'})");lost=True
  await page.evaluate('SceneForgeStorage.checkpoint()');state=await page.evaluate('SceneForgeStorage.state');assert state['active']and state['dirty']>0,state
  local=await page.evaluate('SceneForgeStorage.rawRecords()');assert next(x for x in local if x['key']=='original')['value']['name']=='newer edit during save'
  await page.evaluate('SceneForgeStorage.checkpoint()');assert remote['records'][0]['value']['name']=='newer edit during save'
  # A committed checkpoint receipt with edits made afterwards must preserve those edits.
  await page.evaluate("putRow('original',{id:'original',name:'saved without reply'})")
  await page.evaluate("SceneForgeStorage.markMutation('own-checkpoint','checkpoint')")
  remote['revision']+=1;remote['records']=[row('original','saved without reply')];remote['mutations']=[{'id':'own-checkpoint','kind':'checkpoint','result_revision':remote['revision']}]
  await page.evaluate("putRow('original',{id:'original',name:'edit after committed checkpoint'})")
  await page.reload();ready=await page.evaluate('storageReady');assert ready['ok'],ready
  assert remote['records'][0]['value']['name']=='edit after committed checkpoint'
  # New local project + independent remote project merge automatically against durable base.
  await page.evaluate("putRow('local-new',{id:'local-new',name:'Local new project'})")
  remote['revision']+=1;remote['records'].append(row('disk-new','Disk new project'));remote['mutations']=[];dropMerge=True
  await page.reload();ready=await page.evaluate('storageReady');assert not ready['ok'],ready
  await page.reload();ready=await page.evaluate('storageReady');assert ready['ok'],ready
  assert {x['key']for x in remote['records']}=={'original','local-new','disk-new'};assert archives,'working copy not protected before merge'
  # Real simultaneous edit of the same field stays protected, no overwrite.
  await page.evaluate("putRow('original',{id:'original',name:'LOCAL CONFLICT'})")
  remote['revision']+=1;next(x for x in remote['records']if x['key']=='original')['value']['name']='DISK CONFLICT';before=len(posts)
  await page.reload();ready=await page.evaluate('storageReady');assert not ready['ok']and 'cả hai bản'in ready['message'],ready
  assert len(posts)==before and not(await page.evaluate('SceneForgeStorage.state.active'))
  assert next(x for x in remote['records']if x['key']=='original')['value']['name']=='DISK CONFLICT'
  local=await page.evaluate('SceneForgeStorage.rawRecords()');assert next(x for x in local if x['key']=='original')['value']['name']=='LOCAL CONFLICT'
  # Explicit legacy recovery protects both sides and refuses to overwrite without backup.
  failBackup=True
  failure=await page.evaluate('SceneForgeStorage.recoverWorkingCopy().then(()=>null,e=>e.message)');assert 'backup failed'in failure
  assert len(posts)==before and not(await page.evaluate('SceneForgeStorage.state.active'))
  failBackup=False
  result=await page.evaluate('SceneForgeStorage.recoverWorkingCopy()');assert result['ready']and result['backup']
  assert backups[-1]['records'][0]['value']['name']=='DISK CONFLICT'
  assert next(x for x in remote['records']if x['key']=='original')['value']['name']=='LOCAL CONFLICT'
  assert (await page.evaluate('SceneForgeStorage.state'))['active']
  assert not errors,errors;await browser.close()
 print('PASS lost commit response recovers without losing newer edits; own receipt restart; disjoint projects auto-merge; real same-field conflict preserves both')
asyncio.run(main())
