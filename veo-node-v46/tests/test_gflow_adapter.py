"""Protocol regression tests with a real local child process; no Google requests."""
import asyncio
import importlib.util
import json
import hashlib
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1] / 'local_engine'
PACKAGE = '_gflow_adapter_tests'
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT)]
sys.modules[PACKAGE] = package
adapter_spec = importlib.util.spec_from_file_location(PACKAGE + '.flow_gflow_adapter', ROOT / 'flow_gflow_adapter.py')
adapter = importlib.util.module_from_spec(adapter_spec)
adapter_spec.loader.exec_module(adapter)
class Stopped(RuntimeError): pass
simple = types.ModuleType(PACKAGE + '.simple_flow')
simple.SimpleStopped = Stopped
sys.modules[simple.__name__] = simple

FIXTURE = r'''import json, pathlib, sys, time
spec=json.loads(sys.stdin.readline())
mode=sys.argv[1]
def emit(**event): print(json.dumps(event),flush=True)
emit(event='stage',stage='browser_open')
if mode=='before':
 emit(event='error',error_type='FixtureError',diagnostics=dict(stage='browser_open',detail='fixture startup failure',frames=[dict(file='client.py',line=1,function='setup')]));sys.exit(1)
emit(event='ready',engine_version='0.92.1')
command=json.loads(sys.stdin.readline())
assert command['action']=='generate'
assert pathlib.Path(spec['profile']).joinpath('grant.json').is_file(), 'grant not durable'
if mode=='after':
 emit(event='error',public_error_codes=['PUBLIC_ERROR_UNUSUAL_ACTIVITY','SECRET_INVALID']);sys.exit(1)
assert spec['reference_name']=='flow-fixture-inputs.png'
assert spec['project_id']=='11111111-1111-4111-8111-111111111111'
identity=dict(media_id='media-1',project_id=spec['project_id'],workflow_id=None)
emit(event='started',**identity)
if mode=='cancel':
 assert json.loads(sys.stdin.readline())['action']=='cancel';sys.exit(0)
output=pathlib.Path(spec['output'])/'clip.mp4';output.write_bytes(b'fixture video')
if mode=='mismatch': identity['media_id']='other-media'
emit(event='complete',file=str(output),**identity)
'''

class AdapterTests(unittest.IsolatedAsyncioTestCase):
 async def scenario(self, mode, *, grant_error=False, invalid_prepared=False):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);profile=root/'profile';profile.mkdir()
   image=root/'image.png';image.write_bytes(b'image')
   fixture=root/'fixture.py';fixture.write_text(FIXTURE)
   payload=dict(account_id='account',model='lite',room_id='room',scene_id='scene',part='part',prompt='prompt',prepared_request_id='flow-fixture-inputs')
   binding=dict(account_id='account',profile_key='key',email='user@example.com')
   metadata={};finished=[];children=[]
   def set_metadata(rid,value):
    if value.get('generation_granted'):
     if grant_error: raise OSError('fixture disk failure')
     (profile/'grant.json').write_text(json.dumps(value))
    metadata.update(value)
   async def validate(rid,path,suffix):return path
   async def disconnect():pass
   prepared={key:payload[key] for key in ('account_id','room_id','scene_id','part')}
   prepared.update(request_id=payload['prepared_request_id'],preparation_method='native_reference_pipeline',native_stage='ready',reference_verified=True,uploaded_media_source_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),prompt_sha256=hashlib.sha256(b'prompt').hexdigest(),uploaded_media_project='11111111-1111-4111-8111-111111111111')
   if invalid_prepared:prepared['uploaded_media_source_sha256']='wrong-image'
   service=types.SimpleNamespace(data=root,root=root,sent=False,pair_report=prepared,
    account_bridge=types.SimpleNamespace(binding=lambda aid:binding,selection=lambda:dict(account_id='account',available=True)),
    phase=lambda *args:None,disconnect_browser=disconnect,validate_video=validate,
    ledger=types.SimpleNamespace(set_metadata=set_metadata,finish=lambda *args:finished.append(args)),
    vault=types.SimpleNamespace(set_secret=lambda *args:None))
   login=types.ModuleType(PACKAGE+'.google_login')
   login.flow_profile_path=lambda *args:profile;login.installed_browser=lambda:sys.executable
   runtime=types.ModuleType(PACKAGE+'.flow_gflow_runtime')
   runtime.ensure_runtime=lambda *args:Path(sys.executable)
   real_launch=asyncio.create_subprocess_exec
   async def launch(*args,**kwargs):
    kwargs.pop('creationflags')
    child=await real_launch(sys.executable,str(fixture),mode,**kwargs)
    children.append(child);return child
   with patch.dict(sys.modules,{login.__name__:login,runtime.__name__:runtime}), patch.object(sys,'platform','win32'), patch.object(asyncio,'create_subprocess_exec',launch):
    if mode=='cancel':
     task=asyncio.create_task(adapter.generate(service,'flow-fixture',payload,image))
     for _ in range(200):
      if metadata.get('provider_task'):break
      await asyncio.sleep(.01)
     self.assertIn('provider_task',metadata)
     task.cancel()
     with self.assertRaises(asyncio.CancelledError):await task
    elif mode=='success':
     await adapter.generate(service,'flow-fixture',payload,image)
    else:
     with self.assertRaises((Stopped,OSError)) as caught:
      await adapter.generate(service,'flow-fixture',payload,image)
     self.assertNotIn('SECRET_INVALID',str(caught.exception))
     if mode=='before' and not invalid_prepared:
      self.assertEqual(metadata['engine_diagnostics']['error_type'],'FixtureError')
      self.assertEqual(metadata['engine_diagnostics']['detail'],'fixture startup failure')
      self.assertEqual(metadata['engine_diagnostics']['stage'],'browser_open')
   self.assertTrue(all(child.returncode is not None for child in children))
   self.assertEqual(service.sent, mode!='before' and not grant_error)
   self.assertEqual(len(finished),1 if mode=='success' else 0)
   if finished:
    result=finished[0][2]
    self.assertEqual(result['scene_id'],'scene')
    self.assertEqual(result['provider_identity']['media_id'],'media-1')
    self.assertEqual(result['bytes'],13)
 async def test_changed_prepared_image_never_starts_worker(self):await self.scenario('before',invalid_prepared=True)
 async def test_success(self):await self.scenario('success')
 async def test_error_before_grant(self):await self.scenario('before')
 async def test_error_after_grant(self):await self.scenario('after')
 async def test_wrong_result_identity(self):await self.scenario('mismatch')
 async def test_failed_durable_grant_never_submits(self):await self.scenario('after',grant_error=True)
 async def test_cancel_closes_owned_child(self):await self.scenario('cancel')

if __name__=='__main__':unittest.main()
