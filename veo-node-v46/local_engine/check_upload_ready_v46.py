"""Do not confuse old, wrong, loading, ambiguous or dialog images with a completed new asset."""
import asyncio,tempfile
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright
from .simple_flow_upload import library_images,wait_uploaded_image

async def main():
 with tempfile.TemporaryDirectory()as tmp:
  ref=Path(tmp)/'reference.png';Image.new('RGB',(90,160),'green').save(ref)
  other=Path(tmp)/'other.png';Image.new('RGB',(90,160),'red').save(other)
  async def check():pass
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
   await page.route('https://media.fixture/**',lambda r:r.fulfill(body=(other if '/wrong' in r.request.url else ref).read_bytes(),content_type='image/png'))
   for case in ['old','wrong','busy','ambiguous','dialog','duplicate','url_refresh']:
    await page.set_content('<div data-media-id=old><img src=https://media.fixture/old.png></div>')
    before=await library_images(page)
    if case=='url_refresh':
     await page.set_content('<div><img src=https://media.fixture/same.png?token=old></div>')
     before=await library_images(page)
     await page.locator('img').evaluate('(e)=>e.src="https://media.fixture/same.png?token=new"')
    elif case!='old':
     html='<article data-media-id=new '+('aria-busy=true'if case=='busy'else'')+'><img src=https://media.fixture/'+('wrong'if case=='wrong'else'new')+'.png></article>'
     if case=='ambiguous':html+='<article data-media-id=new2><img src=https://media.fixture/new2.png></article>'
     if case=='dialog':html='<div role=dialog>'+html+'</div>'
     if case=='duplicate':html+='<article data-media-id=new><img src=https://media.fixture/new.png></article>'
     await page.evaluate('(html)=>document.body.insertAdjacentHTML("beforeend",html)',html)
    report={};asset=await wait_uploaded_image(page,before,ref,check,report,timeout=1.5)
    if case=='duplicate':assert asset and asset['media_id']=='new',report
    else:assert asset is None,(case,asset)
   # Return identity of the new image, never an index or the first/last tile.
   await page.set_content('<article data-media-id=old><img src=https://media.fixture/old.png></article>')
   before=await library_images(page)
   await page.evaluate('()=>document.body.insertAdjacentHTML("afterbegin",\'<article data-media-id=uploaded><img src=https://media.fixture/uploaded.png></article>\')')
   asset=await wait_uploaded_image(page,before,ref,check,{},timeout=2)
   assert asset and asset['media_id']=='uploaded'
   await browser.close()
 print('PASS upload completion: new matching loaded library asset only; old identical, wrong, busy, ambiguous and dialog images rejected; duplicate views deduplicated by asset identity.')
if __name__=='__main__':asyncio.run(main())
