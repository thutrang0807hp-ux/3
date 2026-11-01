"""Chromium regression cases for project uploads; no Google account required."""
import asyncio, importlib.util, tempfile
from pathlib import Path
from playwright.async_api import async_playwright
spec=importlib.util.spec_from_file_location('upload',Path(__file__).parents[1]/'local_engine/simple_flow_upload.py')
upload=importlib.util.module_from_spec(spec);spec.loader.exec_module(upload)

async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  with tempfile.TemporaryDirectory() as tmp:
   image=Path(tmp)/'reference.png';image.write_bytes(b'test reference')
   async def run(name,body,expected=True):
    page=await browser.new_page(viewport={'width':1280,'height':720})
    await page.set_content('''<style>#add{position:absolute;top:18px;left:950px}#composer{position:absolute;top:640px}</style>
    <button id=add aria-label="Add media menu" onclick="opens++;openMenu()">add</button>
    <div id=composer><textarea></textarea><button aria-label="Add ingredients to the prompt box" onclick="wrong++">add</button></div>
    <script>let opens=0,wrong=0,received=0;function recordFile(e){if(e.target.files.length)received++}</script>'''+body)
    report={};logs=[];result=await upload.upload_to_project(page,image,logs.append,report)
    assert result is expected,(name,report,logs)
    assert await page.evaluate('wrong')==0,(name,'composer clicked')
    if expected:
     assert await page.evaluate('received')==1,(name,'file not delivered once',report)
     assert report['phase']=='file_delivered'
    else:
     assert report['failed_phase']=='find_upload_menu_item',report
     assert report.get('visible_upload_controls'),report
    assert await page.evaluate('opens') <= 1
    await page.close();print('PASS',name)
   await run('existing image input','<input type=file accept="image/*" onchange="recordFile(event)"><script>function openMenu(){throw Error("should not open")}</script>')
   await run('portal menu with icon and native chooser','''<script>function openMenu(){setTimeout(()=>{let m=document.createElement('div');m.setAttribute('role','menuitem');m.innerHTML='<i>upload</i> Upload';m.onclick=()=>{let f=document.createElement('input');f.type='file';f.onchange=recordFile;f.click()};document.body.append(m)},300)}</script>''')
   await run('plain Upload text and lazy file input','''<script>function openMenu(){let m=document.createElement('div');m.textContent='Upload';m.onclick=()=>{let f=document.createElement('input');f.type='file';f.accept='image/*';f.onchange=recordFile;document.body.append(f)};document.body.append(m)}</script>''')
   await run('ambiguous Upload does not click either','''<script>function openMenu(){for(let i=0;i<2;i++){let b=document.createElement('button');b.textContent='Upload';document.body.append(b)}}</script>''',False)
  await browser.close()
asyncio.run(main())
