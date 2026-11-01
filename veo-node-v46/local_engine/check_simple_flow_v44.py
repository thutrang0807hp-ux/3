"""Intercepted browser: saved session, automatic send, real progress and download."""
import asyncio,base64,io,json,tempfile,subprocess,uuid
from pathlib import Path
from unittest.mock import AsyncMock,patch
from PIL import Image
from playwright.async_api import async_playwright
from .simple_flow import SimpleFlow,MODEL
from .simple_flow_dom import ResultObserver,settings_ready,prepare_settings
from .vault import Vault
from .request_ledger import RequestLedger

async def until(predicate,timeout=12):
 end=asyncio.get_running_loop().time()+timeout
 while asyncio.get_running_loop().time()<end:
  if await predicate():return
  await asyncio.sleep(.05)
 raise AssertionError('Condition timed out')

async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);vault=Vault(root);ledger=RequestLedger(root);s=SimpleFlow(root,vault,ledger)
  movie=root/'fixture.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=90x160:d=8','-c:v','libx264','-pix_fmt','yuv420p','-y',str(movie)],check=True)
  video='data:video/mp4;base64,'+base64.b64encode(movie.read_bytes()).decode()
  image=io.BytesIO();Image.new('RGB',(90,160),'green').save(image,format='PNG');img='data:image/png;base64,'+base64.b64encode(image.getvalue()).decode()
  html='''<script>window.WIZ_global_data={oPEP7c:'fixture@invalid'};window.sent=0;</script>
  <article id="old">Smile and wave.<video src="OLD"></video><span>90%</span></article>
  <form onsubmit="return false"><button type=button>Ingredients to Video</button><button type=button>Veo 3.1 Lite · 8s · 9:16 · x1</button>
  <input type=file accept="image/*" onchange="document.querySelector('#preview').src='IMAGE'"><img id=preview>
  <textarea></textarea><button type=button onclick="window.sent++;document.querySelector('#results').innerHTML='<article id=new><p>Smile and wave.</p><div role=progressbar aria-valuenow=37></div></article>'">Generate</button></form><div id=results></div>'''.replace('IMAGE',img).replace('OLD',video)
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=await browser.new_context(accept_downloads=True)
   await ctx.route('**/*',lambda r:r.fulfill(body=html,content_type='text/html; charset=utf-8'))
   page=await ctx.new_page();await page.goto('https://flow.google.com/project/fixture')
   s.context=ctx;s.page=page;s.email='fixture@invalid';s.connected=True;s.project=s.project_url();s.save_binding()
   assert await settings_ready(page)
   # The tab's Connect button must reuse the current session, not launch a second login.
   with patch.object(s,'login',new_callable=AsyncMock)as login:
    await s.connect({'browser':'msedge'});login.assert_not_awaited();assert s.page is page
   restored=SimpleFlow(root,vault,ledger);assert restored.status()['restorable']and not restored.status()['selection']['available']and restored.token==s.token
   assert restored.account_id()==s.account_id()
   body={'request_id':'flow-'+str(uuid.uuid4()),'kind':'video','model':MODEL,'prompt':'Smile and wave.','references':[{'mime_type':'image/png','data':base64.b64encode(image.getvalue()).decode()}],'room_id':'room','scene_id':'scene','part':'a','confirm_send':True,'automatic':True,'selection_token':s.token}
   await s.submit(body)
   async def progress():return s.lookup(body['request_id']).get('progress')==37
   await until(progress)
   assert s.pending is None and await page.evaluate('window.sent')==1
   record=s.lookup(body['request_id']);assert record['progress_source']=='flow_ui'and record['phase']=='generating',record
   await s.submit(body);assert await page.evaluate('window.sent')==1
   await page.evaluate('src=>{const a=document.querySelector("#new");a.querySelector("[role=progressbar]").remove();const v=document.createElement("video");v.src=src;a.append(v);const link=document.createElement("a");link.download="clip.mp4";link.href=src;link.textContent="Download";a.append(link)}',video)
   await asyncio.wait_for(s.task,15)
   result=s.lookup(body['request_id']);assert result['state']=='done',result
   assert result['result']['scene_id']=='scene'and result['result']['part']=='a'and s.pending is None
   assert (s.root/result['result']['file']).read_bytes()==movie.read_bytes()
   # A historical card that receives an ID late is still historical.
   await page.set_content('<article>Smile and wave.<div role=progressbar aria-valuenow=90></div></article>')
   observer=ResultObserver(page,'Smile and wave.');await observer.baseline()
   await page.locator('article').evaluate('(e)=>e.id="late-id"');assert await observer.read()is None
   # Two matching new results never select whichever happens to come first.
   await page.evaluate('()=>document.body.insertAdjacentHTML("beforeend",\'<article id=a>Smile and wave.<progress role=progressbar></progress></article><article id=b>Smile and wave.<progress role=progressbar></progress></article>\')')
   assert await observer.read()is None and observer.ambiguous
   await page.locator('#b').evaluate('(e)=>e.remove()');assert await observer.read()is None
   # Missing progress stays indeterminate; no fabricated percent.
   observer=ResultObserver(page,'Different prompt.');await observer.baseline()
   await page.evaluate('()=>document.body.insertAdjacentHTML("beforeend",\'<article id=c>Different prompt. Generating</article>\')')
   row=await observer.read();assert row and row['progress']is None
   # Plain div result cards without server IDs get a local stable identity.
   observer=ResultObserver(page,'Plain card prompt.');await observer.baseline()
   await page.evaluate("""()=>document.body.insertAdjacentHTML('beforeend','<div><p>Plain card prompt.</p><div role=progressbar aria-valuenow=57></div></div>')""")
   row=await observer.read();assert row and row['progress']==57 and row['attr']=='data-sceneforge-result-id',(row,await page.content(),observer.before,observer.ambiguous)
   # A percentage written in the prompt is not generation progress.
   observer=ResultObserver(page,'Show 100% cotton.');await observer.baseline()
   await page.evaluate("""()=>document.body.insertAdjacentHTML('beforeend','<article id=percent-prompt><p>Show 100% cotton.</p><p>Generating</p></article>')""")
   row=await observer.read();assert row and row['progress']is None
   # Settings must use selected values, not an unselected Lite option.
   await page.set_content('<form><textarea></textarea><select><option selected>Veo Quality</option><option>Veo Lite 8s 9:16 x1 Ingredients to Video</option></select><button>Generate</button></form>')
   assert not await settings_ready(page)
   # Button popovers can set Ingredients mode without pressing Generate.
   await page.set_content("""<form onsubmit='return false'><textarea></textarea><button type=button id=mode onclick="document.querySelector('#menu').hidden=false">Text to Video</button><button type=button>Veo Lite · 8s · 9:16 · x1</button><button type=button onclick="window.badSend=true">Generate</button></form><div id=menu hidden><div role=option onclick="document.querySelector('#mode').textContent='Ingredients to Video';document.querySelector('#menu').hidden=true">Ingredients to Video</div></div>""")
   assert await prepare_settings(page)and not await page.evaluate('!!window.badSend')
   # Unknown settings/image proof leads to ONE review step, then no extra project/image/submit prompts.
   await page.goto('https://flow.google.com/project/fixture');s.page=page
   await page.locator('form button').nth(1).evaluate('(e)=>e.textContent="Unknown settings"')
   fallback={**body,'request_id':'flow-'+str(uuid.uuid4())};await s.submit(fallback)
   async def review():return bool(s.pending and s.pending['kind']=='review')
   await until(review);assert await page.evaluate('window.sent')==0
   await s.respond({'id':s.pending['id'],'accept':True})
   await until(lambda:page.evaluate('window.sent===1'))
   await s.stop();assert s.lookup(fallback['request_id'])['state']=='unknown'
   # Restore reopens only the saved project; identity changes stop before sending.
   await s.disconnect_browser()
   import types,sys
   page=types.SimpleNamespace(url='https://flow.google.com/project/fixture',goto=AsyncMock(),evaluate=AsyncMock(return_value='fixture@invalid'),is_closed=lambda:False)
   context=types.SimpleNamespace(pages=[page],close=AsyncMock())
   client=types.SimpleNamespace(chromium=types.SimpleNamespace(launch_persistent_context=AsyncMock(return_value=context)),stop=AsyncMock())
   module=types.ModuleType('playwright.async_api');module.async_playwright=lambda:types.SimpleNamespace(start=AsyncMock(return_value=client))
   with patch.dict(sys.modules,{'playwright.async_api':module}),patch.object(restored,'find_browser',return_value=Path('/fixture/browser')):
    await restored.restore();page.goto.assert_awaited_once_with('https://flow.google.com/project/fixture',wait_until='domcontentloaded',timeout=60000)
    assert restored.connected and restored.token==s.token;await restored.disconnect_browser()
    page.evaluate.return_value='other@invalid'
    await restored.reconnect();assert not restored.connected and restored.state=='failed'
   await browser.close()
 print('PASS v44: shared/reused/saved account binding, no-click session restore, automatic image+prompt+single send, actual 37% scoped to new result, automatic validated download to exact scene/part; old/ambiguous results excluded, unknown progress indeterminate, settings selected values only, one fallback review, identity change stops. Fixtures/mocks only, no Google calls.')
if __name__=='__main__':asyncio.run(main())
