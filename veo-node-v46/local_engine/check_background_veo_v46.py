"""Actual headless profile -> room project -> one generation -> validated file. Fixtures only."""
import asyncio,base64,io,tempfile,subprocess,time,uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image
from playwright.async_api import async_playwright
from .vault import Vault
from .account_pool import AccountPool
from .request_ledger import RequestLedger
from .flow_account_session import AccountWebSession
from .google_login import flow_profile_path
from .simple_flow import SimpleFlow,MODEL

async def until(fn,timeout=20):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if fn():return
  await asyncio.sleep(.05)
 raise AssertionError('Timeout')
async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);vault=Vault(root);ledger=RequestLedger(root);pool=AccountPool(vault,'flow');key='d'*24;aid='flow-web-fixture'
  vault.put('accounts',{'id':aid,'service':'flow','name':'Fixture','enabled':True,'session_verified':True,'state':'ready','active':False,'priority':0,'login_transport':'web_ui'})
  vault.set_secret('flow-managed-profiles',{aid:{'account_id':aid,'email':'fixture@invalid','profile_key':key}});pool.select({'mode':'selected','account_id':aid})
  s=SimpleFlow(root,vault,ledger);s.account_bridge=AccountWebSession(root,SimpleNamespace(vault=vault,pool=pool),background=True)
  movie=root/'clip.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=green:s=90x160:d=8','-c:v','libx264','-pix_fmt','yuv420p','-y',str(movie)],check=True)
  image=io.BytesIO();Image.new('RGB',(90,160),'blue').save(image,format='PNG');image64=base64.b64encode(image.getvalue()).decode();video='data:video/mp4;base64,'+base64.b64encode(movie.read_bytes()).decode()
  form='''<form onsubmit="return false"><button type=button>Ingredients to Video</button><button id=model type=button>Veo Lite · 8s · 9:16 · x1</button><input type=file accept="image/*" onchange="document.querySelector('img').src='data:image/png;base64,IMAGE'"><img><textarea oninput="if(!document.querySelector('img').complete||document.querySelector('img').naturalWidth===0||document.querySelector('[role=progressbar]'))window.earlyPrompt=true"></textarea><button id=generate type=button onclick="window.sent++;document.querySelector('#results').innerHTML='<article id=clip><p>Smile and wave.</p><div role=progressbar aria-valuenow=37></div></article>'">Generate</button></form><div id=results></div>'''.replace('IMAGE',image64)
  contexts=[];pages=[];state={'kind':'normal'};created=[];profile=flow_profile_path(root,key)
  async with async_playwright()as pw:
   ctx=await pw.chromium.launch_persistent_context(str(profile),executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
   await ctx.add_cookies([{'name':'fixture_session','value':'saved','domain':'flow.google.com','path':'/','secure':True,'expires':time.time()+3600}]);await ctx.close()
  async def launch(pw,path):
   assert Path(path)==profile
   ctx=await pw.chromium.launch_persistent_context(str(path),executable_path='/usr/bin/chromium',headless=True,accept_downloads=True,args=['--no-sandbox','--disable-gpu','--host-resolver-rules=MAP * ~NOTFOUND'])
   contexts.append(ctx)
   async def route(r):
    if r.request.url.startswith('https://storage.googleapis.com/'):
     assert not r.request.headers.get('cookie');return await r.fulfill(content_type='video/mp4',headers={'Access-Control-Allow-Origin':'*'},body=movie.read_bytes())
    assert 'fixture_session=saved'in r.request.headers.get('cookie','')
    if '/fixture-video/'in r.request.url:return await r.fulfill(content_type='video/mp4',headers={'Content-Disposition':'attachment; filename=clip.mp4'},body=movie.read_bytes())
    email='other@invalid'if state['kind']=='wrong'else'fixture@invalid'
    html="<script>window.WIZ_global_data={oPEP7c:'"+email+"'};window.sent=0;</script>"
    if '/project/'in r.request.url:
     if state['kind']=='loading':html+='<p>Loading...</p><script>setTimeout(()=>{document.body.innerHTML='+__import__('json').dumps(form)+'},1200)</script>'
     else:html+=form
    else:
     from html import escape
     html+='<button id=new type=button>New project</button><script>document.querySelector("#new").onclick=()=>{history.pushState({},"","/project/fixture-project");document.body.innerHTML='+__import__('json').dumps('<p>Loading...</p>')+';setTimeout(()=>{document.body.innerHTML='+__import__('json').dumps(form)+'},1200);fetch("/fixture-created")}</script>'
    if '/fixture-created'in r.request.url:created.append(True);return await r.fulfill(body='ok')
    await r.fulfill(content_type='text/html; charset=utf-8',body=html)
   await ctx.route('**/*',route)
   page=ctx.pages[0];pages.append(page)
   cdp=await ctx.new_cdp_session(page);info=await cdp.send('Browser.getVersion');assert 'HeadlessChrome'in info['userAgent'];await cdp.detach()
   if state['kind']=='upload-failed':await page.add_init_script("document.addEventListener('DOMContentLoaded',()=>{document.querySelector('input')?.removeAttribute('onchange')})")
   if state['kind']=='upload-delayed':await page.add_init_script("document.addEventListener('DOMContentLoaded',()=>{const input=document.querySelector('input');if(input)input.onchange=()=>{const bar=document.createElement('div');bar.setAttribute('role','progressbar');input.after(bar);setTimeout(()=>{document.querySelector('img').src='data:image/png;base64,"+image64+"';bar.remove()},700)}})")
   if state['kind']=='unsafe':await page.add_init_script("document.addEventListener('DOMContentLoaded',()=>{document.querySelector('#model')?.remove()})")
   return ctx
  def body():return {'request_id':'flow-'+str(uuid.uuid4()),'kind':'video','model':MODEL,'prompt':'Smile and wave.','references':[{'mime_type':'image/png','data':image64}],'room_id':'room','scene_id':'scene','part':'a','confirm_send':True,'automatic':True,'selection_token':pool.status()['token']}
  with patch('local_engine.flow_background_session.launch_background',launch),patch('local_engine.flow_browser_probe.probe_flow_browser',side_effect=AssertionError('Must not depend on visible/CDP endpoint')):
   for i in range(2):
    state['kind']='loading'if i==0 else'upload-delayed'
    b=body();await s.submit(b);await until(lambda:s.lookup(b['request_id']).get('progress')==37)
    page=pages[-1];assert await page.evaluate('window.sent')==1 and s.pending is None
    assert not await page.evaluate('!!window.earlyPrompt'), 'Prompt filled before image attached'
    if i==0:
     await s.account_session.save_media('https://storage.googleapis.com/fixture/media.mp4',root/'cors.partial')
     assert(root/'cors.partial').read_bytes()==movie.read_bytes();(root/'cors.partial').unlink()
     from .flow_ui_session import SessionUnavailable
     try:await s.account_session.save_media('https://untrusted.invalid/video.mp4',root/'unsafe.partial')
     except SessionUnavailable:pass
     else:raise AssertionError('Foreign result URL accepted')
     blob=await page.evaluate('()=>URL.createObjectURL(new Blob([new Uint8Array(100)],{type:"video/mp4"}))')
     try:await s.account_session.save_media(blob,root/'limited.partial',limit=4)
     except Exception:pass
     else:raise AssertionError('Oversized media accepted')
     assert not(root/'limited.partial').exists()

    await page.evaluate('encoded=>{const bytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));const src=URL.createObjectURL(new Blob([bytes],{type:"video/mp4"}));const a=document.querySelector("#clip");a.querySelector("[role=progressbar]").remove();const v=document.createElement("video");v.preload="none";v.src=src;a.append(v);const link=document.createElement("a");link.textContent="Download";link.download="clip.mp4";link.href=src;a.append(link)}',base64.b64encode(movie.read_bytes()).decode())
    await asyncio.wait_for(s.task,40);r=s.lookup(b['request_id']);assert r['state']=='done',r
    assert r['result']['account_id']==aid and r['result']['room_id']=='room'and (s.root/r['result']['file']).read_bytes()==movie.read_bytes()
    assert page.is_closed()and s.account_session is None
    await s.submit(b);assert s.lookup(b['request_id'])['state']=='done'
   assert len(created)==1,'Same account/room must reuse one saved project'
   state['kind']='unsafe';b=body();await s.submit(b);await asyncio.wait_for(s.task,40);r=s.lookup(b['request_id'])
   assert r['state']=='failed'and r['has_preview']and not ledger.metadata(b['request_id'])['clicked'],r
   assert (s.root/(b['request_id']+'.preview.png')).is_file()and s.pending is None
   state['kind']='upload-failed';b=body();await s.submit(b);await asyncio.wait_for(s.task,40);r=s.lookup(b['request_id'])
   assert r['state']=='failed'and r['has_preview']and s.pending is None,r
   assert not ledger.metadata(b['request_id'])['clicked']and 'thủ công'not in r['message']and 'Chưa điền prompt'in r['message'],r
   state['kind']='wrong';b=body();await s.submit(b);await asyncio.wait_for(s.task,40)
   assert s.lookup(b['request_id'])['state']=='failed'and not ledger.metadata(b['request_id'])['clicked']
   await s.close()
  # Visible but unselected settings are never accepted as the current mode.
  from .simple_flow_dom import settings_ready,prepare_settings
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=await browser.new_page()
   await page.set_content("""<form><textarea></textarea><button type=button>Veo Lite · 8s · 9:16 · x1</button><button type=button id=text role=tab aria-selected=true>Text to Video</button><button type=button role=tab aria-selected=false onclick="this.setAttribute('aria-selected','true');document.querySelector('#text').setAttribute('aria-selected','false')">Ingredients to Video</button><button type=button>Generate</button></form>""")
   assert not await settings_ready(page)
   assert await prepare_settings(page)and await settings_ready(page)
   await browser.close()
 print('PASS v46 actual headless worker: saved-profile auth, no CDP endpoint or visible window, creates/reuses dedicated room project, exact image+prompt, one click, real 37%, verified 8s download/account/scene, profile released each time, unsafe UI fails before sending with local screenshot and no manual web checkpoint, wrong identity stops. All pages intercepted, no Google requests.')
if __name__=='__main__':asyncio.run(main())
