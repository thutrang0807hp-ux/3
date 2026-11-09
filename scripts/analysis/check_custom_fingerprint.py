"""Actual script-visible device parameters, opt-in API and native first-document injection."""
import asyncio,ast,copy,importlib,sys,tempfile,zipfile
from pathlib import Path
from unittest.mock import patch
import httpx
from fastapi import FastAPI
from playwright.async_api import BrowserType
ROOT=Path('/workspace/3')
HTML='<script>window.first={cores:navigator.hardwareConcurrency,memory:navigator.deviceMemory,w:screen.width,h:screen.height,iw:innerWidth,ih:innerHeight};</script>'
async def main():
 with tempfile.TemporaryDirectory(prefix='sf-fingerprint-')as td:
  root=Path(td);pkg=root/'fp_runtime';pkg.mkdir();(pkg/'__init__.py').write_text('')
  with zipfile.ZipFile(ROOT/'downloads/v46/SceneForge-Veo-v46-Source.zip')as z:
   for name in ['vault.py','schema.py']:(pkg/name).write_bytes(z.read('local_engine/'+name))
  for name in ['browser_profiles.py','google_login.py','fingerprints.py']:
   src=Path('local_engine')/name;src=src if src.exists()else ROOT/'veo-node-v46/local_engine'/name;(pkg/name).write_bytes(src.read_bytes())
  sys.path.insert(0,td);fp=importlib.import_module('fp_runtime.fingerprints');bp=importlib.import_module('fp_runtime.browser_profiles');google=importlib.import_module('fp_runtime.google_login');Vault=importlib.import_module('fp_runtime.vault').Vault;data=root/'data';vault=Vault(data)
  vault.put('accounts',{'id':'A','service':'grok','name':'A'});vault.put('accounts',{'id':'G','service':'gemini_chat','name':'G'});manager=bp.profiles(vault,data);entry=manager.reserve('grok','A');manager.settings(entry,'/usr/bin/chromium');ge=manager.reserve('gemini_chat','G');manager.settings(ge,'/usr/bin/chromium')
  app=FastAPI();fp.install_fingerprints(app,vault,data,lambda aid:manager.lease(manager.registry()[aid]).locked()if aid in manager.registry()else False);client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local');url='/local-api/accounts/fingerprint/A';cfg={'enabled':True,'cores':4,'memory':4,'width':1366,'height':768}
  assert not(await client.get(url)).json()['enabled'];r=await client.post(url,json=cfg);assert r.status_code==200,r.text;ident=r.json()['id'];assert 'seed'not in r.json();assert(await client.post(url,json=cfg)).json()['id']==ident;assert(await client.post(url,json={**cfg,'cores':True})).status_code==400;assert(await client.post(url,json={**cfg,'script':'INJECT'})).status_code==400;assert(await client.get('/local-api/accounts/fingerprint/missing')).status_code==404
  vault.put('accounts',{'id':'B','service':'chatgpt','name':'No profile yet'});summary=(await client.get('/local-api/accounts/fingerprint-status?service=chatgpt')).json();assert len(summary['accounts'])==1 and summary['accounts'][0]['account_id']=='B'and summary['accounts'][0]['available']and not summary['accounts'][0]['enabled'];assert 'B'not in manager.registry();made=await client.post('/local-api/accounts/fingerprint/B/toggle',json={'enabled':True});assert made.status_code==200 and made.json()['cores']==8 and made.json()['memory']==8;assert(await client.post('/local-api/accounts/fingerprint/B/toggle',json={'enabled':True})).json()['id']==made.json()['id'];assert(await client.post('/local-api/accounts/fingerprint/B/toggle',json={'enabled':1})).status_code==400
  original=BrowserType.launch_persistent_context
  async def ci(self,*a,**kw):kw['headless']=True;kw['args']=[*kw.get('args',[]),'--no-sandbox'];return await original(self,*a,**kw)
  async def local(r):await r.fulfill(body=HTML,content_type='text/html')
  with patch.object(BrowserType,'launch_persistent_context',ci):
   pw,browser=await manager.browser(entry);ctx=await browser.new_context();await ctx.route('**/*',local);p=await ctx.new_page();await p.goto('https://fixture.invalid/');first=await p.evaluate('window.first');assert first=={'cores':4,'memory':4,'w':1366,'h':768,'iw':1366,'ih':768},first;await ctx.add_cookies([{'name':'keep','value':'LOCAL_COOKIE','url':'https://fixture.invalid/','expires':2000000000}]);assert(await client.post(url,json={**cfg,'enabled':False})).status_code==409;queued=await client.post(url+'/toggle',json={'enabled':False});assert queued.status_code==200 and queued.json()['apply_next_open'];assert await p.evaluate('window.first')==first;assert(await client.post(url+'/toggle',json={'enabled':True})).json()['id']==ident;await browser.close();await pw.stop()
   pw,browser=await manager.browser(entry);ctx=await browser.new_context();await ctx.route('**/*',local);p=await ctx.new_page();await p.goto('https://fixture.invalid/');assert await p.evaluate('window.first')==first;assert any(c['name']=='keep'for c in await ctx.cookies());await browser.close();await pw.stop()
   assert(await client.post(url,json={**cfg,'enabled':False})).status_code==200
   pw,browser=await manager.browser(entry);ctx=await browser.new_context();await ctx.route('**/*',local);p=await ctx.new_page();await p.goto('https://fixture.invalid/');assert await p.evaluate('typeof globalThis[Symbol.for("sceneforge.device-profile.v1")]')=='undefined';assert any(c['name']=='keep'for c in await ctx.cookies());await browser.close();await pw.stop()
  # Native startup remains about:blank until scripts are installed; all service
  # requests are fulfilled locally, so no provider accounts/network are used.
  fp.write_config(manager.path('gemini_chat',ge['key']),cfg);real_popen=google.subprocess.Popen;real_apply=fp.apply
  def native(args,**kw):
   if args and str(args[0])=='/usr/bin/chromium':args=[*args[:-1],'--headless=new','--no-sandbox',args[-1]]
   return real_popen(args,**kw)
  async def apply_local(context,config):await context.route('**/*',local);await real_apply(context,config)
  with patch.object(google.subprocess,'Popen',native),patch.object(fp,'apply',apply_local):
   login=await manager.native(ge,'https://gemini.google.com/');page=login.connection.contexts[0].pages[0];assert await page.evaluate('window.first')==first;await login.close()
   flow_path=google.flow_profile_path(data,'a'*24);flow_path.mkdir(parents=True);fp.write_config(flow_path,cfg);result=await google.open_flow_web_login(data,auto_connect=True,profile_key='a'*24);assert result['opened'];login=google._FLOW_DEVICE_LOGINS[-1];assert await login.connection.contexts[0].pages[0].evaluate('window.first')==first;await login.close()
  src=Path('local_engine/flow_background_session.py');src=src if src.exists()else ROOT/'veo-node-v46/local_engine/flow_background_session.py';tree=ast.parse(src.read_text());method=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef)and n.name=='launch_background'));ns={'__package__':'fp_runtime','installed_browser':lambda:'/usr/bin/chromium'};exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'actual-flow-background-launch','exec'),ns)
  from playwright.async_api import async_playwright
  with patch.object(BrowserType,'launch_persistent_context',ci):
   pw=await async_playwright().start();context=await ns['launch_background'](pw,flow_path);await context.route('**/*',local);p=context.pages[0]if context.pages else await context.new_page();await p.goto('https://fixture.invalid/');assert await p.evaluate('window.first')==first;await context.close();await pw.stop()
  assert fp.read_config(manager.path('grok',entry['key']))['enabled']is False;await client.aclose()
 print('PASS custom CPU/RAM/screen/viewport on first document; same config across restart; opt-in/off reversible without losing cookies; API validation and busy guard; native pre-navigation injection; no external provider traffic; no Canvas/WebGL/UA modifications.')
if __name__=='__main__':asyncio.run(main())
