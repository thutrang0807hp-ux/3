"""Read-only tracking diagnostics against Chromium + a real request ledger."""
import asyncio,json,tempfile
from pathlib import Path
from unittest.mock import AsyncMock
from playwright.async_api import async_playwright
from fastapi import HTTPException
from .simple_flow import SimpleFlow
from .simple_flow_dom import ResultObserver
from .flow_tracking_diagnostics import observer_report,inspect_tracking
from .request_ledger import RequestLedger
from .vault import Vault

async def main():
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);service=SimpleFlow(root,Vault(root),RequestLedger(root))
  selection={'available':True,'account_id':'account','token':'token'}
  service.account_bridge=type('Bridge',(),{'background':True,'selection':lambda _:selection})()
  service.assert_ready=AsyncMock();service.disconnect_browser=AsyncMock()
  rid='flow-tracking-fixture-unknown';prompt='A person waves slowly and smiles at the camera. Keep the same outfit.'
  service.ledger.claim(rid,{'room_id':'room','scene_id':'scene','account_id':'account','kind':'video'})
  service.ledger.set_metadata(rid,{'transport':'simple_flow','phase':'waiting','prompt':prompt,'part':'a'})
  service.ledger.finish(rid,'unknown')
  async with async_playwright() as p:
   browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   page=await browser.new_page();service.page=page
   await page.route('**/*',lambda r:r.abort())
   await page.set_content('<form><textarea></textarea><button type=button onclick="window.sent++">Generate</button></form><article data-generation-id="old"><p>Old video</p><video width=80 height=100 src="https://example.invalid/media.mp4?token=SENSITIVE"></video></article><script>window.sent=0</script>')
   observer=ResultObserver(page,prompt);await observer.baseline()
   await page.evaluate('''()=>{const card=document.createElement('article');card.setAttribute('data-generation-id','new');card.innerHTML='<p>A person waves slowly and smiles at the camera.</p><div role=progressbar aria-valuenow=72></div>';document.body.append(card)}''')
   snapshot=await observer_report(observer)
   old=next(c for c in snapshot['cards'] if c['value']=='old')
   new=next(c for c in snapshot['cards'] if c['value']=='new')
   assert 'existed_before_submit' in old['rejected_because']
   assert 'full_prompt_not_in_card' in new['rejected_because'] and new['prefix_match']
   assert new['progress']==72
   assert 'SENSITIVE' not in json.dumps(snapshot)
   body={'store_id':service.ledger.store_id,'room_id':'room','prompt':prompt}
   blocker=asyncio.Event();service.task=asyncio.create_task(blocker.wait());service.active=rid;service.observer=observer
   report=await inspect_tracking(service,rid,body)
   assert report['result_tracking']['session_source']=='active_generation'
   assert service.lookup(rid)['state']=='unknown' and report['can_retry'] is False
   service.task.cancel();await asyncio.gather(service.task,return_exceptions=True)
   service.active=None;service.observer=None
   async def restore():await page.evaluate('window.__sfFlowOldCards=null')
   service.restore=AsyncMock(side_effect=restore)
   report=await inspect_tracking(service,rid,body)
   assert report['result_tracking']['session_source']=='reopened_for_read_only_inspection'
   assert not report['result_tracking']['baseline_available']
   assert all('baseline_unavailable' in c['rejected_because'] for c in report['result_tracking']['cards'])
   assert service.lookup(rid)['state']=='unknown' and service.lookup(rid)['result'] is None
   assert await page.evaluate('window.sent')==0
   assert service.unresolved()[0]['id']==rid
   for changed in (dict(body,room_id='other'),dict(body,store_id='other')):
    try:await inspect_tracking(service,rid,changed);raise AssertionError('Wrong binding accepted')
    except HTTPException as e:assert e.status_code==409
   fallback=await inspect_tracking(service,rid,dict(body,prompt=''))
   assert fallback['result_tracking']['expected_prompt_length']==len(' '.join(prompt.split()))
   unknown=service.unresolved()[0]
   assert unknown['room_id']=='room' and unknown['account_id']=='account' and unknown['part']=='a'
   selection['account_id']='other'
   try:await inspect_tracking(service,rid,body);raise AssertionError('Wrong account accepted')
   except HTTPException as e:assert e.status_code==409
   await browser.close()
 print('PASS: records truncated-prompt/old-card rejection and actual 72%; active and reopened inspection preserve unknown/no retry, never click Generate, omit signed media URLs, reject wrong store/room/account.')

if __name__=='__main__':asyncio.run(main())
