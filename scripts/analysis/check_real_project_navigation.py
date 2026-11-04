"""Actual saved image-heavy project + actual workflow/editor frames; local API fixtures only. Run from repo root."""
import asyncio,threading,json,time,sys
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.async_api import async_playwright
root=Path.cwd()
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':1450,'height':950});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  async def api(r):
   if '/library/' in r.request.url:await r.fulfill(status=404,json={});return
   await r.fulfill(json={'enabled':True,'native_pipeline':True,'selection':{'available':False},'unresolved':[],'accounts':[],'logs':[],'operations':[],'jobs':[],'providers':{},'connected':False})
  await page.route('**/local-api/**',api)
  if len(sys.argv)>1:
   async def shellroute(r):
    if r.request.url.split('?',1)[0].endswith('/native/index.html'):await r.continue_()
    else:await r.fulfill(body=Path(sys.argv[1]).read_text(),content_type='text/html')
   await page.route('**/index.html',shellroute)
  if len(sys.argv)>2:
   await page.route('**/workflow.html*',lambda r:r.fulfill(body=Path(sys.argv[2]).read_text(),content_type='text/html'))
  origin=f'http://127.0.0.1:{server.server_port}'
  await page.goto(origin+'/workflow.html?room=fixture-room&mode=reference');await page.wait_for_function('!!window.SceneForgeWorkflow&&!!window.SFVeoNode')
  await page.evaluate('''async()=>{
project=blankProject();project.id='fixture-room';project.name='REAL PROJECT FIXTURE';project.roomSeeded=true;project.analysis.frameQualityRequired=false;
const c=document.createElement('canvas');c.width=384;c.height=682;const ctx=c.getContext('2d');ctx.fillStyle='teal';ctx.fillRect(0,0,c.width,c.height);const image=c.toDataURL('image/jpeg',.8);
project.source={name:'fixture.mp4',poster:image,asset:'source',duration:480};project.scenes=Array.from({length:60},(_,i)=>{const pixels=ctx.createImageData(c.width,c.height);let seed=i+1;for(let j=0;j<pixels.data.length;j+=4){seed=(1664525*seed+1013904223)>>>0;pixels.data[j]=seed&255;pixels.data[j+1]=seed>>>8&255;pixels.data[j+2]=seed>>>16&255;pixels.data[j+3]=255;}ctx.putImageData(pixels,0,0);const image=c.toDataURL('image/jpeg',.9);const s=sceneRecord(i*8,(i+1)*8,i,[image]);s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',image};s.approvedFrame='source';s.frameSelectionId='source';s.videoPromptOverrides={a:'A gentle movement.'};return s});await storeProject();
const d=await new Promise((resolve,reject)=>{const r=indexedDB.open('sceneforge-app-shell',1);r.onupgradeneeded=()=>{for(const s of ['products','rooms','jobs','files','prefs','notifications'])r.result.createObjectStore(s)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});
await new Promise((resolve,reject)=>{const tx=d.transaction(['products','rooms','prefs'],'readwrite');tx.objectStore('products').put({id:'p',name:'Fixture product',refs:project.refs},'p');tx.objectStore('rooms').put({id:project.id,name:project.name,productId:'p',mode:'reference',stage:'review',sceneStates:Array(60).fill('generating'),sceneCount:60,refs:project.refs,poster:image,createdAt:Date.now(),updatedAt:Date.now()},project.id);tx.objectStore('prefs').put({product:'all',lastRoom:null,migrated:true},'main');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)});d.close();}''')
  await page.goto(origin+'/index.html');await page.wait_for_function('window.SceneForgeApp?.getReadiness().rooms')
  at=time.monotonic();await page.locator('#board [data-open-room="fixture-room"]').first.click();await page.wait_for_function('currentView==="analysis"&&!document.querySelector("#roomLoading").hidden===false',timeout=20000)
  print('OPEN seconds',time.monotonic()-at,await page.evaluate('({view:currentView,error:document.querySelector("#homeError").textContent,frames:document.querySelectorAll("#roomFrames iframe").length})'))
  wf=page.frame_locator('#workflowFrame')
  assert await wf.locator('#node-frames img').count()>=60
  assert await wf.locator('#node-scenes .ndScene').count()==60
  assert await wf.locator('#node-videos .vnTile').count()==60
  assert await page.evaluate('''async()=>{const original=render;let calls=0;render=(...args)=>{calls++;return original(...args)};try{await persistRoom(currentRoom);return calls===0}finally{render=original}}''')
  await wf.locator('body').evaluate('''()=>{window.strictFlushCalls=0;window.strictFlushOriginal=SceneForgeWorkflow.flushRoom;SceneForgeWorkflow.flushRoom=async()=>{strictFlushCalls++;throw Error('fixture strict flush blocked')};const input=document.querySelector('#projectName');input.value='EDIT RETAINED AFTER NAVIGATION';input.dispatchEvent(new Event('input',{bubbles:true}));}''')
  at=time.monotonic();await page.locator('.rail [data-view=overview]').click();await page.wait_for_function('currentView==="overview"',timeout=15000);print('HOME AFTER OPEN seconds',time.monotonic()-at)
  assert await wf.locator('body').evaluate('()=>strictFlushCalls')==0
  assert await page.evaluate("SceneForgeApp.flush().then(()=>false,e=>e.message==='fixture strict flush blocked')")
  assert await page.evaluate("(async()=>{const frame=document.querySelector('#workflowFrame');rooms.push({...currentRoom,id:'blocked-room',name:'Blocked new room'});try{await SceneForgeApp.openRoom('blocked-room')}catch{}const kept=currentRoom.id==='fixture-room'&&document.querySelector('#workflowFrame')===frame;rooms=rooms.filter(r=>r.id!=='blocked-room');clearHomeError();return kept})()")
  await wf.locator('body').evaluate('()=>{SceneForgeWorkflow.flushRoom=strictFlushOriginal}')
  await page.wait_for_function("(async()=>{const w=await workflowRecord('fixture-room');return w?.name==='EDIT RETAINED AFTER NAVIGATION'})()")
  assert await page.evaluate("!!document.querySelector('#workflowFrame')?.isConnected")
  summary=await wf.locator('body').evaluate('''()=>({scenes:project.scenes.map(({start,end,hasPerson})=>({start,end,hasPerson})),analysis:{status:project.analysis.status,pipeline6:{running:false},semantic:{recipe:project.analysis.semantic?.recipe||null}}})''')
  assert await page.evaluate('''async summary=>{const original=workflowRecord;let reads=0;workflowRecord=()=>{reads++;throw Error('Unexpected full project read')};const refs={person:{images:[{name:'Legacy cached person',image:'data:image/png;base64,AA=='}]}};rooms.push({id:'other-legacy',name:'Other',refs},{id:'other-current',name:'Other current',refs,recentPeopleRefs:[{name:'Latest cached person',image:'data:image/png;base64,AQ=='}]});try{const people=await SceneForgeApp.recentPeople('fixture-room');await extractReferenceRecipe('fixture-room',summary);const lib=await recipeLibrary();return reads===0&&people.some(p=>p.name==='Latest cached person')&&people.some(p=>p.name==='Legacy cached person')&&lib.sources['fixture-room'].state==='done';}finally{workflowRecord=original;rooms=rooms.filter(r=>!r.id.startsWith('other-'));}}''',summary)
  print('PASS retained autosave, strict checkpoint error, and recent-people/recipe metadata with zero full project reads')
  await page.locator('.rail [data-view=editor]').click();await page.wait_for_function('currentView==="editor"&&document.querySelector("#roomLoading").hidden',timeout=20000)
  at=time.monotonic();await page.locator('.rail [data-view=overview]').click();await page.wait_for_function('currentView==="overview"',timeout=15000);print('HOME AFTER EDITOR',time.monotonic()-at)
  assert not errors,errors;print('PASS real workflow/editor project navigation; page errors:',errors);await b.close()
try:asyncio.run(main())
finally:server.shutdown()
