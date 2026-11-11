"""Shared Settings accounts across four image adapters; real queue/storage, mocked providers."""
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
  sys.path.insert(0,td);api=importlib.import_module('batch_runtime.library_api');app=FastAPI();data=tmp/'data';data.mkdir();lib=api.install_library(app,data);posts=[];account_state={s:{'name':'Saved A '+s,'token':'token-a-'+s,'installed':True}for s in ['gemini_chat','chatgpt','grok','meta']};login_posts=[]
  buf=io.BytesIO();Image.new('RGB',(90,160),'green').save(buf,'PNG');png=buf.getvalue()
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local') as client:
   async with async_playwright() as pw:
    browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    async def route(r):
     url=r.request.url;path=url.split('/local-api/')[-1]
     if '/local-api/library/' in url:
      res=await client.request(r.request.method,'/local-api/'+path,content=r.request.post_data_buffer,headers={'content-type':'application/json'});await r.fulfill(status=res.status_code,body=res.content,content_type=res.headers.get('content-type','application/json'));return
     source='gemini_chat' if path=='gemini-chat/status' else next((k for k in ['chatgpt','grok','meta'] if path=='web-images/'+k+'/status'),None)
     if source:
      state=account_state[source];await r.fulfill(json={'installed':state['installed'],'configured':True,'image_per_account':1,'image_maximum_setting':4,'selection':{'available':True,'mode':'selected','token':state['token'],'account_name':state['name'],'account_id':source+'-account'}});return
     if path in ['gemini-chat/jobs','web-images/jobs'] and r.request.method=='POST':
      body=r.request.post_data_json;source='gemini_chat' if path=='gemini-chat/jobs' else body['source'];posts.append(body);assert body['selection_token']==account_state[source]['token'];assert body['kind']=='image';await r.fulfill(json={'request_id':body['request_id'],'state':'done','result':{'mime_type':'image/png','model':'fixture-image','account_id':source+'-account'}});return
     if path.startswith(('gemini-chat/files/','web-images/files/')):
      await r.fulfill(body=png,content_type='image/png');return
     if r.request.method=='POST' and any(k in path for k in ['login','connect','confirm']):login_posts.append(path)
     if '/local-api/' in url:await r.fulfill(json=[] if path in ['accounts','logs','notifications'] else {});return
     if r.request.resource_type=='document':await r.fulfill(body=(ROOT/'index.html').read_text(),content_type='text/html');return
     await r.fulfill(status=404,body='')
    await page.route('**/*',route);await page.goto('http://127.0.0.1:43895/');await page.wait_for_function('appBootReady&&SceneForgeStorage.state.active')
    await page.evaluate("async()=>{prefs.package5WelcomeDone=true;await savePrefs();document.querySelector('#shellDialog').close();await openBatchStudio();}")
    await page.evaluate("window.settingsTarget=null;accountScreen=async service=>{settingsTarget=service;modal('Cài đặt tài khoản mẫu','<p>Tài khoản đã lưu trong Cài đặt</p>','');};true;")
    for source in ['gemini_chat','chatgpt','grok','meta']:
     await page.locator('#batchEngine').select_option(source);await page.wait_for_function("document.querySelector('#batchAccountNow').dataset.accountState==='ready'")
     assert 'Saved A '+source in await page.locator('#batchAccountNow').text_content()
     await page.locator('#batchConnectSource').click(timeout=4000);assert await page.evaluate('settingsTarget')==source
     account_state[source].update(name='Saved B '+source,token='token-b-'+source)
     await page.evaluate("document.querySelector('#shellDialog').close()")
     await page.wait_for_function("source=>document.querySelector('#batchAccountNow').textContent.includes('Saved B '+source)",arg=source)
     await page.evaluate("async source=>{document.querySelector('#batchPrompts').value='Ảnh '+source;await batchEnqueue();await batchStart();}",source)
     count=len(posts);await page.locator('#batchConfirmSend').click();await page.wait_for_function("batchState.jobs.at(-1).status==='done'",timeout=15000);assert len(posts)==count+1
     assert posts[-1]['selection_token']=='token-b-'+source
    # Changing the Settings selection after review must not dispatch to the new account silently.
    await page.locator('#batchEngine').select_option('gemini_chat')
    await page.evaluate("async()=>{document.querySelector('#batchPrompts').value='Token change';await batchEnqueue();await batchStart();}")
    before=len(posts);account_state['gemini_chat'].update(token='changed-after-review')
    await page.locator('#batchConfirmSend').click();await page.wait_for_function("document.querySelector('#batchConfirmError').textContent.includes('đã đổi')");assert len(posts)==before
    await page.evaluate("document.querySelector('#shellDialog').close()")
    assert not login_posts,login_posts
    assert not errors,errors
    print('PASS shared Settings account refresh + image submission for Gemini Chat/ChatGPT/Grok/Meta; no login/code per batch; changed selection after review blocks send; stored image files; provider mocked')
    await browser.close()
if __name__=='__main__':asyncio.run(main())
