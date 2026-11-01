"""Upload-only adapter: real file delivery, no prompt, generation or video ledger."""
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
  root=Path(tmp);image=root/'source.png';Image.new('RGB',(90,160),'green').save(image)
  raw=image.read_bytes();ledger=RequestLedger(root);s=SimpleFlow(root,Vault(root),ledger)
  s.account_bridge=SimpleNamespace(selection=lambda:{'available':True,'token':'fixture','account_id':'account'})
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
   await page.set_content('<input type=file accept="image/*" hidden><textarea></textarea><button onclick="window.sent=true">Generate</button>')
   async def restore():s.page=page
   s.restore=restore;s.assert_ready=AsyncMock();s.disconnect_browser=AsyncMock()
   receipt=await s.start_upload_only({'reference':{'mime_type':'image/png','data':base64.b64encode(raw).decode()},'room_id':'room','selection_token':'fixture'})
   await asyncio.wait_for(s.task,15)
   report=s.upload_only_status(receipt['request_id'])
   assert report['state']=='delivered_unverified'and report['delivered']and report['has_preview'],report
   assert await page.locator('input').evaluate('(e)=>e.files.length')==1
   actual=await page.locator('input').evaluate('async e=>Array.from(new Uint8Array(await e.files[0].arrayBuffer()))')
   assert bytes(actual)==raw
   assert await page.locator('textarea').input_value()==''and not await page.evaluate('!!window.sent')
   assert ledger.recent()==[]and s.active is None
   assert (s.root/(receipt['request_id']+'.upload-report.json')).is_file()
   assert not list(s.root.glob('*.png'))==[], 'Screenshot retained'
   from .simple_flow_upload import upload_to_project
   await page.set_viewport_size({'width':1280,'height':720})
   await page.set_content("""<button id=top style='position:absolute;top:20px;left:960px' onclick="document.querySelector('#menu').hidden=false">add</button><button style='position:absolute;top:375px;left:200px' onclick='window.wrong=true'>add</button><div id=menu hidden><button role=menuitem onclick="let f=document.createElement('input');f.type='file';f.accept='image/*';f.hidden=true;document.body.append(f);f.click()">Upload image</button></div><form style='position:absolute;top:520px'><button>Start</button><button>End</button><textarea></textarea><button>Generate</button></form>""")
   report={};assert await upload_to_project(page,image,lambda _:None,report)
   assert len([x for x in report['add_controls']if x['toolbar']])==1
   assert await page.locator('input[type=file]').evaluate('(e)=>e.files.length')==1
   assert not await page.evaluate('!!window.wrong')and await page.locator('textarea').input_value()==''
   await browser.close()
 print('PASS upload-only: exact image bytes delivered using upstream function, no prompt/generation/settings, no video ledger entry, screenshot/report retained; delivery is not claimed as library success.')
if __name__=='__main__':asyncio.run(main())
