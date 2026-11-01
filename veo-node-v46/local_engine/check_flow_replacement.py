"""Explicitly replace one unverified attachment with the current scene image."""
import asyncio,base64,hashlib,io,tempfile
from pathlib import Path
from unittest.mock import AsyncMock,patch
from PIL import Image
from fastapi import FastAPI,HTTPException
from playwright.async_api import async_playwright
from .check_flow_prepare import fixture
from .flow_prepare import register_prepare_routes
from .flow_settings import DEFAULTS
from .simple_flow import SimpleFlow
from .vault import Vault
from .request_ledger import RequestLedger

def png(color):
 b=io.BytesIO();Image.new('RGB',(90,160),color).save(b,format='PNG');return b.getvalue()
def data(raw):return 'data:image/png;base64,'+base64.b64encode(raw).decode()

async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);raw=png('green');new=data(raw);old=data(png('blue'));red=data(png('red'))
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
   chip='<div id=old-chip style="width:70px;height:70px"><img width=50 height=50 src="'+old+'"><button type=button aria-label="Remove image" onclick="window.removed++;document.querySelector(\'#attached\').innerHTML=\'\'"><i>close</i></button></div>'
   html=fixture(new,red).replace('<div id=attached></div>','<div id=attached>'+chip+'</div>').replace('window.sent=0;','window.sent=0;window.removed=0;')
   await page.set_content(html);await page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
   selection={'available':True,'account_id':'account','token':'fixture'}
   s=SimpleFlow(root,Vault(root),RequestLedger(root));s.account_bridge=type('Bridge',(),{'selection':lambda _:dict(selection)})();s.connected=True;s.page=page;s.pinned_room='room';s.pinned_account='account';s.assert_ready=AsyncMock()
   source=s.root/'flow-upload-replace.png';source.write_bytes(raw);s.upload_report={'delivered':True,'request_id':'flow-upload-replace','reference_sha256':hashlib.sha256(raw).hexdigest()}
   app=FastAPI();register_prepare_routes(app,s);routes={r.path:r.endpoint for r in app.routes if hasattr(r,'endpoint')};start=routes['/local-api/flow/simple/prepare'];status=routes['/local-api/flow/simple/prepare/{rid}']
   body={'room_id':'room','scene_id':'scene','part':'a','prompt':'Wave once.','reference_sha256':hashlib.sha256(raw).hexdigest(),'settings':DEFAULTS,'selection_token':'fixture'}
   entered=asyncio.Event();release=asyncio.Event();capture=page.screenshot
   async def slow_capture(**kwargs):
    entered.set();await release.wait();return await capture(**kwargs)
   with patch.object(page,'screenshot',side_effect=slow_capture):
    receipt=await start(body);await asyncio.wait_for(entered.wait(),10)
    interim=await status(receipt['request_id']);assert interim['state']=='running',interim
    release.set();await s.task
   report=await status(receipt['request_id']);assert report['state']=='awaiting_replacement',report
   assert report['has_attachment_preview'] and report['has_source_preview']
   preview=await routes['/local-api/flow/simple/prepare/{rid}/attached-image'](report['request_id']);assert Path(preview.path).read_bytes().startswith(b'\x89PNG')
   preview=await routes['/local-api/flow/simple/prepare/{rid}/source-image'](report['request_id']);assert Path(preview.path).read_bytes()==raw
   assert await page.evaluate('removed')==0 and await page.evaluate('sent')==0 and await page.locator('textarea').input_value()==''
   consent={'request_id':report['request_id'],'approval_token':report['replacement']['approval_token']}
   for invalid in [dict(body,replace_attachment=dict(consent,approval_token='wrong')),dict(body,prompt='Changed prompt',replace_attachment=consent),dict(body,scene_id='other-scene',replace_attachment=consent)]:
    try:await start(invalid);raise AssertionError('Invalid approval accepted')
    except HTTPException as error:assert error.status_code==409
   # An image changed after preview must never be removed using stale approval.
   await page.locator('#attached img').evaluate('(e,url)=>e.src=url',red)
   second=await start(dict(body,replace_attachment=consent));await s.task;stale=await status(second['request_id']);assert stale['state']=='failed',stale
   assert await page.evaluate('removed')==0
   # Obtain a new preview and approve exactly that attachment.
   third=await start(body);await s.task;report=await status(third['request_id']);assert report['state']=='awaiting_replacement',report
   consent={'request_id':report['request_id'],'approval_token':report['replacement']['approval_token']}
   fourth=await start(dict(body,replace_attachment=consent));await s.task;ready=await status(fourth['request_id']);assert ready['state']=='ready',ready
   assert ready['removed_attachment'] and await page.evaluate('removed')==1
   assert await page.locator('textarea').input_value()=='Wave once.' and await page.evaluate('sent')==0
   assert await page.locator('article img').count()==2 # Library was not deleted.
   try:await start(dict(body,replace_attachment=consent));raise AssertionError('Approval reused')
   except HTTPException as error:assert error.status_code==409
   assert await page.evaluate('removed')==1
   await browser.close()
 print('PASS replacement: two previews; no change before approval; forged/stale scene/prompt approvals rejected; changed thumbnail preserved; approved chip removed once; correct scene image attached and prompt filled; library intact; Generate untouched.')

if __name__=='__main__':asyncio.run(main())
