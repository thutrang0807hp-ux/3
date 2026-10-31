"""Existing web-login -> actual AccountPool -> Veo worker. No Google calls."""
import asyncio,base64,io,tempfile,subprocess,uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
from fastapi import HTTPException
from PIL import Image
from playwright.async_api import async_playwright
from .vault import Vault
from .request_ledger import RequestLedger
from .account_pool import AccountPool
from .flow_web_login import FlowWebLogin
from .flow_account_session import AccountWebSession
from .flow_ui_session import SessionUnavailable
from .simple_flow import SimpleFlow,MODEL

async def until(predicate):
 for _ in range(250):
  if await predicate():return
  await asyncio.sleep(.05)
 raise AssertionError('Timed out')

async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);vault=Vault(root);ledger=RequestLedger(root);pool=AccountPool(vault,'flow')
  ui=SimpleNamespace(managed_browser=True,verify=AsyncMock(return_value=True))
  accounts=SimpleNamespace(vault=vault,pool=pool,web_ui=ui)
  login=FlowWebLogin(root,accounts);s=SimpleFlow(root,vault,ledger);s.account_bridge=AccountWebSession(root,accounts)
  assert not s.status()['selection']['available']
  # Existing account-tab login registers both identity and owned profile.
  login.profile_key='one';await login.import_account([],{},'one@invalid');a=pool.status()['account_id']
  login.profile_key='two';await login.import_account([],{},'two@invalid');b=pool.status()['account_id']
  assert a!=b and s.status()['selection']['account_id']==b and ui.verify.await_count==2
  assert s.status()['connection_method']=='account_web'
  try:await s.connect({})
  except HTTPException as exc:assert exc.status_code==409
  else:raise AssertionError('A second node login must not exist')
  movie=root/'fixture.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=90x160:d=8','-c:v','libx264','-pix_fmt','yuv420p','-y',str(movie)],check=True)
  video='data:video/mp4;base64,'+base64.b64encode(movie.read_bytes()).decode()
  data=io.BytesIO();Image.new('RGB',(90,160),'green').save(data,format='PNG');image64=base64.b64encode(data.getvalue()).decode()
  html='''<script>window.WIZ_global_data={oPEP7c:'EMAIL'};window.sent=0;</script><form onsubmit="return false"><button type=button>Frames to Video</button><button type=button>Veo Lite · 8s · 9:16 · x1</button><input type=file accept="image/*" onchange="document.querySelector('img').src='data:image/png;base64,IMAGE'"><img><textarea></textarea><button type=button onclick="window.sent++;document.querySelector('#results').innerHTML='<article id=generated><p>Smile and wave.</p><div role=progressbar aria-valuenow=37></div></article>'">Generate</button></form><div id=results></div>'''.replace('IMAGE',image64)
  sessions=[]
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);pages={}
   for key,email in [('one','one@invalid'),('two','two@invalid')]:
    ctx=await browser.new_context(accept_downloads=True)
    await ctx.route('**/*',(lambda address:lambda r:r.fulfill(body=html.replace('EMAIL',address),content_type='text/html; charset=utf-8'))(email))
    page=await ctx.new_page();await page.goto('https://flow.google.com/project/'+key);pages[key]=page
   class Session:
    def __init__(self,data,key):self.key=key;self.page=pages[key];self.email=key+'@invalid';self.detached=False;sessions.append(self)
    async def attach(self,factory):pass
    async def assert_ready(self):
     if self.page.is_closed()or await self.page.evaluate('window.WIZ_global_data.oPEP7c')!=self.email:raise SessionUnavailable('Tài khoản đã đổi; kiểm tra tại tab Tài khoản.')
    async def disconnect(self):self.detached=True
   def body(token):return {'request_id':'flow-'+str(uuid.uuid4()),'kind':'video','model':MODEL,'prompt':'Smile and wave.','references':[{'mime_type':'image/png','data':image64}],'room_id':'room','scene_id':'scene','part':'a','confirm_send':True,'automatic':True,'selection_token':token}
   async def finish(page):
    await page.evaluate('src=>{const a=document.querySelector("#generated");a.querySelector("[role=progressbar]").remove();const v=document.createElement("video");v.src=src;a.append(v);const link=document.createElement("a");link.href=src;link.download="clip.mp4";link.textContent="Download";a.append(link)}',video)
    await asyncio.wait_for(s.task,15)
   with patch('local_engine.flow_account_session.FlowUiSession',Session),patch.object(s,'find_browser',side_effect=AssertionError('No independent browser may launch')):
    pool.select({'mode':'selected','account_id':a});token_a=pool.status()['token'];first=body(token_a)
    await s.submit(first)
    async def generating():return s.lookup(first['request_id']).get('progress')==37
    await until(generating)
    assert sessions[-1].key=='one'and await pages['one'].evaluate('window.sent')==1
    # Switching selection affects NEW jobs; the current job remains pinned to A.
    pool.select({'mode':'selected','account_id':b});assert s.status()['selection']['account_id']==b
    await finish(pages['one']);result=s.lookup(first['request_id'])
    assert result['state']=='done'and result['result']['account_id']==a and result['result']['scene_id']=='scene'
    assert sessions[-1].detached and not pages['one'].is_closed()and await pages['two'].evaluate('window.sent')==0
    try:await s.submit(body(token_a))
    except HTTPException as exc:assert exc.status_code==409
    else:raise AssertionError('Stale account selection sent')
    second=body(pool.status()['token']);await s.submit(second)
    async def generating_b():return s.lookup(second['request_id']).get('progress')==37
    await until(generating_b);assert sessions[-1].key=='two';await finish(pages['two'])
    assert s.lookup(second['request_id'])['result']['account_id']==b
    await s.submit(first);assert await pages['two'].evaluate('window.sent')==1
    # Deleted/expired selection cannot start a new job.
    row=next(x for x in pool.rows()if x['id']==b);row.update(state='expired',session_verified=False);vault.put('accounts',row)
    assert not s.status()['selection']['available']
    try:await s.submit(body(pool.status()['token']))
    except HTTPException:pass
    else:raise AssertionError('Expired selection sent')
    pool.select({'mode':'selected','account_id':a});await pages['one'].evaluate("window.WIZ_global_data.oPEP7c='other@invalid'")
    rejected=body(pool.status()['token']);await s.submit(rejected);await s.task
    assert s.lookup(rejected['request_id'])['state']=='failed'and await pages['one'].evaluate('window.sent')==1
    assert not pages['one'].is_closed()
   await s.close();await browser.close()
 print('PASS v45: existing web-login registry and AccountPool selection drive Veo; selected A/B profiles used without launching a second browser, pinned in-flight identity, new choice for next job, stale/expired/mismatched sessions blocked, correct video/account/scene returned, automation detaches without closing login window. Local browser fixtures and mocked attach/identity registration; no Google calls.')
if __name__=='__main__':asyncio.run(main())
