"""Chromium fixture + ledger checks; this does not exercise Google generation."""
import asyncio,base64,hashlib,io,tempfile
from pathlib import Path
from unittest.mock import AsyncMock
from PIL import Image
from fastapi import FastAPI
from playwright.async_api import async_playwright
from .flow_prepare import prepare_composer,PrepareStopped,register_prepare_routes,validate_prepared
from .flow_settings import DEFAULTS
from .simple_flow import SimpleFlow,SimpleStopped,MODEL
from .vault import Vault
from .request_ledger import RequestLedger

SETTINGS='''<button aria-label="Settings trigger" onclick="document.querySelector('#settings').hidden=false">Video · 8s</button><section id=settings hidden><div><button aria-pressed=false>Hình ảnh</button><button aria-pressed=true>Video</button></div><div><button aria-pressed=false>Khung hình</button><button aria-pressed=true>Thành phần</button></div><div><button aria-pressed=false>16:9</button><button aria-pressed=true>9:16</button></div><button aria-haspopup=listbox>Veo 3.1 - Lite</button><div><button aria-pressed=true>x1</button><button aria-pressed=false>x2</button><button aria-pressed=false>x3</button><button aria-pressed=false>x4</button></div></section>'''

def fixture(image,other,duplicate=False):
 library='<article><img width=90 height=160 src="'+image+'"><button type=button aria-label="More options" onclick="window.opened++;document.querySelector(\'#menu\').hidden=false">more_vert</button></article>'
 return SETTINGS+library+(library if duplicate else '')+'<article><img width=90 height=160 src="'+other+'"><button aria-label="More options" onclick="window.wrong=true">more_vert</button></article>'+'''<div id=menu hidden><button role=menuitem onclick="document.querySelector('#attached').innerHTML='<img width=90 height=160 src=IMAGE>';document.querySelector('#menu').hidden=true">Add to prompt</button><button role=menuitem onclick="window.wrong=true">Animate</button></div><form onsubmit="return false"><div id=attached></div><textarea></textarea><button type=button onclick="window.sent++">Generate</button></form><script>window.sent=0;window.opened=0;document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelector('#settings').hidden=true});for(const b of document.querySelectorAll('[aria-pressed]'))b.onclick=()=>{for(const other of b.parentElement.children)other.setAttribute('aria-pressed','false');b.setAttribute('aria-pressed','true')}</script>'''.replace('IMAGE',image)

async def main():
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);reference=root/'source.png';image=Image.new('RGB',(90,160));image.putdata([((x*3)%256,(y*2)%256,(x+y)%256) for y in range(160) for x in range(90)]);image.save(reference)
  raw=reference.read_bytes();url='data:image/png;base64,'+base64.b64encode(raw).decode();other=io.BytesIO();Image.new('RGB',(90,160),'blue').save(other,format='PNG');otherurl='data:image/png;base64,'+base64.b64encode(other.getvalue()).decode();prompt='A person waves.\nKeep the same outfit.'
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
   await page.set_content(fixture(url,otherurl));await page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
   report={};await prepare_composer(page,reference,prompt,DEFAULTS,AsyncMock(),report)
   assert report['phase']=='ready_for_review' and report['reference_sha256']==hashlib.sha256(raw).hexdigest(),report
   assert await page.locator('textarea').input_value()==prompt and await page.evaluate('sent')==0
   assert await page.evaluate('opened')==1 and not await page.evaluate('!!window.wrong')
   await prepare_composer(page,reference,prompt,DEFAULTS,AsyncMock(),{})
   assert await page.evaluate('opened')==1
   await page.set_content(fixture(url,otherurl,True));await page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
   try:await prepare_composer(page,reference,prompt,DEFAULTS,AsyncMock(),{});raise AssertionError('Duplicate selected')
   except PrepareStopped:pass
   assert await page.evaluate('opened')==0 and await page.evaluate('sent')==0
   await page.set_content(fixture(url,otherurl));await page.locator('textarea').fill('Existing work')
   try:await prepare_composer(page,reference,prompt,DEFAULTS,AsyncMock(),{});raise AssertionError('Prompt overwritten')
   except PrepareStopped:pass
   assert await page.locator('textarea').input_value()=='Existing work'
   await page.set_content(fixture(url,otherurl));ledger=RequestLedger(root);s=SimpleFlow(root,Vault(root),ledger)
   s.account_bridge=type('Bridge',(),{'background':True,'selection':lambda _:{'available':True,'token':'fixture','account_id':'account'}})()
   s.connected=True;s.page=page;s.pinned_room='room';s.pinned_account='account';s.assert_ready=AsyncMock();s.disconnect_browser=AsyncMock()
   upload_ref=s.root/'flow-upload-fixture.png';upload_ref.write_bytes(raw);s.upload_report={'delivered':True,'request_id':'flow-upload-fixture','reference_sha256':hashlib.sha256(raw).hexdigest()}
   app=FastAPI();register_prepare_routes(app,s);routes={r.path:r.endpoint for r in app.routes if hasattr(r,'endpoint')}
   receipt=await routes['/local-api/flow/simple/prepare']({'settings':DEFAULTS,'prompt':prompt,'reference_sha256':hashlib.sha256(raw).hexdigest(),'room_id':'room','scene_id':'scene','part':'part','selection_token':'fixture'})
   await s.task;prepared=await routes['/local-api/flow/simple/prepare/{rid}'](receipt['request_id']);assert prepared['state']=='ready',prepared
   assert prepared['has_preview'] and '_prompt' not in prepared
   payload={'prepared_request_id':prepared['request_id'],'room_id':'room','scene_id':'scene','part':'part','account_id':'account','prompt':prompt}
   await validate_prepared(s,payload,raw)
   try:await validate_prepared(s,dict(payload,scene_id='other-scene'),raw);raise AssertionError('Other scene accepted')
   except PrepareStopped:pass
   try:await validate_prepared(s,payload,b'changed image');raise AssertionError('Changed image accepted')
   except PrepareStopped:pass
   await page.locator('textarea').fill('Changed after preparation')
   try:await validate_prepared(s,payload,raw);raise AssertionError('Changed prompt accepted')
   except PrepareStopped:pass
   await page.locator('textarea').fill(prompt)
   s.wait_result=AsyncMock(side_effect=SimpleStopped('Fixture stops after submit; no live generation'))
   body={'request_id':'flow-fixture-submit-once','kind':'video','model':MODEL,'prompt':prompt,'references':[{'mime_type':'image/png','data':base64.b64encode(raw).decode()}],'room_id':'room','scene_id':'scene','part':'part','confirm_send':True,'automatic':True,'selection_token':'fixture','prepared_request_id':prepared['request_id']}
   await s.submit(body);await s.task
   assert await page.evaluate('sent')==1
   assert s.lookup(body['request_id'])['state']=='unknown'
   again=await s.submit(body);assert again['state']=='unknown' and await page.evaluate('sent')==1
   await browser.close()
 print('PASS prepare: unique matching image, Add to prompt, exact prompt, duplicate rejection, existing prompt preserved, ready receipt/screenshot, changed input rejected; real ledger clicks Generate once and never retries unknown. No Google generation tested.')

if __name__=='__main__':asyncio.run(main())
