"""Local Chromium fixture only; no live Google Flow or video generation."""
import asyncio,tempfile
from pathlib import Path
from unittest.mock import AsyncMock
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
  await browser.close()
 print('PASS Chromium: composer-only +, real filechooser delivery once, chip without decoded preview, prompt readback, no Generate; existing chip preserved and prompt still handled.')

if __name__=='__main__':asyncio.run(main())
