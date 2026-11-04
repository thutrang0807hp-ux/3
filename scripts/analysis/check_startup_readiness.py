"""Full cold startup with delayed local-library status and early navigation.
No preloaded app globals; existing IndexedDB fixture data must survive startup/reload.
"""
import asyncio,sys
from pathlib import Path
from playwright.async_api import async_playwright

async def startup(browser,source,existing=False,fail_db=False,managed=False):
 context=await browser.new_context();page=await context.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 release=asyncio.Event();requested=asyncio.Event()
 async def route(r):
  url=r.request.url
  if url.endswith('/seed.html'):await r.fulfill(body='<html></html>',content_type='text/html')
  elif r.request.resource_type=='document':await r.fulfill(body=Path(source).read_text(),content_type='text/html')
  elif '/local-api/library/status' in url:
   requested.set();await release.wait()
   if managed:await r.fulfill(json={'root':'fixture-managed-library','revision':0,'backups':[]})
   else:await r.fulfill(status=404,json={'detail':'fixture library API unavailable; use existing local cache'})
  elif '/local-api/library/snapshot' in url:
   body=r.request.post_data_json if r.request.method=='POST' else {}
   await r.fulfill(json={'revision':body.get('revision',0)+(1 if body else 0),'library_id':'fixture-library','records':body.get('records',[]),'warnings':[],'mutations':[]})
  else:await r.fulfill(status=404,json={})
 await page.route('**/*',route)
 if existing:
  await page.goto('http://127.0.0.1:43891/seed.html')
  await page.evaluate('''async()=>{
const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('sceneforge-app-shell',1);r.onupgradeneeded=()=>{for(const s of ['products','rooms','jobs','files','prefs','notifications'])r.result.createObjectStore(s)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});
const refs=Object.fromEntries(['person','outfit','product','background'].map(k=>[k,{images:[],description:''}]));
await new Promise((resolve,reject)=>{const tx=db.transaction(['products','rooms','files','prefs'],'readwrite');tx.objectStore('products').put({id:'preserved-product',name:'PRESERVED PRODUCT',refs},'preserved-product');tx.objectStore('rooms').put({id:'preserved-room',name:'PRESERVED ROOM',productId:'preserved-product',mode:'photos',stage:'review',refs,createdAt:Date.now(),updatedAt:Date.now(),sceneStates:[]},'preserved-room');tx.objectStore('files').put(new Blob(['preserved media fixture'],{type:'video/mp4'}),'preserved-room:source');tx.objectStore('prefs').put({product:'all',lastRoom:null,migrated:true},'main');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)});db.close();}''')
 if fail_db:
  await page.add_init_script('''const original=indexedDB.open.bind(indexedDB);indexedDB.open=(name,...args)=>{if(name==='sceneforge-app-shell')throw Error('fixture database unavailable');return original(name,...args)};''')
 await page.goto('http://127.0.0.1:43891/index.html')
 await asyncio.wait_for(requested.wait(),5)
 await page.wait_for_function('!!window.SceneForgeApp')
 # Direct readers must wait; user clicks must not invoke pre-boot model operations.
 await page.evaluate('''window.earlyReadState='pending';window.earlyRead=io('rooms','readonly').then(rows=>{earlyReadState='resolved';return rows},error=>{earlyReadState=error.message;return null});void 0;''')
 await page.locator('#g6OpenRecipes').click();await page.locator('.rail [data-view=overview]').click()
 await page.wait_for_timeout(100)
 before=await page.evaluate('({read:earlyReadState,error:document.querySelector("#homeError").textContent,ready:SceneForgeApp.getReadiness().rooms})')
 assert before['read']=='pending' and not before['error'] and not before['ready'],before
 release.set()
 if fail_db:
  await page.wait_for_function("document.querySelector('#homeError').textContent.includes('fixture database unavailable')")
  assert await page.evaluate('earlyReadState')=='fixture database unavailable'
  assert not await page.evaluate('SceneForgeApp.getReadiness().rooms')
 else:
  await page.wait_for_function('SceneForgeApp.getReadiness().rooms')
  await page.evaluate('window.earlyRead')
  await page.wait_for_timeout(100)
  result=await page.evaluate('''async()=>({ready:SceneForgeApp.getReadiness(),error:document.querySelector('#homeError').textContent,products:products.map(p=>({id:p.id,name:p.name})),rooms:rooms.map(r=>({id:r.id,name:r.name})),file:await (await io('files','readonly','preserved-room:source'))?.text(),home:currentView==='overview'&&!g6RecipeOpen,bootStatus:!!document.querySelector('#appBootStatus')})''')
  assert not result['error'] and result['ready']['localPersistence'] and result['home'] and not result['bootStatus'],result
  if existing:
   assert result['products']==[{'id':'preserved-product','name':'PRESERVED PRODUCT'}],result
   assert result['rooms']==[{'id':'preserved-room','name':'PRESERVED ROOM'}] and result['file']=='preserved media fixture',result
   await page.reload();await page.wait_for_function('SceneForgeApp.getReadiness().rooms')
   assert await page.evaluate("(async()=>({rooms:(await io('rooms','readonly')).length,file:await(await io('files','readonly','preserved-room:source')).text()}))()") == {'rooms':1,'file':'preserved media fixture'}
  else:assert len(result['products'])==1 and not result['rooms'],result
  assert await page.evaluate("(async()=>{const original=io;recipeCache=null;recipeLoading=null;io=(...args)=>args[0]==='prefs'&&args[2]==='recipe-library'?Promise.reject(Error('fixture transient read failure')):original(...args);let failed=false;try{await recipeLibrary()}catch{failed=true}finally{io=original}const lib=await recipeLibrary();return failed&&Array.isArray(lib.items)})()")
 assert not errors,errors
 print('PASS full startup',{'existingData':existing,'databaseFailure':fail_db,'managedLibrary':managed,'earlyReadWaits':True,'noTransactionUndefined':True})
 await context.close()

async def main():
 source=sys.argv[1] if len(sys.argv)>1 else 'index.html'
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   await startup(browser,source)
   await startup(browser,source,existing=True)
   await startup(browser,source,fail_db=True)
   await startup(browser,source,managed=True)
  finally:await browser.close()
if __name__=='__main__':asyncio.run(main())
