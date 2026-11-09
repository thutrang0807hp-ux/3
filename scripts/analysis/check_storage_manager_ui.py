"""Actual SQLite/file measurements and browser-reviewed storage actions; no provider calls."""
import asyncio,importlib,json,os,sys,tempfile,time,types,zipfile
from pathlib import Path
import httpx
from fastapi import FastAPI
from playwright.async_api import async_playwright,expect

async def main():
 root=Path('/workspace/3');html=(Path('index.html')if Path('index.html').exists()else root/'index.html').read_text()
 with tempfile.TemporaryDirectory(prefix='sf-storage89-')as td:
  tmp=Path(td);pkg=tmp/'storage89_runtime';pkg.mkdir();(pkg/'__init__.py').write_text('')
  with zipfile.ZipFile(root/'downloads/v46/SceneForge-Veo-v46-Source.zip')as z:
   for name in ['library.py','library_api.py','library_lock.py','storage_lifecycle.py','schema.py','instance.py','storage_jobs.py']:(pkg/name).write_bytes(z.read('local_engine/'+name))
  source=Path('local_engine/monitoring.py');source=source if source.exists()else root/'veo-node-v46/local_engine/monitoring.py';(pkg/'monitoring.py').write_bytes(source.read_bytes());sys.path.insert(0,td)
  tts=types.ModuleType('storage89_runtime.local_tts');tts.engine_root=lambda data:tmp/'voice';sys.modules[tts.__name__]=tts
  api=importlib.import_module('storage89_runtime.library_api');monitor=importlib.import_module('storage89_runtime.monitoring');app=FastAPI();data=tmp/'data';data.mkdir();lib=api.install_library(app,data);monitor.install_monitoring(app,None,None,lib,data)
  old=lib.root/'cache/thu-vien-old.zip';old.write_bytes(b'CACHE');os.utime(old,(time.time()-7200,)*2);fresh=lib.root/'cache/thu-vien-new.zip';fresh.write_bytes(b'FRESH');model=data/'models';model.mkdir();(model/'weights.bin').write_bytes(b'MODEL')
  working=data/'timeline-exports';working.mkdir();(working/'render.mp4').write_bytes(b'WORKING_VIDEO')
  outside=data/'outside';outside.write_bytes(b'NOT_MANAGED');(lib.root/'cache/link').symlink_to(outside)
  requests=[];client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local')
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1440,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   async def route(r):
    path=r.request.url.split('/local-api/')[-1]
    if '/local-api/library/'in r.request.url:
     requests.append((r.request.method,path));response=await client.request(r.request.method,'/local-api/'+path,content=r.request.post_data_buffer,headers={'content-type':r.request.headers.get('content-type','application/json')});await r.fulfill(status=response.status_code,body=response.content,content_type=response.headers.get('content-type','application/json'));return
    if '/local-api/'in r.request.url:
     await r.fulfill(json={'engines':[],'accounts':[]}if path=='system'else []if path in ['logs','notifications','accounts']else{});return
    if r.request.resource_type=='document':await r.fulfill(body=html,content_type='text/html');return
    await r.fulfill(status=404,body='')
   await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/');await page.wait_for_function('!!db&&SceneForgeStorage.state.active')
   await page.evaluate('''async()=>{prefs.package5WelcomeDone=true;await savePrefs();document.querySelector('#shellDialog').close();const p=products[0]||{id:'P',name:'Sản phẩm'};if(!products.length){products.push(p);await io('products','readwrite',p.id,p);}for(const [id,name,archived]of [['A','Dự án nặng',false],['B','Dự án cũ',true],['C','Dự án rác',false]]){const r={id,name,productId:p.id,archived,createdAt:1700000000000,updatedAt:1700000000000,...(id==='C'?{trashedAt:Date.now()}:{}),mode:'reference',stage:'draft'};rooms.push(r);await io('rooms','readwrite',id,r);}const shared=new Blob(['SHARED'],{type:'image/png'});await io('files','readwrite','A:source',new Blob(['VIDEO_A'.repeat(80)],{type:'video/mp4'}));await io('files','readwrite','A:frame',shared);await io('files','readwrite','B:frame',shared);await io('files','readwrite','C:frame',new Blob(['C'],{type:'image/png'}));await SceneForgeStorage.flush();render();await g5OpenSettings('storage');await settingsMeasure();}''')
   await expect(page.locator('.g5SettingsTitle h2')).to_have_text('Dữ liệu & dung lượng');await expect(page.locator('#smProjectList tbody tr')).to_have_count(3)
   measured=await page.evaluate('settingsStorageData');u={r['id']:r for r in measured['room_usage']};assert u['A']['bytes']==566 and u['B']['bytes']==6 and u['A']['shared_bytes']==6 and u['B']['shared_bytes']==6,u
   assert measured['counts']['projects']['images']==2 and measured['counts']['projects']['videos']==1,measured['counts'];assert measured['categories']['cache']==10 and measured['safe_cache_bytes']==5 and measured['categories']['models']==5
   assert measured['categories']['working']==13 and measured['counts']['working']['videos']==1
   assert measured['total_bytes']==sum(measured['categories'].values());assert measured['complete'];assert all(method=='GET'or not path.endswith(('cleanup','cache','lifecycle/execute'))for method,path in requests)
   assert await page.locator('#smProjectList tbody tr').first.locator('td').nth(1).inner_text()=='Dự án nặng\n'+await page.locator('#smProjectList tbody tr').first.locator('td').nth(1).locator('small').inner_text()
   await page.locator('#smSearch').fill('Dự án cũ');await expect(page.locator('#smProjectList tbody tr')).to_have_count(1);await page.locator('#smSelectAll').check();await expect(page.locator('[data-sm-bulk=compact]')).to_be_enabled();await page.locator('[data-sm-bulk=compact]').click();await expect(page.locator('#storageBulkMode')).to_have_value('compact');assert not any(path.endswith('lifecycle/execute')for _,path in requests)
   await page.evaluate("g5OpenSettings('storage')");await page.locator('#smSearch').fill('');await page.locator('#smFilter').select_option('trash');await expect(page.locator('#smProjectList tbody tr')).to_have_count(1);await expect(page.locator('#smProjectList tbody')).to_contain_text('Dự án rác')
   await page.locator('#smFilter').select_option('all');await page.locator('#smClearSelection').click();await expect(page.locator('[data-sm-bulk=delete]')).to_be_disabled()
   await page.locator('[data-sm-room=A]').click();await expect(page.locator('#storageMode')).to_have_value('unused');await page.locator('#storageMode').select_option('delete');await page.locator('#storagePreview').click();await expect(page.locator('#storageConfirmRead')).to_be_visible();await page.locator('#storageExecute').click();await expect(page.locator('#storageExecuteError')).to_contain_text('Cần xác nhận');assert not any(path.endswith('lifecycle/execute')for _,path in requests)
   # Only cache confirmation mutates; cancelling/backing out does not delete.
   await page.evaluate("g5OpenSettings('storage')");await page.locator('#settingsClearCache').click();assert old.exists();await page.locator('#smCacheBack').click();assert old.exists();await page.locator('#settingsClearCache').click();await page.locator('#smCacheConfirm').click();await page.wait_for_function('document.querySelector("#smSearch")!==null');assert not old.exists()and fresh.exists()and outside.exists()and(model/'weights.bin').exists()
   await page.locator('#settingsMeasureStorage').click();await page.wait_for_function('!settingsStorageLoading');assert await page.evaluate('settingsStorageData.safe_cache_bytes')==0
   await page.locator('#smFilter').select_option('all');await page.screenshot(path='/tmp/sceneforge-storage-manager-v89.png');await page.locator('#smProjectList').scroll_into_view_if_needed();await page.screenshot(path='/tmp/sceneforge-storage-manager-projects-v89.png')
   await page.set_viewport_size({'width':600,'height':900});await page.screenshot(path='/tmp/sceneforge-storage-manager-mobile-v89.png');assert await page.locator('.g5SettingsScroll').evaluate('e=>e.scrollWidth<=e.clientWidth+2')
   # Shared physical file is counted once globally, in each logical project.
   before=lib.status()['revision'];again=monitor.storage_breakdown(lib,data);assert again['counts']['projects']['images']==2 and lib.status()['revision']==before
   assert not errors,errors;await browser.close()
  await client.aclose()
 print('PASS real SQLite/deduplicated media counts; per-project shared bytes; search/filter/sort/selection; guarded single/bulk cleanup; cache cancel/confirm preserves model/project/fresh files; responsive storage overview; no provider requests')
if __name__=='__main__':asyncio.run(main())
