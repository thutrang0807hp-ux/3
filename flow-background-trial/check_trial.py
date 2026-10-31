"""Actual headless persistent-profile trial; every web request intercepted."""
import asyncio,json,sys,tempfile,time
from pathlib import Path
from unittest.mock import AsyncMock,patch
sys.path.insert(0,'/workspace/sceneforge')
from playwright.async_api import async_playwright
from local_engine.vault import Vault
from local_engine.account_pool import AccountPool
from local_engine.google_login import flow_profile_path
from probe import probe

async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);vault=Vault(root);pool=AccountPool(vault,'flow');aid='flow-web-fixture';key='c'*24
  vault.put('accounts',{'id':aid,'service':'flow','name':'Fixture','enabled':True,'session_verified':True,'state':'ready','active':False,'priority':0,'login_transport':'web_ui'})
  vault.set_secret('flow-managed-profiles',{aid:{'account_id':aid,'email':'fixture@invalid','profile_key':key}});pool.select({'mode':'selected','account_id':aid})
  profile=flow_profile_path(root,key);profile.mkdir(parents=True)
  original_rows=vault.rows('accounts');original_binding=vault.secret('flow-managed-profiles');state={'kind':'normal'};launches=[];requests=[]
  async with async_playwright()as pw:
   async def factory(path):
    assert path==profile;launches.append(str(path))
    context=await pw.chromium.launch_persistent_context(str(path),executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--host-resolver-rules=MAP * ~NOTFOUND'])
    async def route(r):
     requests.append(r.request.url)
     if state['kind']=='redirect'and 'flow.google.com'in r.request.url:return await r.fulfill(status=302,headers={'Location':'https://accounts.google.com/'})
     email='other@invalid'if state['kind']=='other'else'fixture@invalid'
     authenticated='fixture_session=stored-fixture'in r.request.headers.get('cookie','')
     identity="<script>window.WIZ_global_data={oPEP7c:'"+email+"'}</script>"if authenticated and state['kind']!='missing'else''
     if state['kind']=='challenge':identity+='<div role=alert>Unusual activity</div>'
     await r.fulfill(content_type='text/html; charset=utf-8',body=identity+'<p>Fixture only</p>')
    await context.route('**/*',route)
    page=context.pages[0];cdp=await context.new_cdp_session(page);info=await cdp.send('Browser.getVersion');assert 'HeadlessChrome'in info.get('userAgent','');await cdp.detach()
    return context
   seed=await factory(profile)
   await seed.add_cookies([{'name':'fixture_session','value':'stored-fixture','domain':'flow.google.com','path':'/','expires':time.time()+3600,'secure':True}]);await seed.close()
   outputs=[]
   for kind,expected in [('normal','BACKGROUND_SESSION_OK'),('other','ACCOUNT_MISMATCH'),('missing','IDENTITY_UNREADABLE'),('challenge','VERIFICATION_REQUIRED'),('redirect','FLOW_NAVIGATION_FAILED')]:
    state['kind']=kind;out=await probe(root,vault,factory,identity_timeout=.4);outputs.append(out);assert out['code']==expected,(kind,expected,out)
   from types import SimpleNamespace
   async def login_page(path):return SimpleNamespace(pages=[SimpleNamespace(url='https://accounts.google.com/',goto=AsyncMock())],close=AsyncMock())
   assert(await probe(root,vault,login_page))['code']=='AUTH_REQUIRED'
   before=len(launches)
   with patch('local_engine.flow_browser_probe.probe_flow_browser',new=AsyncMock(return_value={'ready':True,'code':'FLOW_BROWSER_READY'})):
    assert(await probe(root,vault,factory))['code']=='VISIBLE_FLOW_STILL_OPEN'
   assert len(launches)==before
   async def busy(path):raise RuntimeError('Fixture profile busy')
   assert(await probe(root,vault,busy))['code']=='PROFILE_IN_USE_OR_START_FAILED'
   assert vault.rows('accounts')==original_rows and vault.secret('flow-managed-profiles')==original_binding
   assert all(not r['generation_attempted']and not r['account_data_exported']for r in outputs)
   serialized=json.dumps(outputs);assert 'fixture@invalid'not in serialized and 'stored-fixture'not in serialized
 print('PASS background trial: actual headless Chromium reopens the exact persistent profile and uses its saved fixture session; wrong identity, missing identity, challenge, login redirect and busy/live profile stop; zero generation requests and no account/cookie values in output. No Google calls or Windows verification.')
if __name__=='__main__':asyncio.run(main())
