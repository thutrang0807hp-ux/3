"""Real batch queue + SQLite/IndexedDB, intercepted Gemini image provider; no online sends."""
import asyncio,importlib,io,json,sys,tempfile,zipfile
from pathlib import Path
import httpx
from fastapi import FastAPI
from PIL import Image
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
async def main():
 with tempfile.TemporaryDirectory() as td:
  tmp=Path(td);pkg=tmp/'batch_runtime';pkg.mkdir();(pkg/'__init__.py').write_text('')
  with zipfile.ZipFile(ROOT/'downloads/v46/SceneForge-Veo-v46-Source.zip') as z:
   for name in ['library.py','library_api.py','library_lock.py','storage_lifecycle.py','schema.py','instance.py','storage_jobs.py']:(pkg/name).write_bytes(z.read('local_engine/'+name))
  sys.path.insert(0,td);api=importlib.import_module('batch_runtime.library_api');app=FastAPI();data=tmp/'data';data.mkdir();lib=api.install_library(app,data);posts=[]
  buf=io.BytesIO();Image.new('RGB',(90,160),'green').save(buf,'PNG');png=buf.getvalue()
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local') as client:
   async with async_playwright() as pw:
    browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    async def route(r):
     url=r.request.url;path=url.split('/local-api/')[-1]
     if '/local-api/library/' in url:
      res=await client.request(r.request.method,'/local-api/'+path,content=r.request.post_data_buffer,headers={'content-type':'application/json'});await r.fulfill(status=res.status_code,body=res.content,content_type=res.headers.get('content-type','application/json'));return
     if path=='batch/images/models':await r.fulfill(json={'models':['gemini-image-fixture']});return
     if path=='flow/models':await r.fulfill(json={'models':['imagen-fixture','veo-3.1-lite']});return
     if path=='gemini-chat/status':await r.fulfill(json={'installed':True,'configured':True,'image_per_account':1,'image_maximum_setting':4,'selection':{'available':True,'mode':'selected','token':'fixture-token','account_name':'Fixture Gemini','account_id':'a'}});return
     if path=='gemini-chat/jobs' and r.request.method=='POST':
      body=r.request.post_data_json;posts.append(body);assert body['kind']=='image' and body['role']=='image' and body['selection_token']=='fixture-token';await r.fulfill(json={'request_id':body['request_id'],'state':'done','result':{'mime_type':'image/png','model':'fixture-image','account_id':'a'}});return
     if path.startswith('gemini-chat/files/'):
      await r.fulfill(body=png,content_type='image/png');return
     if '/local-api/' in url:await r.fulfill(json=[] if path in ['accounts','logs','notifications'] else {});return
     if r.request.resource_type=='document':await r.fulfill(body=(ROOT/'index.html').read_text(),content_type='text/html');return
     await r.fulfill(status=404,body='')
    await page.route('**/*',route);await page.goto('http://127.0.0.1:43895/');await page.wait_for_function('appBootReady&&SceneForgeStorage.state.active')
    await page.evaluate("async()=>{prefs.package5WelcomeDone=true;await savePrefs();document.querySelector('#shellDialog').close();await openBatchStudio();}")
    assert await page.locator('#batchEngine').input_value()=='gemini_chat'
    assert not posts
    assert await page.locator('#batchImageChoice').is_visible()
    assert not await page.locator('#batchEngine').is_visible()
    assert not await page.locator('#batchImageModel').is_visible()
    await page.locator('#batchImageChoice').select_option('["gemini",""]')
    await page.locator('#batchCheckModels').click()
    await page.wait_for_function('document.querySelector("#batchImageChoice").value===JSON.stringify(["gemini","gemini-image-fixture"])')
    await page.locator('#batchImageChoice').select_option('["flow",""]')
    assert await page.locator('#batchImageModel').input_value()==''
    await page.locator('#batchCheckModels').click()
    await page.wait_for_function('document.querySelector("#batchImageChoice").value===JSON.stringify(["flow","imagen-fixture"])')
    assert not posts
    await page.locator('#batchImageChoice').select_option('["simulation",""]');await page.wait_for_function("batchState.preferredSource==='simulation'")
    await page.evaluate("async()=>{document.querySelector('#batchPrompts').value='Mô phỏng cũ';await batchEnqueue();}")
    old=await page.evaluate('batchState.jobs[0].id')
    await page.locator('#batchImageChoice').select_option('["gemini_chat",""]');await page.wait_for_function("batchState.preferredSource==='gemini_chat'")
    await page.evaluate("async()=>{document.querySelector('#batchPrompts').value='Ảnh sản phẩm trên bàn';await batchEnqueue();}")
    assert await page.evaluate("batchState.jobs[0].engine==='simulation'&&batchSource(batchState.jobs.at(-1))==='gemini_chat'")
    await page.evaluate('batchStart()');assert not posts,'confirmation bypassed'
    await page.locator('#batchConfirmSend').click();await page.wait_for_function("batchState.jobs.at(-1).status==='done'",timeout=15000)
    assert len(posts)==1
    result=await page.evaluate("async()=>{const j=batchState.jobs.at(-1),file=await io('files','readonly',j.resultKey);await SceneForgeStorage.flush();return {source:batchSource(j),type:file.type,bytes:file.size,status:j.status,old:batchState.jobs[0].engine};}")
    assert result['source']=='gemini_chat' and result['type']=='image/png' and result['bytes']==len(png) and result['old']=='simulation',result
    await page.reload();await page.wait_for_function('appBootReady&&SceneForgeStorage.state.active');await page.evaluate("async()=>{document.querySelector('#shellDialog').close();await openBatchStudio();}")
    assert await page.locator('#batchEngine').input_value()=='gemini_chat'
    assert len(posts)==1,'reload resent generation'
    await page.locator('#batchImageChoice').select_option('["gemini",""]')
    await page.locator('#batchCheckModels').click()
    await page.wait_for_function('document.querySelector("#batchImageChoice").value===JSON.stringify(["gemini","gemini-image-fixture"])')
    await page.locator('#batchImageChoice').select_option('["flow",""]')
    assert await page.locator('#batchImageModel').input_value()==''
    await page.locator('#batchCheckModels').click()
    await page.wait_for_function('document.querySelector("#batchImageChoice").value===JSON.stringify(["flow","imagen-fixture"])')
    assert len(posts)==1
    await page.locator('#batchImageChoice').select_option('["simulation",""]');await page.evaluate('batchPersist()');await page.evaluate('SceneForgeStorage.flush()');await page.reload();await page.wait_for_function('appBootReady&&SceneForgeStorage.state.active');await page.evaluate("async()=>{document.querySelector('#shellDialog').close();await openBatchStudio();}")
    assert await page.locator('#batchEngine').input_value()=='simulation','explicit simulation choice lost'
    assert not errors,errors
    print('PASS Gemini default, remembered source including explicit simulation, preserved old jobs, confirmation, actual PNG into SQLite/IndexedDB, reload no resend',result)
    await browser.close()
if __name__=='__main__':asyncio.run(main())
