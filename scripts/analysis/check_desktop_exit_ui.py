"""Run the actual native-host save handshake against real IndexedDB and SQLite.

No Windows host is executed: its existing JavaScript handshake is reproduced in
Chromium. Genuine save failures must still return ok:false to the host.
"""
import asyncio,importlib,json,sys,tempfile,zipfile,hashlib
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from fastapi import FastAPI
from playwright.async_api import async_playwright
ROOT=Path('/workspace/3')
HOST="""async()=>{try{await window.SceneForgeApp?.flush?.();await window.SceneForgeStorage?.flush?.();return {type:'sf-desktop-flush',ok:true};}catch(e){return {type:'sf-desktop-flush',ok:false,error:e.message};}}"""
async def main():
 paths=['index.html','workflow.html','photos.html','native/index.html'];html={p:(Path(p)if Path(p).exists()else ROOT/p).read_text()for p in paths}
 html['index.html']=html['index.html'].replace('return {ready,edit,','return {testHasLocalRecords:hasLocalRecords,testContentHash:contentHash,testEqualBlob:equalBlob,ready,edit,')
 with tempfile.TemporaryDirectory(prefix='sf-exit96-')as td:
  root=Path(td);pkg=root/'exit_runtime';pkg.mkdir();(pkg/'__init__.py').write_text('')
  with zipfile.ZipFile(ROOT/'downloads/v46/SceneForge-Veo-v46-Source.zip')as z:
   for n in ['library.py','library_api.py','library_lock.py','storage_lifecycle.py','schema.py','instance.py','storage_jobs.py']:(pkg/n).write_bytes(z.read('local_engine/'+n))
  sys.path.insert(0,td);api=importlib.import_module('exit_runtime.library_api');app=FastAPI();data=root/'data';data.mkdir();lib=api.install_library(app,data);client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local');requests=[];reject=False
  async with async_playwright()as p:
   browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   async def route(r):
    path=urlsplit(r.request.url).path
    if path.startswith('/local-api/library/'):
     requests.append((r.request.method,path))
     if reject and r.request.method=='POST'and path.endswith('/snapshot'):await r.fulfill(status=409,json={'detail':'Fixture save conflict'});return
     res=await client.request(r.request.method,path+('?' +urlsplit(r.request.url).query if urlsplit(r.request.url).query else''),content=r.request.post_data_buffer,headers={'Content-Type':r.request.headers.get('content-type','application/json')});await r.fulfill(status=res.status_code,body=res.content,content_type=res.headers.get('content-type','application/json'));return
    if path.startswith('/local-api/'):
     await r.fulfill(json=[]if path in ['/local-api/logs','/local-api/accounts']else{'engines':[],'accounts':[]});return
    target='index.html'if path=='/'else path.lstrip('/')
    if target in html:await r.fulfill(body=html[target],content_type='text/html');return
    await r.fulfill(status=404,body='')
   await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/');await page.wait_for_function('appBootReady&&SceneForgeStorage.state.active');await page.evaluate('''async()=>{prefs.package5WelcomeDone=true;await savePrefs();document.querySelector('#shellDialog').close();const r={id:'exit-room',name:'Exit fixture',mode:'reference',productId:products[0].id,stage:'draft'};rooms.push(r);await io('rooms','readwrite',r.id,r);document.querySelector('#roomFrames').replaceChildren();const f=document.createElement('iframe');f.id='workflowFrame';f.src='workflow.html?room=exit-room&host=1&mode=reference';document.querySelector('#roomFrames').append(f);}''');frame=page.frame_locator('#workflowFrame');await page.wait_for_function('!!document.querySelector("#workflowFrame").contentWindow.SceneForgeWorkflow?.flushForClose');wf=page.frames[-1]
   binary=await page.evaluate("""async()=>{const a=new Blob(['x'.repeat(16*1024*1024)]),b=new Blob(['x'.repeat(16*1024*1024)]),c=new Blob(['x'.repeat(16*1024*1024-1)+'y']);const at=performance.now();const nativeHash=await SceneForgeStorage.testContentHash(a);const nativeMs=performance.now()-at;const before=performance.now();const oldHash=(await SceneForgePortable.fingerprintWorker(a)).hash;return {nativeHash,oldHash,nativeMs,workerMs:performance.now()-before,equal:await SceneForgeStorage.testEqualBlob(a,b),different:await SceneForgeStorage.testEqualBlob(a,c)}}""")
   assert binary['nativeHash']==binary['oldHash']==hashlib.sha256(b'x'*(16*1024*1024)).hexdigest(),binary
   assert binary['equal']and not binary['different'],binary
   print('16MiB hash native_ms='+str(round(binary['nativeMs'],1))+' previous_worker_ms='+str(round(binary['workerMs'],1)))
   await page.evaluate('SceneForgeStorage.observeWindow(document.querySelector("#workflowFrame").contentWindow)');await wf.evaluate("assets.set('fixture-media',new Blob(['x'.repeat(2*1024*1024)],{type:'video/mp4'}));project.name='Initial saved';save()")
   warm=await page.evaluate(HOST);assert warm['ok'],warm;assert not await page.evaluate('SceneForgeStorage.state.dirty')
   # Metadata-only saves must never open unchanged project/media cursors.
   await page.evaluate("""async()=>{window.exitCursorReads=[];const old=IDBObjectStore.prototype.openCursor;IDBObjectStore.prototype.openCursor=function(...args){exitCursorReads.push([this.transaction.db.name,this.name,args.length]);return old.apply(this,args)};await io('prefs','readwrite','incremental-fixture',{value:1});await SceneForgeStorage.flush();}""")
   assert await page.evaluate('SceneForgeStorage.testHasLocalRecords()')is True
   reads=await page.evaluate('exitCursorReads');assert reads and all(r[1]=='prefs'and r[2]==1 for r in reads),reads
   assert any(r['key']=='incremental-fixture'for r in lib.snapshot()['records'])
   await page.evaluate("""async()=>{await new Promise((ok,no)=>{const tx=db.transaction('prefs','readwrite');tx.objectStore('prefs').delete('incremental-fixture');tx.oncomplete=ok;tx.onerror=()=>no(tx.error)});await SceneForgeStorage.flush()}""")
   assert not any(r['key']=='incremental-fixture'for r in lib.snapshot()['records'])
   await wf.evaluate("(()=>{window.exitWrites=0;const old=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(...args){if(this.name==='projects')exitWrites++;return old.apply(this,args)};})()")
   before=len(requests);idle=await page.evaluate('''async fn=>{const at=performance.now();const result=await eval('('+fn+')')();return {result,ms:performance.now()-at}}''',HOST);assert idle['result']['ok']and idle['ms']<500,idle;assert await wf.evaluate('exitWrites')==0;assert not any(method=='POST'and path.endswith('/snapshot')for method,path in requests[before:]),requests[before:];assert not await page.evaluate("(()=>{const e=new Event('beforeunload',{cancelable:true});dispatchEvent(e);return e.defaultPrevented})()")
   # One new workflow edit: the host's two flush calls must write it only once.
   await wf.evaluate("project.name='Last edit before close';save()");before=len(requests);saved=await page.evaluate(HOST);assert saved['ok'],saved;assert await wf.evaluate('exitWrites')==1;assert sum(method=='POST'and path.endswith('/snapshot')for method,path in requests[before:])==1
   record=next(r for r in lib.snapshot()['records']if r['db']=='sceneforge-workflows'and r['key']=='exit-room');assert record['value']['name']=='Last edit before close';marker=record['value']['assetEntries'][0][1];assert lib.read_asset_path(marker['hash']).stat().st_size==2*1024*1024
   # Scan/room-switch guard remains intact, but saving the current draft can close.
   await wf.evaluate("project.analysis.status='scanning';save()")
   blocked=await page.evaluate("async()=>{try{await flushFrames();return false}catch{return true}}")
   assert blocked;result=await page.evaluate(HOST);assert result['ok'],result;assert await wf.evaluate("project.analysis.status")=='scanning'
   # Photo director also has a save-only path, separate from production guards.
   await page.evaluate("(()=>{const old=document.querySelector('#workflowFrame');old.id='exitWorkflowHidden';old.hidden=true;const f=document.createElement('iframe');f.id='workflowFrame';f.src='photos.html?room=exit-room&host=1';document.querySelector('#roomFrames').append(f)})()")
   await page.wait_for_function('!!document.querySelector("#workflowFrame").contentWindow.SceneForgeWorkflow?.flushForClose');photo=next(f for f in page.frames if '/photos.html'in f.url)
   await photo.evaluate("async()=>{const s=parent.SceneForgeApp.getState(),r=s.rooms.find(r=>r.id==='exit-room');await SceneForgeWorkflow.openRoom({...r,product:s.products.find(p=>p.id===r.productId)});}")
   result=await page.evaluate(HOST);assert result['ok'],result
   await page.evaluate("(()=>{window.photoExitWrites=0;const old=SceneForgeApp.photoBridge.saveDraft;SceneForgeApp.photoBridge.saveDraft=async(...args)=>{photoExitWrites++;return old(...args)}})()")
   await photo.evaluate("draft.exitNote='Photo last edit';scheduleSave();pendingActions.add('fixture-pending')")
   assert await page.evaluate("async()=>{try{await flushFrames();return false}catch{return true}}")
   result=await page.evaluate(HOST);assert result['ok'],result;assert await page.evaluate('photoExitWrites')==1;assert next(r for r in lib.snapshot()['records']if r['db']=='sceneforge-app-shell'and r['store']=='rooms'and r['key']=='exit-room')['value']['photoDraft']['exitNote']=='Photo last edit';await photo.evaluate('pendingActions.clear()')
   # Native timeline: save the draft even when an export is active, without
   # weakening the room-switch/export guard or claiming an MP4 was completed.
   await page.evaluate("(()=>{const old=document.querySelector('#workflowFrame');old.id='exitPhotoHidden';old.hidden=true;const f=document.createElement('iframe');f.id='standaloneEditorDemo';f.src='native/index.html?room=exit-room&host=1';document.querySelector('#roomFrames').append(f)})()")
   await page.wait_for_function('!!document.querySelector("#standaloneEditorDemo").contentWindow.SceneForgeEditor?.flushForClose');ed=next(f for f in page.frames if '/native/index.html'in f.url);await ed.evaluate('SceneForgeEditor.roomReady')
   await page.evaluate('SceneForgeStorage.observeWindow(document.querySelector("#standaloneEditorDemo").contentWindow)');await ed.evaluate("(()=>{window.exitIsExporting=SceneForgeEditor.isExporting;SceneForgeEditor.isExporting=()=>true;document.querySelector('#addMarker').click();document.querySelector('#markerLabel').value='Last editor edit';document.querySelector('#markerAt').value='0.1';document.querySelector('#saveMarker').click()})()")
   assert await page.evaluate("async()=>{try{await flushFrames();return false}catch{return true}}")
   result=await page.evaluate(HOST);assert result['ok'],result;draft=next(r for r in lib.snapshot()['records']if r['db']=='sceneforge-editor-local'and r['key']=='exit-room');assert any(m.get('label')=='Last editor edit'for m in draft['value']['payload']['markers']);assert await ed.evaluate('SceneForgeEditor.isExporting()')is True
   await ed.evaluate('(()=>{SceneForgeEditor.isExporting=window.exitIsExporting})()');await page.evaluate("document.querySelector('#standaloneEditorDemo').remove();document.querySelector('#exitWorkflowHidden').id='workflowFrame'")
   # Failed canonical save still warns, retaining the newer browser draft.
   reject=True;await wf.evaluate("project.name='Unsynced edit retained';save()");failed=await page.evaluate(HOST);assert not failed['ok'];assert await wf.evaluate("(async()=>{const p=await readProject(project.id);return p.name})()")=='Unsynced edit retained';assert not await page.evaluate('SceneForgeStorage.state.active');assert await page.evaluate("(()=>{const e=new Event('beforeunload',{cancelable:true});dispatchEvent(e);return e.defaultPrevented})()")
   report=await page.evaluate("JSON.parse(localStorage.getItem('sceneforge-close-error'))");assert report['stage']in ['Ghi kho dữ liệu trên máy','Kiểm tra kho dữ liệu']and 'Fixture save conflict'in report['error'],report
   assert 'Fixture save conflict'in await page.locator('#sfCloseDiagnostic').inner_text()
   assert not errors,errors;await browser.close()
  await client.aclose()
 print('idle_flush_ms='+str(round(idle['ms'],2)))
 print('PASS actual host handshake: clean exit <500ms with zero workflow writes/checkpoints; edit saved once to IndexedDB+SQLite with media; active scan draft saves without weakening room-switch guard; failed canonical save returns false and retains local edit. Chromium fixture only, not Windows UI.')
if __name__=='__main__':asyncio.run(main())
