"""Local detail-view fixtures, no paid video generation or download."""
import asyncio,json,tempfile
from pathlib import Path
from unittest.mock import AsyncMock
from types import SimpleNamespace
from playwright.async_api import async_playwright
from .flow_video_detail_probe import inspect_video_details
from .flow_tracking_diagnostics import inspect_tracking
from .simple_flow import SimpleFlow
from .request_ledger import RequestLedger
from .vault import Vault

HTML='''<script>window.opened=0;window.reused=0;window.sent=0;window.downloaded=0</script>
<form><textarea></textarea><button onclick="window.sent++" type=button>Generate</button></form>
<flow-grid-tile-container role=group aria-label="Short title…"><flow-tile-container><flow-video-tile><img class=thumbnail width=60 height=90 src="https://example.invalid/thumbnail?token=SENSITIVE" onclick="window.opened++;document.querySelector('#viewer').hidden=false"><button onclick="window.reused++">Reuse prompt</button></flow-video-tile></flow-tile-container></flow-grid-tile-container>
<section id=viewer role=dialog hidden><video width=80 height=120 src="https://example.invalid/movie?token=SENSITIVE"></video><label for=original>Prompt</label><textarea id=original readonly></textarea><button onclick="window.downloaded++">Download</button></section>'''

async def fixture(page,prompt):
 await page.set_content(HTML)
 await page.locator('#original').evaluate('(e,text)=>e.value=text',prompt)

async def main():
 prompt='A person smiles.\nKeep the same outfit.'
 with tempfile.TemporaryDirectory() as folder:
  async with async_playwright() as p:
   browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   page=await browser.new_page();await page.route('**/*',lambda r:r.abort())
   await page.route('https://flow.google.com/**',lambda r:r.fulfill(body=HTML,content_type='text/html'))
   await page.goto('https://flow.google.com/project/fixture')
   await fixture(page,prompt)
   # Reuse a hidden video DOM node that existed BEFORE the thumbnail click.
   report=await inspect_video_details(page,prompt,AsyncMock(),detail_timeout=.3)
   assert report['thumbnail_clicked'] and report['detail_found'] and report['full_prompt_match'],report
   assert not report['request_attribution_confirmed'] and not report['generation_submitted'] and not report['download_started']
   assert await page.evaluate('window.opened')==1
   assert await page.evaluate('window.reused+window.sent+window.downloaded')==0
   assert 'SENSITIVE' not in json.dumps(report)
   assert await page.locator('[data-sf-video-probe],[data-sf-detail-probe]').count()==0
   # More than one visible video tile: never choose the first.
   await fixture(page,prompt)
   await page.locator('flow-grid-tile-container').evaluate('e=>e.after(e.cloneNode(true))')
   report=await inspect_video_details(page,prompt,AsyncMock(),detail_timeout=.1)
   assert not report['thumbnail_clicked'] and await page.evaluate('window.opened')==0
   # A title/body match alone cannot substitute for a labelled prompt field.
   await fixture(page,prompt)
   await page.locator('#original').evaluate("e=>{e.removeAttribute('readonly');e.remove()}")
   await page.locator('#viewer').evaluate('(e,text)=>{const p=document.createElement("p");p.textContent=text;e.append(p)}',prompt)
   report=await inspect_video_details(page,prompt,AsyncMock(),detail_timeout=.2)
   assert report['detail_found'] and not report['full_prompt_match'],report
   # A changed account/session guard before click must stop without clicking.
   await fixture(page,prompt)
   calls=0
   async def check():
    nonlocal calls
    calls+=1
    if calls==2:raise RuntimeError('fixture identity changed')
   report=await inspect_video_details(page,prompt,check,detail_timeout=.1)
   assert not report['thumbnail_clicked'] and await page.evaluate('window.opened')==0
   # Existing visible viewer is left alone.
   await fixture(page,prompt);await page.locator('#viewer').evaluate('e=>e.hidden=false')
   report=await inspect_video_details(page,prompt,AsyncMock(),detail_timeout=.1)
   assert not report['thumbnail_clicked'] and await page.evaluate('window.opened')==0
   # Route integration only opens details on explicit request for an idle unknown.
   await fixture(page,prompt)
   root=Path(folder);service=SimpleFlow(root,Vault(root),RequestLedger(root))
   service.account_bridge=type('Bridge',(),{'background':True,'selection':lambda _:{'available':True,'account_id':'account'},'check':AsyncMock()})()
   service.page=page;service.project='https://flow.google.com/project/fixture';service.connected=True;service.account_session=SimpleNamespace(page=page);service.pinned_binding={'account_id':'account'};service.assert_ready=AsyncMock();service.restore=AsyncMock();service.disconnect_browser=AsyncMock()
   rid='flow-detail-inspection-fixture'
   service.ledger.claim(rid,{'room_id':'room','account_id':'account','scene_id':'scene'})
   service.ledger.set_metadata(rid,{'transport':'simple_flow','prompt':prompt});service.ledger.finish(rid,'unknown')
   body={'store_id':service.ledger.store_id,'room_id':'room','prompt':prompt}
   ordinary=await inspect_tracking(service,rid,body)
   assert 'video_detail_probe' not in ordinary['result_tracking'] and await page.evaluate('window.opened')==0
   expanded=await inspect_tracking(service,rid,dict(body,inspect_video_detail=True))
   probe=expanded['result_tracking']['video_detail_probe']
   assert probe['full_prompt_match'] and not probe['request_attribution_confirmed'],probe
   assert 'media_structure_after_detail' in expanded['result_tracking']
   assert service.lookup(rid)['state']=='unknown' and service.lookup(rid)['result'] is None
   assert expanded['can_retry'] is False and await page.evaluate('window.sent+window.reused+window.downloaded')==0
   await browser.close()
 print('PASS: known Flow thumbnail structure; hidden-video node reuse; labelled full prompt only; ambiguous tiles/existing viewer/account change stop; explicit unknown-detail integration preserves state, no Generate/Reuse/Download clicks.')

if __name__=='__main__':asyncio.run(main())
