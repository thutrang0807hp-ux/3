"""Real Chromium profile restart, isolated cookies/storage and stable identity settings.

CI runs headless via a test-only launch override; production always uses the same
headed mode for login, checking and work. No external account verification.
"""
import asyncio,ast,copy,importlib,json,sys,tempfile,threading,time,types,uuid,zipfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from unittest.mock import patch
from fastapi import HTTPException
from playwright.async_api import BrowserType
ROOT=Path('/workspace/3')
async def main():
 with tempfile.TemporaryDirectory(prefix='sf profiles ')as td:
  root=Path(td);pkg=root/'profile_runtime';pkg.mkdir();(pkg/'__init__.py').write_text('')
  with zipfile.ZipFile(ROOT/'downloads/v46/SceneForge-Veo-v46-Source.zip')as z:
   for name in ['vault.py','schema.py']:(pkg/name).write_bytes(z.read('local_engine/'+name))
  for name in ['browser_profiles.py','google_login.py']:
   src=Path('local_engine')/name;src=src if src.exists()else ROOT/'veo-node-v46/local_engine'/name;(pkg/name).write_bytes(src.read_bytes())
  sys.path.insert(0,td);mod=importlib.import_module('profile_runtime.browser_profiles');Vault=importlib.import_module('profile_runtime.vault').Vault;data=root/'data';vault=Vault(data)
  for id in ['A','B']:vault.put('accounts',{'id':id,'name':id,'service':'grok','enabled':True,'state':'ready'})
  class Handler(BaseHTTPRequestHandler):
   def do_GET(self):self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<title>Local session fixture</title>')
   def log_message(self,*args):pass
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
  original=BrowserType.launch_persistent_context
  async def ci_launch(self,*a,**kw):kw['headless']=True;kw['args']=[*kw.get('args',[]),'--no-sandbox'];return await original(self,*a,**kw)
  manager=mod.Profiles(vault,data);entry=manager.reserve('grok','A');other=manager.reserve('grok','B');assert entry!=other;cfg=manager.settings(entry,'/usr/bin/chromium');assert cfg['viewport']=={'width':1280,'height':800}
  with patch.object(BrowserType,'launch_persistent_context',ci_launch):
   pw,browser=await manager.browser(entry);ctx=await browser.new_context();page=await ctx.new_page();await page.goto(url);await ctx.add_cookies([{'name':'session','value':'PRIVATE_A','url':url}]);await page.evaluate("localStorage.setItem('account','A')");ident=await page.evaluate('({ua:navigator.userAgent,platform:navigator.platform,language:navigator.language,w:innerWidth,h:innerHeight})');state=await ctx.storage_state()
   try:manager.ensure_idle('A');assert False
   except HTTPException as e:assert e.status_code==409
   waiting=asyncio.create_task(manager.browser(entry,state));await asyncio.sleep(.03);assert not waiting.done();waiting.cancel()
   try:await waiting
   except asyncio.CancelledError:pass
   await browser.close();await pw.stop()
   # Simulate a companion restart: reopen vault and manager, then same disk profile.
   vault2=Vault(data);manager=mod.Profiles(vault2,data);again=manager.reserve('grok','A');assert again==entry and manager.settings(again)['identity_id']==cfg['identity_id']
   pw,browser=await manager.browser(again,state);ctx=await browser.new_context();page=await ctx.new_page();await page.goto(url);assert await page.evaluate("localStorage.getItem('account')")=='A';assert next(c for c in await ctx.cookies(url)if c['name']=='session')['value']=='PRIVATE_A';assert await page.evaluate('({ua:navigator.userAgent,platform:navigator.platform,language:navigator.language,w:innerWidth,h:innerHeight})')==ident
   await ctx.add_cookies([{'name':'session','value':'REFRESHED_A','url':url,'expires':2000000000}]);fresh=await ctx.storage_state();await browser.close();await pw.stop()
   pw,browser=await manager.browser(again,state);ctx=await browser.new_context();assert next(c for c in await ctx.cookies(url)if c['name']=='session')['value']=='REFRESHED_A','Old saved snapshot must not overwrite the newer browser cookie';await browser.close();await pw.stop()
   pw,browser=await manager.browser(other);ctx=await browser.new_context();page=await ctx.new_page();await page.goto(url);assert not await ctx.cookies(url);assert await page.evaluate("localStorage.getItem('account')")is None;await browser.close();await pw.stop()
  # Native Chrome/Edge login lifecycle: exercise actual subprocess + CDP, with
  # a test-only headless/local-origin substitution before the process is launched.
  google=importlib.import_module('profile_runtime.google_login');real_popen=google.subprocess.Popen
  def native_fixture(args,**kw):
   if args and str(args[0])=='/usr/bin/chromium':args=[*args[:-1],'--headless=new','--no-sandbox',url]
   return real_popen(args,**kw)
  vault2.put('accounts',{'id':'G','name':'Google fixture','service':'gemini_chat'})
  native_entry=manager.reserve('gemini_chat','G');native_cfg=manager.settings(native_entry,'/usr/bin/chromium')
  with patch.object(google.subprocess,'Popen',native_fixture):
   login=await manager.native(native_entry,'https://gemini.google.com/');await login.cookies();context=login.connection.contexts[0];await context.add_cookies([{'name':'native','value':'PRIVATE_NATIVE','url':url,'expires':2000000000}]);page=context.pages[0];await page.evaluate("localStorage.setItem('native','saved')")
   try:await manager.native(native_entry,'https://gemini.google.com/');assert False
   except HTTPException as e:assert e.status_code==409
   await login.close();assert manager.path('gemini_chat',native_entry['key']).exists()
   login=await manager.native(native_entry,'https://gemini.google.com/');cookies=await login.cookies();assert any(c['name']=='native'and c['value']=='PRIVATE_NATIVE'for c in cookies);assert await login.connection.contexts[0].pages[0].evaluate("localStorage.getItem('native')")=='saved';assert manager.settings(native_entry)['identity_id']==native_cfg['identity_id'];await login.close()
  # Removing B cannot erase A; tentative cancelled profiles are discarded only.
  await manager.remove('B');assert not manager.path(other['service'],other['key']).exists()and manager.path(entry['service'],entry['key']).exists();tentative=manager.reserve('chatgpt');await manager.discard(tentative);assert not manager.path('chatgpt',tentative['key']).exists();await manager.discard(entry);assert manager.path(entry['service'],entry['key']).exists()
  try:manager.path('grok','../outside');assert False
  except HTTPException:pass
  try:manager.reserve('chatgpt','A');assert False
  except HTTPException:pass
  assert mod.saved_cookies({'cookies':[{'domain':'.google.com','name':'s','value':'a'},{'domain':'evil.invalid','name':'s','value':'b'}]},'gemini_chat')==[{'domain':'.google.com','name':'s','value':'a'}]
  # Run actual Muse backend handlers against the real encrypted vault, replacing
  # only the external browser. Save/reopen/cancel must bind and preserve one id.
  tree=ast.parse((Path('local_engine/server.py')if Path('local_engine/server.py').exists()else ROOT/'veo-node-v46/local_engine/server.py').read_text())
  nodes=[copy.deepcopy(n)for n in tree.body if isinstance(n,ast.AsyncFunctionDef)and n.name in ['connect_account','save_login','cancel_account_login','remove_account','open_saved_profile']]
  for n in nodes:n.decorator_list=[]
  factory=mod.profiles(vault2,data);opened=[]
  class FakeBrowser:
   def __init__(self):self.closed=False
   async def cookies(self):return [{'domain':'.muse.ai','name':'session','value':'PRIVATE_MUSE'},{'domain':'.wrong.invalid','name':'no','value':'DO_NOT_IMPORT'}]
   async def close(self):self.closed=True
   async def stop(self):pass
  async def fake_native(entry,url,cookies=None):opened.append(dict(entry));return FakeBrowser()
  ns={'__package__':'profile_runtime','asyncio':asyncio,'time':time,'uuid':uuid,'HTTPException':HTTPException,'VAULT':vault2,'DATA':data,'LOGINS':{},'account':lambda aid:next(dict(a)for a in vault2.rows('accounts')if a['id']==aid),'MUSE_PROVIDER':types.SimpleNamespace(lock=lambda aid:asyncio.Lock(),phases={},remove=lambda aid:None)}
  exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'actual-profile-handlers','exec'),ns)
  with patch.object(factory,'native',fake_native):
   result=await ns['connect_account']({'service':'muse'});mid=result['id'];await ns['save_login']({'id':mid});bound=factory.registry()[mid];row=ns['account'](mid);assert row['browser_profile_id']==bound['key'][:8]and row['state']=='unverified';assert len(vault2.secret('account:'+mid)['cookies'])==1
   await ns['connect_account']({'service':'muse','account_id':mid});assert opened[-1]==bound;await ns['cancel_account_login']({'id':mid});assert ns['account'](mid)['browser_profile_id']==bound['key'][:8]and factory.path('muse',bound['key']).exists()
   temp=await ns['connect_account']({'service':'muse'});temporary=opened[-1];await ns['cancel_account_login']({'id':temp['id']});assert not any(a['id']==temp['id']for a in vault2.rows('accounts'))and not factory.path('muse',temporary['key']).exists()
   await ns['remove_account']({'id':mid});assert not any(a['id']==mid for a in vault2.rows('accounts'))and not factory.path('muse',bound['key']).exists()
  vault2.put('accounts',{'id':'F','name':'Flow fixture','service':'flow'});ns['SIMPLE_FLOW']=types.SimpleNamespace(busy=lambda:True)
  try:await ns['open_saved_profile']({'id':'F'});assert False
  except HTTPException as e:assert e.status_code==409
  gemini=Path('local_engine/gemini_chat.py');gemini=gemini if gemini.exists()else ROOT/'veo-node-v46/local_engine/gemini_chat.py';tree=ast.parse(gemini.read_text());klass=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='GeminiChat');method=copy.deepcopy(next(n for n in klass.body if isinstance(n,ast.AsyncFunctionDef)and n.name=='login'));locked=asyncio.Lock();await locked.acquire();gns={'__package__':'profile_runtime','HTTPException':HTTPException};exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'actual-gemini-busy-guard','exec'),gns);obj=types.SimpleNamespace(require_sdk=lambda:None,logins={},vault=vault2,data=data,lock=lambda aid:locked,phases={})
  try:await gns['login'](obj,{'name':'Google fixture','account_id':'G'});assert False
  except HTTPException as e:assert e.status_code==409
  finally:locked.release()
  raw=(data/'vault.sqlite').read_bytes();assert b'account-browser-profiles-v1'in raw and entry['key'].encode()not in raw,'Registry values must use the encrypted vault';server.shutdown()
 print('PASS real browser restart retains cookies/localStorage and UA/platform/language/viewport; encrypted stable profile mapping; account isolation; session-cookie restore; fresh cookie beats old snapshot; cancellable profile serialization; safe removal/path guards. Headless CI only; no real provider accounts.')
if __name__=='__main__':asyncio.run(main())
