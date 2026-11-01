"""End-to-end upload-ready -> correct Ingredients attachment -> prompt, before Generate."""
import asyncio,base64,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from PIL import Image
from playwright.async_api import async_playwright
from .simple_flow import SimpleFlow
from .vault import Vault
from .request_ledger import RequestLedger

async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);image=root/'input.png';Image.new('RGB',(90,160),'green').save(image);raw=image.read_bytes()
  ledger=RequestLedger(root);service=SimpleFlow(root,Vault(root),ledger)
  service.account_bridge=SimpleNamespace(selection=lambda:{'available':True,'token':'fixture','account_id':'account'})
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
   await page.route('https://media.fixture/**',lambda r:r.fulfill(body=raw,content_type='image/png'))
   await page.set_content('''<script>window.sent=0;window.chosen='';</script><article data-media-id=old oncontextmenu="window.chosen='old'"><img src=https://media.fixture/old.png></article>
   <input type=file accept="image/*" hidden onchange="const card=document.createElement('article');card.dataset.mediaId='new';card.innerHTML='<img src=https://media.fixture/new.png>';card.oncontextmenu=e=>{e.preventDefault();window.chosen='new';document.querySelector('#actions').hidden=false};document.body.append(card)">
   <form onsubmit="return false"><button type=button>Ingredients</button><div id=refs></div><textarea></textarea><button type=button onclick="window.sent++">Generate</button></form>
   <div id=actions role=menu hidden><button role=menuitem onclick="document.querySelector('#refs').innerHTML='<img src=https://media.fixture/new.png>';document.querySelector('#actions').hidden=true">Add to prompt</button></div>''')
   await page.wait_for_function('Array.from(document.images).every(e=>e.complete)')
   async def restore():service.page=page
   service.restore=restore;service.assert_ready=AsyncMock();service.disconnect_browser=AsyncMock()
   await service.start_upload_only({'reference':{'mime_type':'image/png','data':base64.b64encode(raw).decode()},'room_id':'room','scene_id':'scene-2','part':'b','selection_token':'fixture','prepare_prompt':True,'prompt':'Move slowly with the new image.'})
   await asyncio.wait_for(service.task,15)
   report=service.upload_report
   assert report['state']=='prompt_ready'and report['preparation_stage']=='prompt_ready',report
   assert report['uploaded_asset']['media_id']=='new'and report['attached_asset_key']==report['uploaded_asset']['key']
   assert report['scene_id']=='scene-2'and report['part']=='b'
   assert await page.locator('textarea').input_value()=='Move slowly with the new image.'
   assert await page.evaluate('window.chosen')=='new'and await page.evaluate('window.sent')==0
   assert ledger.recent()==[]and report['has_preview']
   assert 'Move slowly'not in (service.root/(report['request_id']+'.upload-report.json')).read_text()
   await browser.close()
 print('PASS complete preparation worker: exact new upload/scene/part -> Ingredients attachment -> prompt; old identical image not selected, no generation or video receipt, report contains prompt hash only.')
if __name__=='__main__':asyncio.run(main())
