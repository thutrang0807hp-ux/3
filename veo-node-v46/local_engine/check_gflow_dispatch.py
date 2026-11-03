"""Real SimpleFlow submit/run/ledger, fixture engine only; no Google calls.
Run with full app dependencies: python -m local_engine.check_gflow_dispatch.
"""
import asyncio,base64,io,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
from PIL import Image
from .simple_flow import SimpleFlow,SimpleStopped,MODEL
from .request_ledger import RequestLedger

async def scenario(mode):
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);ledger=RequestLedger(root)
  service=SimpleFlow(root,SimpleNamespace(secret=lambda key:None,set_secret=lambda *args:None),ledger)
  service.account_bridge=SimpleNamespace(background=True,selection=lambda:dict(available=True,account_id='selected',token='selected-token'))
  service.cli_driver_enabled=True;service.native_pipeline_enabled=True
  order=[]
  async def restore():order.append('restore')
  service.restore=AsyncMock(side_effect=restore)
  service.assert_ready=AsyncMock()
  service.capture_preview=AsyncMock()
  buffer=io.BytesIO();Image.new('RGB',(32,48),'green').save(buffer,format='PNG')
  raw=buffer.getvalue();rid='flow-dispatch-'+mode
  body=dict(request_id=rid,kind='video',model=MODEL,prompt='fixture prompt',
   references=[dict(data=base64.b64encode(raw).decode(),mime_type='image/png')],
   room_id='room',scene_id='scene',part='part',confirm_send=True,
   native_pipeline=True,automatic=True,selection_token='selected-token')
  calls=[]
  async def engine(actual,request,payload,reference):
   assert actual is service and request==rid and reference.read_bytes()==raw
   assert ledger.metadata(rid)['engine']=='gflow-cli-direct'
   assert (payload['room_id'],payload['scene_id'],payload['part'],payload['account_id'])==('room','scene','part','selected')
   assert order==['restore','prepare','validate'],order
   order.append('engine');calls.append(request)
   if mode=='before':raise SimpleStopped('fixture stopped before grant')
   service.sent=True
   ledger.set_metadata(rid,dict(engine='gflow-cli-direct',generation_granted=True))
   if mode=='after':raise SimpleStopped('fixture stopped after grant')
   ledger.set_metadata(rid,{'provider_task':dict(media_id='video',project_id='project',workflow_id=None,association_confirmed=True)})
   ledger.finish(rid,'done',dict(file='fixture.mp4',scene_id='scene',part='part'))
  async def prepare(actual,report,image,mime,prompt,settings,check,**callbacks):
   order.append('prepare')
   report.update(preparation_method='native_reference_pipeline',native_stage='ready',reference_verified=True,uploaded_media_id='uploaded-image',uploaded_media_project='original-project')
   callbacks['on_persist']()
  async def validate(actual,payload,image):
   order.append('validate')
   assert actual.pair_report['uploaded_media_id']=='uploaded-image'
  with patch('local_engine.flow_native_pipeline.prepare_inputs',prepare),patch('local_engine.flow_prepare.validate_prepared',validate),patch('local_engine.flow_gflow_cli.generate',engine):
   await service.submit(body)
   await service.tasks[rid]
   row=service.lookup(rid);expected={'success':'done','before':'failed','after':'unknown'}[mode]
   assert row['state']==expected,row
   assert service.active is None and service.task.done()
   service.restore.assert_awaited_once()
   assert order==['restore','prepare','validate','engine'],order
   assert ledger.metadata(rid)['native_inputs']['uploaded_media_id']=='uploaded-image'
   if mode=='success':assert row['provider_task']['media_id']=='video' and row['result']['scene_id']=='scene'
   again=await service.submit(body)
   assert again['state']==expected and calls==[rid],(again,calls)
  print('PASS actual submit/run dispatch, ledger, duplicate receipt:',mode)

async def upload_only():
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);service=SimpleFlow(root,SimpleNamespace(secret=lambda key:None),RequestLedger(root))
  service.cli_driver_enabled=True;service.upload_report=dict(logs=[],request_id='upload-test',delivered=False)
  service.restore=AsyncMock(side_effect=SimpleStopped('fixture stop before uploading'))
  with patch('local_engine.flow_gflow_cli.generate',new_callable=AsyncMock) as engine:
   await service.run_upload_only('upload-test',b'fixture','image/png');engine.assert_not_called()
  print('PASS upload-only never invokes generation engine')

async def main():
 for mode in ('success','before','after'):await scenario(mode)
 await upload_only()
if __name__=='__main__':asyncio.run(main())
