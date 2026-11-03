"""Private worker boundary tests using an SDK double; no browser or Google calls."""
import asyncio
import importlib.metadata
import importlib.util
import io
from pathlib import Path
import queue
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).parents[1] / 'local_engine/flow_gflow_worker.py'
spec = importlib.util.spec_from_file_location('sceneforge_worker_test', SOURCE)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)

class Controls:
 def __init__(self): self.queue=queue.Queue()
 def __iter__(self):
  while (line:=self.queue.get()) is not None:yield line

class WorkerTests(unittest.IsolatedAsyncioTestCase):
 async def scenario(self, actual='user@example.com', grant=True):
  controls=Controls();events=[];requests=[];calls=[];closed=[]
  class Page:
   async def evaluate(self,script):return actual
  class Client:
   def __init__(self,**kwargs):self.page=Page();calls.append(kwargs)
   def _persistent_context_kwargs(self):return {'channel':'chrome','headless':False}
   async def __aenter__(self):return self
   async def __aexit__(self,*args):closed.append(True)
   async def generate_video(self,**kwargs):
    requests.append(kwargs)
    assert kwargs['project_id']=='project'
    assert kwargs['req'].ref_names==('flow-fixture-inputs.png',)
    assert not hasattr(kwargs['req'],'reference_images')
    started=types.SimpleNamespace(media_id='media',project_id='project',workflow_id=None)
    kwargs['on_started'](started)
    return types.SimpleNamespace(status=types.SimpleNamespace(succeeded=True,media_id='media'),local_path=Path('clip.mp4'),project_id='project',workflow_id=None)
  client_module=types.ModuleType('gflow_cli.api.client');client_module.FlowApiClient=Client
  video=types.ModuleType('gflow_cli.api.video')
  video.Mode=types.SimpleNamespace(R2V='r2v');video.Aspect=types.SimpleNamespace(PORTRAIT='portrait')
  video.VideoModel=types.SimpleNamespace(VEO_3_1_LITE='lite')
  video.GenerateVideoRequest=lambda **kwargs:types.SimpleNamespace(**kwargs)
  config=types.ModuleType('gflow_cli.config');config.Settings=lambda **kwargs:kwargs
  modules={'gflow_cli':types.ModuleType('gflow_cli'),'gflow_cli.api':types.ModuleType('gflow_cli.api'),client_module.__name__:client_module,video.__name__:video,config.__name__:config}
  def emit(event,**kwargs):
   events.append({'event':event,**kwargs})
   if event=='ready':controls.queue.put('{"action":"generate"}\n' if grant else '{"action":"cancel"}\n')
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);image=root/'input.png';image.write_bytes(b'image')
   browser=root/'chrome.exe';browser.write_bytes(b'fixture')
   values=dict(profile=folder,image=str(image),output=folder,prompt='prompt',browser=str(browser),expected_email='user@example.com',project_id='project',reference_name='flow-fixture-inputs.png')
   try:
    with patch.dict(sys.modules,modules),patch.object(importlib.metadata,'version',return_value='0.92.1'),patch.object(sys,'stdin',controls),patch.object(worker,'emit',emit):
     if actual!='user@example.com':
      with self.assertRaises(ValueError):await worker.run(values)
     elif not grant:
      with self.assertRaises(asyncio.CancelledError):await worker.run(values)
     else:await worker.run(values)
   finally:controls.queue.put(None)
  self.assertEqual(len(closed),1)
  self.assertEqual(len(requests),1 if grant and actual=='user@example.com' else 0)
  if requests:
   request=requests[0]['req']
   self.assertEqual((request.mode,request.aspect,request.model,request.duration,request.count),('r2v','portrait','lite',8,1))
   self.assertEqual([event['event'] for event in events if event['event']!='stage'],['ready','started','complete'])
 async def test_one_reference_portrait_lite(self):await self.scenario()
 async def test_wrong_account_never_generates(self):await self.scenario(actual='other@example.com')
 async def test_no_parent_grant_never_generates(self):await self.scenario(grant=False)

if __name__=='__main__':unittest.main()
