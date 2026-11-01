"""Local Chromium fixture only; no live Google Flow or video generation."""
import asyncio,tempfile
from pathlib import Path
from unittest.mock import AsyncMock,patch
from types import SimpleNamespace
from .flow_pair_trial import run_pair
from playwright.async_api import async_playwright
from .flow_composer_upload import upload_into_composer_and_fill

HTML='''<button onclick="window.wrong++" aria-label="Add media menu">+</button>
<div id=menu hidden><button onclick="document.querySelector('#file').click()">Upload media</button></div>
<input id=file type=file hidden accept="image/*" onchange="window.files=this.files.length;document.querySelector('#chips').innerHTML='<img width=40 height=40 src=broken>';document.querySelector('#menu').hidden=true">
<form onsubmit="return false"><div id=chips></div><textarea></textarea><button type=button aria-label="Add ingredients to the prompt box" onclick="document.querySelector('#menu').hidden=false">+</button><button type=button onclick="window.sent++">Generate</button></form><script>window.sent=0;window.wrong=0;window.files=0</script>'''

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=await browser.new_page()
  with tempfile.TemporaryDirectory() as folder:
   image=Path(folder)/'reference.png';image.write_bytes(b'filechooser fixture')
   await page.set_content(HTML)
   report=await upload_into_composer_and_fill(page,image,'Scene prompt',AsyncMock())
   assert report['delivered'] and report['image_attached'] and report['prompt_verified'],report
   assert await page.evaluate('window.files')==1
   assert await page.evaluate('window.wrong')==0 and await page.evaluate('window.sent')==0
   assert await page.locator('textarea').input_value()=='Scene prompt'
   assert not report['generation_submitted']
   await page.set_content(HTML)
   await page.locator('#chips').evaluate("e=>e.innerHTML='<img width=40 height=40 src=old>'")
   report=await upload_into_composer_and_fill(page,image,'Second prompt',AsyncMock())
   assert not report['delivered'] and not report['image_attached'] and report['prompt_verified'],report
   assert await page.evaluate('window.files')==0 and await page.evaluate('window.sent')==0
   # Exercise the actual orchestrator, not just the upload helper.
   await page.set_content(HTML)
   selection={'available':True,'account_id':'account','token':'token'}
   service=SimpleNamespace(root=Path(folder),page=page,
       account_bridge=SimpleNamespace(selection=lambda:selection),
       assert_ready=AsyncMock(),disconnect_browser=AsyncMock(),restore=AsyncMock(),active='trial')
   report={'request_id':'flow-pair-orchestrator','account_id':'account'}
   with patch('local_engine.flow_pair_trial.apply_settings',AsyncMock(return_value=True)):
    await run_pair(service,report,b'fixture','image/png','Orchestrated prompt',{},'token')
   assert report['state']=='inputs_sent',report
   assert report['delivered'] and report['prompt_verified'] and report['image_attached'],report
   assert not report['errors'] and service.active is None,report
   assert await page.evaluate('window.sent')==0 and await page.evaluate('window.wrong')==0
   assert (Path(folder)/'flow-pair-orchestrator.pair.json').is_file()
  await browser.close()
 print('PASS Chromium: composer-only +, real filechooser delivery once, chip without decoded preview, prompt readback, no Generate; existing chip preserved; actual run_pair passes settings-to-upload transition without TypeError.')

if __name__=='__main__':asyncio.run(main())
