"""Native first, controlled after close; a live port/rejected page is not a login."""
import asyncio,importlib,sys,tempfile,types,ast
from pathlib import Path
from unittest.mock import AsyncMock,Mock,patch
ROOT=Path(__file__).resolve().parents[2]
async def main():
 with tempfile.TemporaryDirectory()as td:
  pkg=Path(td)/'flow_login_test';pkg.mkdir();(pkg/'__init__.py').write_text('')
  for n in ('google_login.py','flow_web_login.py'):(pkg/n).write_bytes((ROOT/'veo-node-v46/local_engine'/n).read_bytes())
  sys.path.insert(0,td)
  connection=types.ModuleType('flow_login_test.flow_connection');connection.public_error=lambda e:{'message':'error'};sys.modules[connection.__name__]=connection
  probe=types.ModuleType('flow_login_test.flow_browser_probe');probe.probe_flow_browser=AsyncMock(return_value={'ready':False});sys.modules[probe.__name__]=probe
  mod=importlib.import_module('flow_login_test.flow_web_login')
  bindings={'old':{'profile_key':'a'*24},'selected':{'profile_key':'b'*24}}
  vault=types.SimpleNamespace(rows=lambda _:[{'id':'old','service':'flow','session_verified':True,'state':'ready'},{'id':'selected','service':'flow','session_verified':True,'state':'ready'}],put=Mock(),secret=lambda k:bindings if k=='flow-managed-profiles'else{},set_secret=Mock())
  accounts=types.SimpleNamespace(vault=vault,pool=types.SimpleNamespace(status=lambda:{'account_id':'selected'}))
  flow=mod.FlowWebLogin(td,accounts);flow.managed_driver=lambda:object();flow.watch=AsyncMock()
  proc=Mock();proc.poll.return_value=None;manual=types.SimpleNamespace(process=proc,close=AsyncMock())
  with patch.object(mod,'open_flow_manual_login',AsyncMock(return_value=manual))as native,patch.object(mod,'open_flow_web_login',AsyncMock())as controlled:
   result=await flow.start(account_id='old');assert result['phase']=='manual_signin'and flow.profile_key=='a'*24
   await asyncio.sleep(0);controlled.assert_not_awaited();flow.watch.assert_not_awaited();assert native.await_args.args[-1]=='a'*24
   proc.poll.return_value=0;await flow.task
   controlled.assert_awaited_once_with(flow.data,auto_connect=True,profile_key='a'*24);flow.watch.assert_awaited_once();manual.close.assert_awaited_once()
  print('PASS clicked old-account profile pinned, native sign-in first, no early controlled browser, same profile capture only after close')
  # Simulate the already-open rejected page in the user's screenshot.
  for url,code in [('https://accounts.google.com/v3/signin/rejected?continue=SECRET','GOOGLE_BROWSER_SIGNIN_REJECTED'),('https://accounts.google.com/v3/signin/identifier?continue=SECRET','FLOW_BROWSER_LOGIN_REQUIRED')]:
   page=types.SimpleNamespace(url=url);context=types.SimpleNamespace(pages=[page],cookies=AsyncMock());browser=types.SimpleNamespace(contexts=[context],is_connected=lambda:True)
   pw=types.SimpleNamespace(chromium=types.SimpleNamespace(connect_over_cdp=AsyncMock(return_value=browser)),stop=AsyncMock())
   api=types.ModuleType('playwright.async_api');api.async_playwright=lambda:types.SimpleNamespace(start=AsyncMock(return_value=pw))
   flow=mod.FlowWebLogin(td,accounts);flow.request_account_id='old';flow.import_account=AsyncMock();probe.probe_flow_browser.return_value={'ready':True,'endpoint':'http://127.0.0.1:1'}
   with patch.dict(sys.modules,{'playwright.async_api':api}):await flow.watch()
   assert flow.status()['state']=='failed'and flow.status()['code']==code,flow.status()
   assert vault.put.call_args.args[1]['id']=='old'and vault.put.call_args.args[1]['session_verified']is False
   assert 'SECRET'not in str(flow.status());flow.import_account.assert_not_awaited();context.cookies.assert_not_awaited();pw.stop.assert_awaited_once()
  print('PASS rejected/sign-in pages never imported, no credential reads/retry, no redirect query exported')
  # The actual saved-account endpoint must not treat DevTools readiness as auth.
  tree=ast.parse((ROOT/'veo-node-v46/local_engine/server.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef)and n.name=='open_saved_profile');node.decorator_list=[]
  service=types.SimpleNamespace(start=AsyncMock(return_value={'opened':True,'state':'waiting'}));env={'account':lambda _: {'id':'old','service':'flow'},'SIMPLE_FLOW':types.SimpleNamespace(busy=lambda:False),'VAULT':vault,'FLOW_WEB_LOGIN':service}
  exec(compile(ast.Module(body=[node],type_ignores=[]),'endpoint','exec'),env)
  await env['open_saved_profile']({'id':'old'});service.start.assert_awaited_once_with(account_id='old')
  print('PASS saved-account route uses login verification, not live-port success')
asyncio.run(main())
