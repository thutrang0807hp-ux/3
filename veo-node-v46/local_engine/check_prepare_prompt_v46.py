"""Real Chromium: bind the exact new library image to Ingredients before prompt; never Generate."""
import asyncio,tempfile
from pathlib import Path
from PIL import Image
from .simple_flow_upload import library_images,prepare_uploaded_prompt
from playwright.async_api import async_playwright

async def main():
 with tempfile.TemporaryDirectory()as tmp:
  reference=Path(tmp)/'reference.png';Image.new('RGB',(90,160),'green').save(reference)
  wrong=Path(tmp)/'wrong.png';Image.new('RGB',(90,160),'red').save(wrong)
  async def check():pass
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
   await page.route('https://media.fixture/**',lambda r:r.fulfill(body=(wrong if '/wrong' in r.request.url else reference).read_bytes(),content_type='image/png'))
   html='''<script>window.sent=0;window.chosen='';window.early=false;</script>
   <article data-media-id=old oncontextmenu="event.preventDefault();window.chosen='old'"><img src=https://media.fixture/old.png></article>
   <article data-media-id=new oncontextmenu="event.preventDefault();window.chosen='new';document.querySelector('#actions').hidden=false"><img src=https://media.fixture/new.png></article>
   <form onsubmit="return false"><button type=button id=mode onclick="document.querySelector('#modes').hidden=false">Video · 720p · 8s · x2</button><div id=refs></div><textarea oninput="window.early=!document.querySelector('#refs img')?.complete"></textarea><button type=button onclick="window.sent++">Generate</button></form>
   <div id=modes role=menu hidden><button role=option onclick="document.querySelector('#mode').textContent='Ingredients';document.querySelector('#modes').hidden=true">Ingredients</button></div>
   <div role=menu id=actions hidden><button role=menuitem onclick="document.querySelector('#refs').innerHTML='<img src=https://media.fixture/new.png>';document.querySelector('#actions').hidden=true">Add to prompt</button></div>'''
   for case in ['success','overlay','plain_label','wrong_attached','old_reference','old_prompt','missing_asset','unknown_action']:
    await page.set_content(html)
    await page.wait_for_function('Array.from(document.images).every(e=>e.complete)')
    asset=next(x for x in await library_images(page)if x['id']=='new')
    if case=='overlay':
     await page.evaluate("""()=>{const overlay=document.createElement('div');overlay.id='upload-overlay';overlay.style='position:fixed;inset:0;z-index:99999';document.body.append(overlay);document.addEventListener('keydown',e=>{if(e.key==='Escape'){overlay.remove();const b=document.querySelector('#mode');b.outerHTML=b.outerHTML}},{once:true})}""")
    if case=='plain_label':await page.locator('#mode').evaluate("e=>e.outerHTML='<span id=mode>Ingredients</span>'")
    if case=='wrong_attached':await page.locator('#actions button').evaluate("e=>e.onclick=()=>{document.querySelector('#refs').innerHTML='<img src=https://media.fixture/wrong.png>';document.querySelector('#actions').hidden=true}")
    if case=='old_reference':await page.locator('#refs').evaluate("e=>e.innerHTML='<img src=https://media.fixture/old.png>'")
    if case=='old_prompt':await page.locator('textarea').fill('Existing user text')
    if case=='missing_asset':asset['key']='does-not-exist'
    if case=='unknown_action':await page.locator('#actions button').evaluate("e=>e.textContent='Generate now'")
    report={};ok=await prepare_uploaded_prompt(page,asset,reference,'Prompt for this new image',check,report,timeout=.7)
    assert await page.evaluate('window.sent')==0,(case,report)
    if case in ('success','overlay','plain_label'):
     assert ok and report['attached_asset_key']==asset['key'],report
     assert await page.evaluate('window.chosen')=='new'and not await page.evaluate('window.early')
     assert await page.locator('textarea').input_value()=='Prompt for this new image'
    else:
     assert not ok,(case,report)
     assert await page.locator('textarea').input_value()==('Existing user text'if case=='old_prompt'else''),(case,report)
     assert await page.evaluate('window.chosen')!='old'
   await browser.close()
 print('PASS Ingredients preparation: exact new asset selected among old identical image; prompt only after matching attachment; wrong/missing asset, existing refs/text and unsafe actions stop; Generate never clicked.')
if __name__=='__main__':asyncio.run(main())
