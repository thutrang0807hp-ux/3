"""Local Chromium fixture only; no live Google Flow or video generation."""
import asyncio,tempfile
from pathlib import Path
from unittest.mock import AsyncMock,patch
from types import SimpleNamespace
from .flow_pair_trial import run_pair
from .add_to_prompt import click_add_to_prompt,wait_for_composer_attachment
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
   # Flow variant: upload opens a confirmation instead of attaching immediately.
   await page.set_content(HTML)
   await page.evaluate("""() => {
    const dialog=document.createElement('div');dialog.setAttribute('role','dialog');dialog.hidden=true;
    dialog.innerHTML='<img width=50 height=50 src=uploaded><button>Thêm vào câu lệnh</button>';
    dialog.querySelector('button').onclick=()=>{window.confirmed=(window.confirmed||0)+1;document.querySelector('#chips').innerHTML='<img width=40 height=40 src=attached>';dialog.hidden=true};
    document.body.append(dialog);
    document.querySelector('#file').onchange=()=>{window.files++;document.querySelector('#menu').hidden=true;dialog.hidden=false};
   }""")
   report=await upload_into_composer_and_fill(page,image,'Confirm prompt',AsyncMock())
   assert report['add_to_prompt_clicked'] and report['image_attached'] and report['prompt_verified'],report
   assert await page.evaluate('window.confirmed')==1 and await page.evaluate('window.sent')==0
   # No role=dialog: a positioned one-image detail with a close control.
   await page.set_content(HTML)
   await page.evaluate("""() => {
    const detail=document.createElement('section');detail.style.position='fixed';detail.hidden=true;
    detail.innerHTML='<button aria-label="Close">×</button><img width=50 height=50 src=uploaded><button>Add to prompt</button>';
    detail.querySelectorAll('button')[1].onclick=()=>{window.confirmed=1;document.querySelector('#chips').innerHTML='<img width=40 height=40 src=attached>';detail.hidden=true};
    document.body.append(detail);
    document.querySelector('#file').onchange=()=>{window.files++;document.querySelector('#menu').hidden=true;detail.hidden=false};
   }""")
   report=await upload_into_composer_and_fill(page,image,'No dialog prompt',AsyncMock())
   assert report['add_to_prompt_clicked'] and report['image_attached'] and report['prompt_verified'],report
   assert report['qualified_detail_region_count']==1 and await page.evaluate('window.sent')==0
   # A normal library card with one image/action has no detail boundary.
   await page.set_content('<article><img width=50 height=50 src=a><button onclick="window.wrong=1">Add to prompt</button></article>')
   assert not await click_add_to_prompt(page,lambda x:None,AsyncMock(),{})
   assert not await page.evaluate('!!window.wrong')
   # Two valid detail regions are ambiguous: neither can be clicked.
   await page.set_content('<section style="position:fixed"><button aria-label="Close">×</button><img width=40 height=40 src=a><button>Add to prompt</button></section><section style="position:absolute"><button aria-label="Close">×</button><img width=40 height=40 src=b><button>Add to prompt</button></section>')
   assert not await click_add_to_prompt(page,lambda x:None,AsyncMock(),{})
   # Clicking alone is not evidence: no chip must reach timeout.
   await page.set_content('<form><textarea></textarea><button>Generate</button></form>')
   try:
    await asyncio.wait_for(wait_for_composer_attachment(page,AsyncMock()),.05)
    raise AssertionError('Missing chip reported as attached')
   except asyncio.TimeoutError:pass
   # Ambiguous resource picker and unrelated global buttons are never clicked.
   await page.set_content('<div role=dialog><img src=a><img src=b><button onclick="window.wrong=1">Add to prompt</button></div><button onclick="window.wrong=1">Add to prompt</button>')
   assert not await click_add_to_prompt(page,lambda x:None,AsyncMock(),{})
   assert not await page.evaluate('!!window.wrong')
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
