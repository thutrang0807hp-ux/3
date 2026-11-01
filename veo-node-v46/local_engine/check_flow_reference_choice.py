"""Two matching media IDs: explicit choice, revalidation and remembered binding."""
import asyncio,base64,hashlib,io,tempfile
from pathlib import Path
from unittest.mock import AsyncMock
from fastapi import FastAPI,HTTPException
from PIL import Image
from playwright.async_api import async_playwright
from .check_flow_prepare import fixture
from .flow_prepare import register_prepare_routes
from .flow_settings import DEFAULTS
from .simple_flow import SimpleFlow
from .vault import Vault
from .request_ledger import RequestLedger

async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);buf=io.BytesIO();image=Image.new('RGB',(90,160));image.putdata([((x*3)%256,(y*2)%256,(x+y)%256)for y in range(160)for x in range(90)]);image.save(buf,format='PNG');raw=buf.getvalue();url='data:image/png;base64,'+base64.b64encode(raw).decode();other=io.BytesIO();Image.new('RGB',(90,160),'blue').save(other,format='PNG');otherurl='data:image/png;base64,'+base64.b64encode(other.getvalue()).decode()
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
   html=fixture(url,otherurl,True).replace('window.opened++;','window.selectedMedia=this.closest(\'article\').dataset.mediaId;window.opened++;')
   await page.set_content(html);await page.locator('article').nth(0).evaluate("e=>e.dataset.mediaId='media-one'");await page.locator('article').nth(1).evaluate("e=>e.dataset.mediaId='media-two'");await page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
   service=SimpleFlow(root,Vault(root),RequestLedger(root));service.account_bridge=type('Bridge',(),{'selection':lambda _:{'available':True,'account_id':'account','token':'fixture'}})();service.connected=True;service.page=page;service.pinned_room='room';service.pinned_account='account';service.assert_ready=AsyncMock()
   source=service.root/'flow-upload-choice.png';source.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest();service.upload_report={'delivered':True,'request_id':'flow-upload-choice','reference_sha256':digest}
   app=FastAPI();register_prepare_routes(app,service);routes={r.path:r.endpoint for r in app.routes if hasattr(r,'endpoint')};start=routes['/local-api/flow/simple/prepare'];status=routes['/local-api/flow/simple/prepare/{rid}'];preview=routes['/local-api/flow/simple/prepare/{rid}/candidates/{candidate_id}']
   body={'room_id':'room','scene_id':'scene','part':'a','reference_sha256':digest,'prompt':'Wave once and smile.','settings':DEFAULTS,'selection_token':'fixture'}
   first=await start(body);await service.task;report=await status(first['request_id']);assert report['state']=='awaiting_selection',report
   assert len(report['candidates'])==2 and all(c['has_preview']for c in report['candidates'])
   assert await page.evaluate('opened')==0 and await page.evaluate('sent')==0 and await page.locator('textarea').input_value()==''
   candidate=next(c for c in report['candidates']if c['media_id']=='media-two');response=await preview(report['request_id'],candidate['id']);assert Path(response.path).read_bytes().startswith(b'\x89PNG')
   choice={'request_id':report['request_id'],'candidate_id':candidate['id']}
   for changed in [dict(body,candidate_choice={'request_id':report['request_id'],'candidate_id':'forged'}),dict(body,prompt='Different prompt',candidate_choice=choice),dict(body,scene_id='other-scene',candidate_choice=choice)]:
    try:await start(changed);raise AssertionError('Stale/forged choice accepted')
    except HTTPException as e:assert e.status_code==409
   # Reordering the grid must not turn the second media ID into the first tile.
   await page.locator('article').nth(1).evaluate('e=>e.parentElement.prepend(e)')
   receipt=await start(dict(body,candidate_choice=choice));await service.task;ready=await status(receipt['request_id']);assert ready['state']=='ready',ready
   assert ready['matched_reference']['media_id']=='media-two' and await page.evaluate('selectedMedia')=='media-two'
   assert await page.locator('textarea').input_value()==body['prompt'] and await page.evaluate('sent')==0
   # The same source uses its verified binding on the next preparation in this session.
   await page.locator('#attached').evaluate('e=>e.innerHTML=""');await page.locator('textarea').fill('')
   third=await start(body);await service.task;remembered=await status(third['request_id']);assert remembered['state']=='ready' and remembered['matched_reference']['media_id']=='media-two',remembered
   assert await page.evaluate('sent')==0
   await browser.close()
 print('PASS duplicate reference choice: two media IDs shown with PNG previews; no menu/prompt/Generate before choice; stale/forged choices rejected; selected second ID revalidated and attached; prompt correct; binding reused without upload or generation.')

if __name__=='__main__':asyncio.run(main())
