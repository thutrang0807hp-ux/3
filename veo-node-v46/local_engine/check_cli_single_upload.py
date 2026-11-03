"""Real preparation/receipt validation: CLI mode must never pre-upload an image."""
import asyncio,hashlib,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
from .flow_native_pipeline import prepare_inputs,DEFAULTS
from .flow_pair_generation import validate_pair
from .flow_prepare import PrepareStopped
PROJECT='11111111-1111-4111-8111-111111111111'

async def main():
 with tempfile.TemporaryDirectory() as folder:
  raw=b'fixture-image';prompt='fixture prompt';page=SimpleNamespace(url='https://flow.google.com/project/'+PROJECT,is_closed=lambda:False)
  report=dict(request_id='flow-single-inputs',room_id='room',scene_id='scene',part='a',account_id='account',reference_sha256=hashlib.sha256(raw).hexdigest(),prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())
  service=SimpleNamespace(root=Path(folder),page=page,pair_page=page,pair_report=report,cli_driver_enabled=True,assert_ready=AsyncMock(),account_bridge=SimpleNamespace(selection=lambda:dict(available=True,account_id='account')))
  native=SimpleNamespace(warmup=AsyncMock(),upload=AsyncMock(),resolve=AsyncMock())
  payload=dict(prepared_request_id=report['request_id'],room_id='room',scene_id='scene',part='a',account_id='account',prompt=prompt)
  with patch('local_engine.flow_native_pipeline.NativeProjectSession',return_value=native):
   await prepare_inputs(service,report,raw,'image/png',prompt,DEFAULTS,service.assert_ready,upload_reference=False)
   native.warmup.assert_awaited_once_with(PROJECT);native.upload.assert_not_called()
   assert report['upload_attempted'] is False and report['delivered'] is False
   assert report['preparation_method']=='cli_reference_pipeline' and report['project_id']==PROJECT
   assert 'uploaded_media_id' not in report and 'uploaded_media_source_sha256' not in report
   await validate_pair(service,payload,raw)
   try:await validate_pair(service,payload,raw+b'changed')
   except PrepareStopped:pass
   else:raise AssertionError('Changed image accepted')
   page.url='https://flow.google.com/project/22222222-2222-4222-8222-222222222222'
   try:await validate_pair(service,payload,raw)
   except PrepareStopped:pass
   else:raise AssertionError('Changed project accepted')
   native.upload.assert_not_called()
 print('PASS actual preparation/receipt: one CLI upload only, no native upload, changed image/project rejected')
if __name__=='__main__':asyncio.run(main())
