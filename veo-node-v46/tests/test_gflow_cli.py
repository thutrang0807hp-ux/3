"""Direct -m gflow_cli process integration; local CLI fixture, zero Google calls."""
import asyncio,hashlib,importlib.util,json,os
from pathlib import Path
import sys,tempfile,types,unittest
from unittest.mock import patch
ROOT=Path(__file__).parents[1]/'local_engine'
PACKAGE='_cli_test'
package=types.ModuleType(PACKAGE);package.__path__=[str(ROOT)];sys.modules[PACKAGE]=package
spec=importlib.util.spec_from_file_location(PACKAGE+'.flow_gflow_cli',ROOT/'flow_gflow_cli.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
class Stopped(RuntimeError):pass
simple=types.ModuleType(PACKAGE+'.simple_flow');simple.SimpleStopped=Stopped;sys.modules[simple.__name__]=simple
PROJECT='11111111-1111-4111-8111-111111111111'
MEDIA='22222222-2222-4222-8222-222222222222'
FIXTURE='''import json,pathlib,sys
args=sys.argv[1:]
assert args[:2]==['video','r2v']
assert args[-2]=='--' and args[-1]=='--a prompt as plain text'
assert args[args.index('--duration')+1]=='8'
assert args[args.index('--profile')+1]=='default'
ref=pathlib.Path(args[args.index('--ref')+1]);assert ref.name=='flow-fixture-inputs.png' and ref.read_bytes()==b'image'
assert pathlib.Path('grant.json').is_file()
mode=pathlib.Path('mode').read_text()
print('fixture stderr retained',file=sys.stderr)
if mode=='error':sys.exit(3)
out=pathlib.Path(args[args.index('--out-dir')+1])/'video.mp4';out.write_bytes(b'fixture video')
print(json.dumps(dict(command='video r2v',status='ok',succeeded=True,media_id='22222222-2222-4222-8222-222222222222',local_path=str(out)),indent=2))
'''

class CliTests(unittest.IsolatedAsyncioTestCase):
 async def scenario(self,mode):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);repo=root/'Downloads'/'GFlow-Studio-Portable';repo.mkdir(parents=True)
   (repo/'runtime').mkdir();(repo/'runtime/python.exe').write_bytes(b'fixture')
   profile=repo/'data/profiles/profile_default';profile.mkdir(parents=True);(profile/'.gflow_account').write_text('selected@example.com')
   module=repo/'gflow_cli';module.mkdir();(module/'__main__.py').write_text(FIXTURE)
   (repo/'mode').write_text(mode)
   reference=root/'reference.png';reference.write_bytes(b'image')
   payload=dict(account_id='account',room_id='room',scene_id='scene',part='part',model='lite',prompt='--a prompt as plain text',prepared_request_id='flow-fixture-inputs')
   prepared=dict(request_id=payload['prepared_request_id'],uploaded_media_project=PROJECT,uploaded_media_source_sha256=hashlib.sha256(b'image').hexdigest())
   metadata={};finished=[];launches=[]
   async def ready():pass
   async def validate(rid,path,suffix):return path
   def save(rid,value):
    metadata.update(value)
    if value.get('generation_granted'):(repo/'grant.json').write_text('durable')
   service=types.SimpleNamespace(pair_report=prepared,root=root,sent=False,
    account_bridge=types.SimpleNamespace(binding=lambda aid:dict(email='selected@example.com')),
    assert_ready=ready,disconnect_browser=ready,phase=lambda *args:None,validate_video=validate,
    ledger=types.SimpleNamespace(set_metadata=save,finish=lambda *args:finished.append(args)))
   original=asyncio.create_subprocess_exec
   async def launch(*args,**kwargs):
    self.assertEqual(args[1:3],('-m','gflow_cli'))
    self.assertEqual(kwargs['cwd'],str(repo))
    self.assertEqual(kwargs['stderr'],asyncio.subprocess.PIPE)
    self.assertEqual(kwargs['env']['GFLOW_CLI_HOME'],str(repo/'data/profiles'))
    launches.append(args)
    return await original(sys.executable,*args[1:],**kwargs)
   with patch.object(cli,'REPO_DIRECTORY',str(repo)),patch.object(asyncio,'create_subprocess_exec',launch):
    if mode=='error':
     with self.assertRaises(Stopped):await cli.generate(service,'flow-fixture',payload,reference)
    else:await cli.generate(service,'flow-fixture',payload,reference)
   self.assertEqual(len(launches),1)
   self.assertIn('fixture stderr retained',metadata['engine_diagnostics']['stderr'])
   self.assertEqual(len(finished),0 if mode=='error' else 1)
   if finished:self.assertEqual(finished[0][2]['provider_identity']['media_id'],MEDIA)
 async def test_cli_success_and_result(self):await self.scenario('success')
 async def test_cli_stderr_and_nonzero_exit(self):await self.scenario('error')
 def test_download_discovery_normalizes_windows_line_endings(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);repo=root/'Downloads'/'wrapper'/'GFlow-Studio-Portable';(repo/'app').mkdir(parents=True)
   (repo/'app/app.py').write_bytes(b'fixture\r\n')
   with patch.object(cli,'APP_SHA256',hashlib.sha256(b'fixture\n').hexdigest()):
    self.assertEqual(cli.find_repo([root/'Downloads']),[repo])
 def test_command_keeps_prompt_as_one_argument(self):
  args=cli.command('/repo','/image.png','$(not a command)','project','/out')
  self.assertEqual(args[:5],['py','-m','gflow_cli','video','r2v'])
  self.assertEqual(args[-2:],['--','$(not a command)'])

if __name__=='__main__':unittest.main()
