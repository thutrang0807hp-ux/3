"""Real Chromium reference-upload regressions; no external requests."""
import asyncio,base64,tempfile
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright
from .simple_flow_upload import upload_reference
from .simple_flow_dom import previews,uploaded_preview,prepare_settings,settings_ready,wait_composer

async def main():
 with tempfile.TemporaryDirectory() as tmp:
  reference=Path(tmp)/'reference.png'
  Image.new('RGB',(90,160),'blue').save(reference)
  src='data:image/png;base64,'+base64.b64encode(reference.read_bytes()).decode()
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   page=await browser.new_page()
   await page.route('**/*',lambda r:r.abort())
   async def check():pass
   await page.set_content('<p>Loading...</p>')
   assert not await wait_composer(page,check,timeout=.3)
   assert await page.locator('textarea').count()==0
   await page.evaluate("""()=>setTimeout(()=>document.body.innerHTML='<form><textarea></textarea><button disabled>Generate</button></form>',400)""")
   assert await wait_composer(page,check,timeout=2)
   # An unrelated input outside the composer must never receive the reference.
   base='''<input id=unrelated type=file accept="video/*"><form onsubmit="return false"><button type=button>Ingredients</button><button type=button>Veo Lite · 8s · 9:16 · x1</button><textarea></textarea><img id=preview>CONTENT<button type=button>Generate</button></form>'''
   changed="document.querySelector('#preview').src='"+src+"'"
   for kind in ['direct','lazy','chooser']:
    if kind=='direct':content='<input id=upload type=file accept="image/*" onchange="'+changed+'">'
    elif kind=='lazy':content='''<button type=button onclick="document.querySelector('#picker').hidden=false">Add reference</button><div role=dialog id=picker hidden><input id=upload type=file accept="image/*" onchange="'''+changed+''';document.querySelector('#picker').hidden=true"></div>'''
    else:content='''<button type=button onclick="const input=document.createElement('input');input.type='file';input.accept='image/*';input.onchange=()=>{'''+changed+'''};input.click()">Add reference</button>'''
    await page.set_content(base.replace('CONTENT',content))
    assert await prepare_settings(page)and await settings_ready(page)
    before=await previews(page)
    assert await upload_reference(page,reference,lambda _:None),kind
    assert await uploaded_preview(page,before),kind
    assert await page.locator('#unrelated').evaluate('(e)=>e.files.length')==0
    assert await page.locator('textarea').input_value()==''
   # Flow-style non-form composer: nested prompt row, icon-only add button,
   # and a hidden image input mounted outside the composer by the menu action.
   await page.set_content("""<input id=unrelated type=file accept="video/*"><div id=composer><button>Ingredients</button><img id=preview><div><textarea></textarea><button id=add type=button>add_2</button></div><button disabled>Generate</button></div>""")
   await page.locator('#add').evaluate("""(e,src)=>e.onclick=()=>{const input=document.createElement('input');input.type='file';input.accept='image/*';input.id='portal';input.hidden=true;input.onchange=()=>document.querySelector('#preview').src=src;document.body.append(input)}""",src)
   before=await previews(page)
   assert await upload_reference(page,reference,lambda _:None)
   assert await page.locator('#portal').evaluate('(e)=>e.files.length')==1
   assert await page.locator('#unrelated').evaluate('(e)=>e.files.length')==0
   assert await uploaded_preview(page,before)
   # Exact rtrtr4 regression: a pre-existing hidden image input is global,
   # outside the composer; it must work without opening + or confirmation.
   await page.set_content('<input type=file accept="video/*"><input id=global-upload type=file accept="image/*" hidden><form><textarea></textarea><img id=preview><button disabled>Generate</button></form>')
   await page.locator('#global-upload').evaluate('(e,src)=>e.onchange=()=>document.querySelector("#preview").src=src',src)
   before=await previews(page)
   assert await upload_reference(page,reference,lambda _:None)
   assert await uploaded_preview(page,before)
   await page.set_content('<input type=file accept="image/*"><input type=file accept="image/*">')
   assert not await upload_reference(page,reference,lambda _:None)
   assert await page.locator('input').evaluate_all('(xs)=>xs.reduce((n,e)=>n+e.files.length,0)')==0
   # File delivery, a library thumbnail, stale images and busy/error UI are not attachment proof.
   await page.set_content(base.replace('CONTENT','<input type=file accept="image/*">')+'<div role=dialog><img src="'+src+'"></div>')
   assert not await uploaded_preview(page,[],timeout=.3)
   await page.locator('[role=dialog]').evaluate('(e)=>e.remove()')
   await page.locator('#preview').evaluate('(e,src)=>e.src=src',src)
   await page.wait_for_function("document.querySelector('#preview').naturalWidth>32")
   assert not await uploaded_preview(page,await previews(page),timeout=.3)
   for blocked in ['<div role=progressbar>Uploading</div>','<div aria-busy=true>Uploading</div>','<div role=alert>Upload failed</div>']:
    await page.locator('form').evaluate('(e,html)=>e.insertAdjacentHTML("beforeend",html)',blocked)
    assert not await uploaded_preview(page,[],timeout=.3)
    await page.locator('form > div').evaluate('(e)=>e.remove()')
   # Keep Ingredients selected even when a Frames tab is available.
   await page.locator('form').evaluate('(e)=>e.insertAdjacentHTML("beforeend",`<button type=button role=tab aria-selected=false onclick="window.framesClicked=true">Frames</button>`)')
   assert await prepare_settings(page)and not await page.evaluate('!!window.framesClicked')
   await browser.close()
 print('PASS v46 upload: direct/lazy-dialog/native chooser, scoped file input, Ingredients preserved; stale/library/busy/error previews rejected.')

if __name__=='__main__':asyncio.run(main())
