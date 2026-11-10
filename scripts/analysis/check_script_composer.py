"""Structured AI script draft + real library UI/save/copy tests, no provider calls."""
import asyncio,importlib,json,sys,tempfile,types,zipfile
from pathlib import Path
import httpx
from fastapi import FastAPI,HTTPException
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
async def main():
 with tempfile.TemporaryDirectory(prefix='sf-script108-')as td:
  tmp=Path(td);pkg=tmp/'compose_runtime';pkg.mkdir();(pkg/'__init__.py').write_text('')
  with zipfile.ZipFile(ROOT/'downloads/v46/SceneForge-Veo-v46-Source.zip')as z:
   for name in ['library.py','library_api.py','library_lock.py','storage_lifecycle.py','schema.py','instance.py','storage_jobs.py','request_ledger.py']:(pkg/name).write_bytes(z.read('local_engine/'+name))
  for name in ['script_library.py','script_composer.py']:
   src=Path('local_engine')/name;src=src if src.exists()else ROOT/'veo-node-v46/local_engine'/name;(pkg/name).write_bytes(src.read_bytes())
  sys.path.insert(0,td);api=importlib.import_module('compose_runtime.library_api');sl=importlib.import_module('compose_runtime.script_library');composer=importlib.import_module('compose_runtime.script_composer');ledger_mod=importlib.import_module('compose_runtime.request_ledger')
  app=FastAPI();data=tmp/'data';data.mkdir();lib=api.install_library(app,data);ledger=ledger_mod.RequestLedger(data);calls=[];requests=[];delay=False;drop_response=False;seen=asyncio.Event();release=asyncio.Event()
  vault=types.SimpleNamespace(secret=lambda k:{'source':'gemini_chat'}if k=='ai-routing'else None)
  async def ai(body,instruction):
   rid,cached=ledger.claim(body['request_id'],{'body':body,'instruction':instruction,'media':None})
   if cached is not ledger_mod.NO_RESULT:return cached
   calls.append(json.loads(json.dumps(body)));assert 'khách Việt Nam'in instruction and 'Không bịa'in instruction
   if delay:seen.set();await release.wait()
   if not body.get('facts')and not body.get('answers'):raw={'needs_info':True,'questions':['Điểm nổi bật nào của sản phẩm đã được xác nhận?'],'variants':[]}
   else:raw={'needs_info':False,'questions':[],'variants':[{'title':'Hướng '+str(i),'angle':'Hướng tiếp cận '+str(i),'hook':'Mở đầu '+str(i)+'.','body':'Mở đầu '+str(i)+'.\n\nSản phẩm có thông tin bạn đã cung cấp.\n\nXem thêm thông tin bên dưới.','notes':[]}for i in range(1,4)]}
   ledger.finish(rid,'done',raw);return raw
  class Chat:
   async def execute_json(self,body,instruction,**kwargs):
    assert kwargs.get('read_only')is True
    with ledger.connect()as db:r=db.execute('SELECT state,result FROM request WHERE id=?',(body['request_id'],)).fetchone()
    if not r or r[0]!='done':raise HTTPException(409,'Chưa có kết quả, không tự gửi lại.')
    return json.loads(r[1])
  sl.install_script_library(app,vault,ledger,Chat(),ai)
  valid={'action':'compose','brief':'Viết video bán giày','facts':'Đế cao su, giá 250 nghìn','product_name':'Giày','target_seconds':30,'tone':'gan-gui'}
  assert composer.validate_input(valid)==composer.INSTRUCTION
  assert sl.validate_input({'action':'write','idea':'x','product_name':'giày','target_seconds':30})==sl.WRITE
  try:composer.validate_input({**valid,'target_seconds':True});raise AssertionError('bool duration accepted')
  except HTTPException:pass
  try:composer.validate_result({'needs_info':False,'variants':[]});raise AssertionError('empty variants accepted')
  except HTTPException:pass
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local')as client:
   bad=await client.post('/local-api/ai/script-library',json={**valid,'expected_store_id':'wrong','ai_source':'gemini_chat'});assert bad.status_code==409 and not calls
   async with async_playwright()as pw:
    browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1440,'height':1050});errors=[];dialogs=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.message),asyncio.create_task(d.dismiss())))
    async def route(r):
     nonlocal drop_response
     path=r.request.url.split('/local-api/')[-1]
     if '/local-api/library/'in r.request.url or '/local-api/ai/script-library'in r.request.url:
      requests.append((r.request.method,path,r.request.post_data));res=await client.request(r.request.method,'/local-api/'+path,content=r.request.post_data_buffer,headers={'content-type':'application/json'});
      if drop_response and path=='ai/script-library'and r.request.method=='POST':drop_response=False;await r.fulfill(status=502,json={'detail':'Fixture lost response; request already sent'});return
      await r.fulfill(status=res.status_code,body=res.content,content_type=res.headers.get('content-type','application/json'));return
     if '/local-api/'in r.request.url:await r.fulfill(json=[]if path in ['accounts','logs','notifications']else{});return
     if r.request.resource_type=='document':await r.fulfill(body=(Path(sys.argv[1])if len(sys.argv)>1 else Path('index.html')if Path('index.html').exists()else ROOT/'index.html').read_text(),content_type='text/html');return
     await r.fulfill(status=404,body='')
    await page.route('**/*',route);await page.goto('http://127.0.0.1:43895/');await page.wait_for_function('appBootReady&&SceneForgeStorage.state.active')
    await page.evaluate("async()=>{prefs.package5WelcomeDone=true;await savePrefs();document.querySelector('#shellDialog').close();await g6OpenRecipes()}")
    await page.locator('[data-sc=open]').click();await page.locator('[data-sc-field=brief]').fill('Viết video bán đôi giày này cho người đi làm')
    await page.locator('[data-sc=generate]:visible').click();await expect(page.locator('.scQuestions')).to_contain_text('Điểm nổi bật');assert len(calls)==1
    await page.locator('[data-sc-field=answers]').fill('Đế cao su, giá 250 nghìn. Không có ưu đãi.')
    await page.locator('[data-sc=generate]:visible').click();await expect(page.locator('.scChoices button')).to_have_count(3);assert len(calls)==2 and not dialogs
    await page.locator('[data-sc-choice="1"]').click();await page.locator('#scBody').fill('Lời đã sửa theo cách tôi nói.\n\nThông tin tôi xác nhận.');await page.evaluate('SceneForgeStorage.flush()');assert next(r for r in lib.snapshot()['records']if r['store']=='prefs'and r['key']=='main')['value']['scriptComposer']['runs'][-1]['edits']['1']=='Lời đã sửa theo cách tôi nói.\n\nThông tin tôi xác nhận.'
    await page.locator('[data-sc=close]').click();await page.locator('[data-sc=open]').click();await expect(page.locator('#scBody')).to_have_value('Lời đã sửa theo cách tôi nói.\n\nThông tin tôi xác nhận.')
    await page.locator('[data-sc=save]').click();await page.wait_for_function("!document.querySelector('#scPanel')&&recipeCache.items.some(r=>r.kind==='script'&&r.body.startsWith('Lời đã sửa'))")
    stored=await page.evaluate("recipeCache.items.find(r=>r.body?.startsWith('Lời đã sửa'))");assert stored['kind']=='script'
    # Use existing room-copy path; avoid loading a full photo frame in this fixture.
    await page.evaluate("window.realOpenRoom=openRoom;openRoom=async id=>{window.openedScriptRoom=id}")
    await page.locator('[data-v4=use-script]').click();await page.locator('[data-choose-product]').first.click();await page.wait_for_function('!!window.openedScriptRoom')
    copied=await page.evaluate("(()=>{const r=roomFor(openedScriptRoom),original=recipeCache.items.find(x=>x.id===r.photoDraft.sourceScriptId);r.photoDraft.beats[0].text='Edited inside video';return {original:original.body,copied:r.photoDraft.sourceScriptBody}})()")
    assert copied['original']==copied['copied']==stored['body']
    # Losing a completed response retains the input and recovers the same request.
    await page.evaluate('g6OpenRecipes()');await page.locator('[data-sc=open]').click();drop_response=True
    await page.locator('[data-sc=generate]:visible').click();await page.wait_for_function("prefs.scriptComposer.runs.at(-1).status==='error'");assert len(calls)==3
    await expect(page.locator('[data-sc=fresh]')).to_be_visible()
    await page.locator('[data-sc=generate]:visible').click();await expect(page.locator('.scChoices button')).to_have_count(3);assert len(calls)==3
    # A pending AI response may finish after navigation, without taking the tab back.
    await page.evaluate('g6OpenRecipes()');await page.locator('[data-sc=open]').click();delay=True
    await page.locator('[data-sc=generate]:visible').click();await asyncio.wait_for(seen.wait(),10);assert len(calls)==4
    await page.locator('.rail [data-view=overview]').click();await page.wait_for_function("!g6RecipeOpen&&currentView==='overview'")
    release.set();await page.wait_for_function("prefs.scriptComposer.runs.at(-1).status==='done'");assert await page.evaluate('currentView')=='overview'
    # Cached recovery uses the same request and no additional provider dispatch.
    submitted=next(x for x in reversed(requests)if x[0]=='POST'and x[1]=='ai/script-library');body=json.loads(submitted[2]);body['recovery']=True;res=await client.post('/local-api/ai/script-library',json=body);assert res.status_code==200 and len(calls)==4
    await page.evaluate('g6OpenRecipes()');await expect(page.locator('[data-sc=save]')).to_be_enabled();await page.screenshot(path='/tmp/sceneforge-script-composer108.png');assert not errors,errors
    assert all(not path.startswith(('flow/','ai/image','ai/video'))for _,path,_ in requests)
    await browser.close()
 print('PASS brief→questions→3 drafts; edited draft survives close/reopen; real IndexedDB/SQLite library save; video gets independent copy; late result does not steal navigation; request recovery no redispatch; old node write contract retained. Fixture AI only, no real Gemini/provider/Windows run.')
asyncio.run(main())
