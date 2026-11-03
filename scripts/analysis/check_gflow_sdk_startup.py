"""Real SDK + Chromium startup, local intercepted HTTP, cancel before generation.
Set PYTHONPATH to the pinned gflow source and install its Linux test dependencies.
This does not test Windows or live Flow.
"""
import asyncio, importlib.util, importlib.metadata, tempfile, sys, queue
from pathlib import Path
from unittest.mock import patch
from gflow_cli.api.client import FlowApiClient
spec=importlib.util.spec_from_file_location('worker',Path(__file__).resolve().parents[2]/'veo-node-v46/local_engine/flow_gflow_worker.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
class Input:
 def __init__(self):self.q=queue.Queue()
 def __iter__(self):
  while (line:=self.q.get()) is not None:yield line
async def main():
 original=FlowApiClient._launch_persistent_context
 async def local_browser(self,options):
  options=dict(options,headless=True)
  options['args']=[*options['args'],'--no-sandbox']
  context=await original(self,options)
  await context.route('**/*',lambda route:route.fulfill(status=200,content_type='text/html',body='<script>window.WIZ_global_data={oPEP7c:"fixture@example.com"}</script>'))
  return context
 controls=Input();events=[]
 def emit(event,**fields):
  events.append(event)
  if event=='ready':controls.q.put('{"action":"cancel"}\n')
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);image=root/'image.png';image.write_bytes(b'image')
  values=dict(profile=folder,image=str(image),output=folder,prompt='fixture',browser='/usr/bin/chromium',expected_email='fixture@example.com',project_id='11111111-1111-4111-8111-111111111111',reference_name='ref.png')
  with patch.object(importlib.metadata,'version',return_value='0.92.1'),patch.object(FlowApiClient,'_launch_persistent_context',local_browser),patch.object(worker,'emit',emit),patch.object(sys,'stdin',controls):
   try:
    await asyncio.wait_for(worker.run(values),70)
   except asyncio.CancelledError:pass
   finally:controls.q.put(None)
  assert [event for event in events if event!='stage']==['ready'],events
 from gflow_cli.redaction import redact_sensitive_text
 detail=worker.error_fields(RuntimeError('Bearer fixture_secret_token OSID=fixture_cookie https://example.test/video?X-Goog-Signature=fixture_signature'))
 assert all(value not in detail['detail'] for value in ('fixture_secret_token','fixture_cookie','fixture_signature'))
 print('PASS actual SDK error-detail redaction')
 print('PASS actual SDK/Chromium startup through worker, intercepted HTTP, zero generation grants')
asyncio.run(main())
