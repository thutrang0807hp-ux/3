"""Real-ledger acknowledgement tests: unlock NEW IDs, never mark old video received."""
import asyncio,base64,io,tempfile,time
from pathlib import Path
from unittest.mock import AsyncMock,patch
from fastapi import HTTPException
from PIL import Image
from .simple_flow import SimpleFlow,MODEL
from .request_ledger import RequestLedger
from .vault import Vault
from .flow_saved_video_review import acknowledge_saved_video

async def main():
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);ledger=RequestLedger(root);vault=Vault(root);service=SimpleFlow(root,vault,ledger)
  selection={'available':True,'account_id':'account','token':'token'}
  bridge=type('Bridge',(),{'background':True,'selection':lambda _:selection})()
  service.account_bridge=bridge
  ids=['flow-acknowledge-old-one','flow-acknowledge-old-two']
  for rid in ids:
   ledger.claim(rid,{'room_id':'room','scene_id':'scene','account_id':'account'})
   ledger.set_metadata(rid,{'transport':'simple_flow','phase':'waiting'})
   ledger.finish(rid,'unknown')
   with ledger.connect() as db:db.execute('UPDATE request SET updated=? WHERE id=?',(time.time()-181,rid))
  assert all(item['needs_manual_review'] for item in service.unresolved())
  assert service.lookup(ids[0])['needs_manual_review']
  assert len(service.unresolved())==2  # Age alone never unlocks.
  body={'store_id':ledger.store_id,'room_id':'room','confirm_saved_video':True,'allow_new_generation':True}
  for changed in (dict(body,confirm_saved_video=False),dict(body,allow_new_generation=False),dict(body,store_id='wrong'),dict(body,room_id='other')):
   try:await acknowledge_saved_video(service,ids[0],changed);raise AssertionError('Invalid confirmation accepted')
   except HTTPException:pass
  selection['account_id']='other'
  try:await acknowledge_saved_video(service,ids[0],body);raise AssertionError('Wrong account accepted')
  except HTTPException:pass
  selection['account_id']='account'
  receipt=await acknowledge_saved_video(service,ids[0],body)
  assert receipt['state']=='unknown' and receipt['result'] is None and receipt['submitted'] is None
  assert receipt['saved_video_review']['allow_new_generation'] and not receipt['saved_video_review']['old_request_retry_allowed']
  assert not receipt['needs_manual_review'] and not receipt['automatic_retry']
  assert [row['id'] for row in service.unresolved()]==[ids[1]]
  await acknowledge_saved_video(service,ids[0],body)
  assert len(ledger.metadata(ids[0])['review_events'])==1
  await acknowledge_saved_video(service,ids[1],body)
  assert not service.unresolved()
  # Reopening app must retain acknowledgements without changing old request states.
  reopened=SimpleFlow(root,vault,RequestLedger(root));reopened.account_bridge=bridge
  assert not reopened.unresolved() and len(reopened.saved_video_reviews())==2
  assert all(reopened.lookup(rid)['state']=='unknown' for rid in ids)
  # With fresh verified inputs, a NEW ID may be admitted; an old ID cannot be retried.
  buffer=io.BytesIO();Image.new('RGB',(2,2)).save(buffer,format='PNG')
  reopened.pair_trial_only=True;reopened.pair_report={'request_id':'flow-pair-fresh'};reopened.run=AsyncMock()
  request={'request_id':'flow-fresh-after-saved-review','kind':'video','model':MODEL,'prompt':'New scene prompt',
   'references':[{'mime_type':'image/png','data':base64.b64encode(buffer.getvalue()).decode()}],
   'room_id':'room','scene_id':'scene','part':'a','selection_token':'token','prepared_request_id':'flow-pair-fresh','confirm_send':True}
  with patch('local_engine.flow_prepare.validate_prepared',AsyncMock()):
   await reopened.submit(request);await reopened.task
   try:await reopened.submit(dict(request,request_id=ids[0]));raise AssertionError('Old request reused')
   except HTTPException:pass
  reopened.run.assert_awaited_once()
  assert ledger.metadata(ids[0])['saved_video_review']['status']=='user_kept_video'
 print('PASS: timeout only flags review; explicit store/room/account-bound acknowledgement persists; old unknown/result unchanged, idempotent log, new ID admitted only after input validation, old ID never retried.')

if __name__=='__main__':asyncio.run(main())
