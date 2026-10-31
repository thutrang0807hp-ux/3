"""Real existing web-login browser -> CDP attach -> Veo download; all sites intercepted."""
import asyncio,base64,io,os,subprocess,tempfile,uuid
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from playwright.async_api import async_playwright
from .google_login import open_flow_web_login,flow_profile_path,_FLOW_WEB_PROCESSES
from .flow_managed_driver import FlowManagedDriver
from .flow_provider import FlowProvider
from .flow_accounts import FlowAccounts
from .flow_web_login import FlowWebLogin
from .flow_account_session import AccountWebSession
from .simple_flow import SimpleFlow,MODEL
from .vault import Vault
from .request_ledger import RequestLedger

async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);key='b'*24;movie=root/'fixture.mp4'
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=90x160:d=8','-c:v','libx264','-pix_fmt','yuv420p','-y',str(movie)],check=True)
  encoded=base64.b64encode(movie.read_bytes()).decode();image=io.BytesIO();Image.new('RGB',(90,160),'green').save(image,format='PNG');image64=base64.b64encode(image.getvalue()).decode()
  html='''<script>window.WIZ_global_data={oPEP7c:'fixture@invalid'};window.sent=0;</script><form onsubmit="return false"><button type=button>Frames to Video</button><button type=button>Veo Lite · 8s · 9:16 · x1</button><input type=file accept="image/*" onchange="document.querySelector('img').src='data:image/png;base64,IMAGE'"><img><textarea></textarea><button type=button onclick="window.sent++;document.querySelector('#results').innerHTML='<article id=generated><p>Smile and wave.</p><div role=progressbar aria-valuenow=37></div></article>'">Generate</button></form><div id=results></div>'''.replace('IMAGE',image64)
  shim=root/'browser';shim.write_text('#!/bin/sh\nexec /usr/bin/chromium --headless=new --no-sandbox --host-resolver-rules="MAP * ~NOTFOUND" "$@"\n');shim.chmod(0o700)
  before=list(_FLOW_WEB_PROCESSES)
  with patch.dict(os.environ,{'SCENEFORGE_BROWSER':str(shim)}):await open_flow_web_login(root,auto_connect=True,profile_key=key)
  spawned=[p for p in _FLOW_WEB_PROCESSES if p not in before]
  try:
   portfile=flow_profile_path(root,key)/'DevToolsActivePort'
   for _ in range(100):
    if portfile.exists():break
    await asyncio.sleep(.1)
   async with async_playwright()as pw:
    browser=await pw.chromium.connect_over_cdp('http://127.0.0.1:'+portfile.read_text().splitlines()[0]);ctx=browser.contexts[0]
    await ctx.route('**/*',lambda r:r.fulfill(status=200,content_type='text/html; charset=utf-8',body=html))
    page=ctx.pages[0];await page.goto('https://flow.google.com/project/fixture')
    vault=Vault(root);ledger=RequestLedger(root);provider=FlowProvider(vault,root,ledger);accounts=FlowAccounts(provider);provider.account_service=accounts
    managed=FlowManagedDriver(root,vault);accounts.web_ui=managed
    login=FlowWebLogin(root,accounts);login.profile_key=key;await login.import_account([],{},'fixture@invalid')
    assert login.status()['state']=='done',login.status()
    s=SimpleFlow(root,vault,ledger);s.account_bridge=AccountWebSession(root,accounts);provider.simple=s
    body={'request_id':'flow-'+str(uuid.uuid4()),'kind':'video','model':MODEL,'prompt':'Smile and wave.','references':[{'mime_type':'image/png','data':image64}],'room_id':'room','scene_id':'scene','part':'a','confirm_send':True,'automatic':True,'selection_token':accounts.pool.status()['token']}
    with patch.object(s,'find_browser',side_effect=AssertionError('No independent browser/profile allowed')):
     await s.submit(body)
     for _ in range(200):
      record=s.lookup(body['request_id'])
      if record.get('progress')==37:break
      if s.task.done():raise AssertionError(record)
      await asyncio.sleep(.05)
     assert record['progress']==37 and await page.evaluate('window.sent')==1,record
     await page.evaluate('src=>{const a=document.querySelector("#generated");a.querySelector("[role=progressbar]").remove();const v=document.createElement("video");v.src=src;a.append(v);const link=document.createElement("a");link.href=src;link.download="clip.mp4";link.textContent="Download";a.append(link)}','data:video/mp4;base64,'+encoded)
     await asyncio.wait_for(s.task,25)
     result=s.lookup(body['request_id']);assert result['state']=='done',result
     assert result['result']['account_id']==accounts.pool.status()['account_id']and (s.root/result['result']['file']).read_bytes()==movie.read_bytes()
     await s.close();await managed.close()
     assert browser.is_connected()and not page.is_closed()and all(p.poll()is None for p in spawned)
     assert len([p for p in _FLOW_WEB_PROCESSES if p not in before])==1
    for process in spawned:
     process.terminate();await asyncio.to_thread(process.wait,timeout=5)
    # Closing the shared login window never causes an independent browser launch.
    expired={**body,'request_id':'flow-'+str(uuid.uuid4())}
    await s.submit(expired);await asyncio.wait_for(s.task,15)
    assert s.lookup(expired['request_id'])['state']=='failed'and not ledger.metadata(expired['request_id'])['clicked']
    assert len([p for p in _FLOW_WEB_PROCESSES if p not in before])==1
  finally:
   for process in spawned:
    if process.poll()is None:process.terminate()
 print('PASS v45 actual CDP: original web-login browser/profile registered in Accounts, new Veo worker attaches to that exact browser, real 37% and validated 8s download, zero secondary browser launches, cleanup leaves login window alive. All pages intercepted/DNS blocked; not Google or Windows verification.')
if __name__=='__main__':asyncio.run(main())
