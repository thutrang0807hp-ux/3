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
FIXTURE=r'''import json,pathlib,sys,time
args=sys.argv[1:]
mode=pathlib.Path('mode').read_text()
with pathlib.Path('calls').open('a') as log:log.write(' '.join(args[:2])+'\n')
if args[:2]==['data','download']:
 assert args[2]=='22222222-2222-4222-8222-222222222222'
 assert '--ref' not in args and 'r2v' not in args
 if mode=='download_still_fails':sys.exit(6)
 out=pathlib.Path(args[args.index('--out')+1])/'recovered.mp4';out.write_bytes(b'fixture video')
 print(json.dumps(dict(media_id=args[2],project_id='11111111-1111-4111-8111-111111111111',profile='default',workflow_id=None,path=str(out))))
 print('fixture download stderr retained',file=sys.stderr)
 sys.exit(0)
assert args[0]=='video' and args[1] in ('r2v','i2v')
assert '--' in args and args[-1]=='--a prompt as plain text'
assert '--duration' not in args
assert args[args.index('--profile')+1]=='default'
ref=pathlib.Path(args[args.index('--ref')+1] if args[1]=='r2v' else args[args.index('--')+1]);assert ref.name=='flow-fixture-inputs.png' and ref.read_bytes()==b'image'
assert pathlib.Path('grant.json').is_file()
mode=pathlib.Path('mode').read_text()
print('fixture stderr retained',file=sys.stderr)
if mode in ('live_progress','live_mismatch'):
 def event(name,**fields):print(json.dumps(dict(event=name,level='info',**fields)),file=sys.stderr,flush=True)
 event('migrated.dispatch',project_id='11111111-1111-4111-8111-111111111111')
 event('migrated.frame_uploaded',media_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
 if mode=='live_progress':
  while not pathlib.Path('allow_video').exists():time.sleep(.01)
 event('migrated.submit_observed',media_id='22222222-2222-4222-8222-222222222222' if mode=='live_progress' else '44444444-4444-4444-8444-444444444444',workflow_id='33333333-3333-4333-8333-333333333333',status=6)
 event('migrated.status',status=2)
 if mode=='live_progress':
  while not pathlib.Path('release').exists():time.sleep(.01)
 event('migrated.status',status=3)
if mode=='error':sys.exit(3)
if mode in ('download_error','download_still_fails'):
 print(json.dumps(dict(status='fail',error=dict(**{'class':'MediaDownloadError'},remediation_hint='Run gflow data download 22222222-2222-4222-8222-222222222222'))))
 sys.exit(6)
out=pathlib.Path(args[args.index('--out-dir')+1])/'video.mp4';out.write_bytes(b'fixture video')
print(json.dumps(dict(command='video '+args[1],status='ok',succeeded=True,media_id='22222222-2222-4222-8222-222222222222',local_path=str(out)),indent=2))
'''

class CliTests(unittest.IsolatedAsyncioTestCase):
 async def scenario(self,mode,settings=None):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);repo=root/'Downloads'/'GFlow-Studio-Portable';repo.mkdir(parents=True)
   (repo/'runtime').mkdir();(repo/'runtime/python.exe').write_bytes(b'fixture')
   profile=repo/'data/profiles/profile_default';profile.mkdir(parents=True);(profile/'.gflow_account').write_text('selected@example.com')
   module=repo/'gflow_cli';module.mkdir();(module/'__main__.py').write_text(FIXTURE)
   (repo/'mode').write_text(mode)
   reference=root/'reference.png';reference.write_bytes(b'image')
   payload=dict(account_id='account',room_id='room',scene_id='scene',part='part',model='lite',prompt='--a prompt as plain text',prepared_request_id='flow-fixture-inputs')
   cfg=settings or dict(kind='video',mode='ingredients',ratio='9:16',model='lite',outputs=1)
   if settings:payload['settings']=cfg
   prepared=dict(settings=cfg,request_id=payload['prepared_request_id'],uploaded_media_project=PROJECT,uploaded_media_source_sha256=hashlib.sha256(b'image').hexdigest())
   if mode=='cli_only_upload':
    prepared.pop('uploaded_media_project');prepared.pop('uploaded_media_source_sha256')
    prepared.update(preparation_method='cli_reference_pipeline',project_id=PROJECT,reference_sha256=hashlib.sha256(b'image').hexdigest())
   metadata={**payload,'engine':'gflow-cli-direct','native_inputs':prepared,'cli':{'cwd':str(repo)}};finished=[];launches=[]
   async def ready():pass
   async def validate(rid,path,suffix):return path
   def save(rid,value):
    metadata.update(value)
    if value.get('generation_granted'):(repo/'grant.json').write_text('durable')
   service=types.SimpleNamespace(pair_report=prepared,root=root,sent=False,
    account_bridge=types.SimpleNamespace(binding=lambda aid:dict(email='selected@example.com'),selection=lambda:dict(available=True,account_id='account')),
    gate=asyncio.Lock(),task=None,active=None,busy=lambda:False,lookup=lambda rid:dict(state='unknown'),
    assert_ready=ready,disconnect_browser=ready,phase=lambda rid,phase,message:save(rid,{'phase':phase,'message':message}),validate_video=validate,
    ledger=types.SimpleNamespace(metadata=lambda rid:metadata,set_metadata=save,finish=lambda *args:finished.append(args)))
   original=asyncio.create_subprocess_exec
   async def launch(*args,**kwargs):
    self.assertEqual(args[1:3],('-m','gflow_cli'))
    self.assertEqual(kwargs['cwd'],str(repo))
    self.assertEqual(kwargs['stderr'],asyncio.subprocess.PIPE)
    self.assertEqual(kwargs['env']['GFLOW_CLI_HOME'],str(repo/'data/profiles'))
    if args[3]=='video':
     self.assertEqual(args[args.index('--aspect')+1],cfg['ratio'])
     self.assertEqual(args[args.index('--model')+1],'veo-'+cfg['model'])
     self.assertEqual(args[4],'i2v' if cfg['mode']=='frames' else 'r2v')
    launches.append(args)
    return await original(sys.executable,*args[1:],**kwargs)
   with patch.object(cli,'REPO_DIRECTORY',str(repo)),patch.object(asyncio,'create_subprocess_exec',launch):
    if mode in ('error','download_still_fails','live_mismatch'):
     with self.assertRaises(Stopped):await cli.generate(service,'flow-fixture',payload,reference)
    elif mode=='old_download_error':
     metadata['engine_diagnostics']=dict(exit_code=6,stdout='MediaDownloadError: Run gflow data download '+MEDIA,stderr='')
     await cli.recover_existing(service,'flow-fixture')
    elif mode=='live_progress':
     async def until(predicate):
      async with asyncio.timeout(4):
       while not predicate():await asyncio.sleep(.01)
     task=asyncio.create_task(cli.generate(service,'flow-fixture',payload,reference))
     try:
      await until(lambda:metadata.get('phase')=='uploading')
      self.assertNotIn('provider_task',metadata)
      (repo/'allow_video').touch()
      await until(lambda:(metadata.get('provider_task')or{}).get('state')=='generating')
      self.assertFalse(task.done())
      self.assertEqual(metadata['provider_task']['media_id'],MEDIA)
      self.assertEqual(metadata['provider_task']['workflow_id'],'33333333-3333-4333-8333-333333333333')
      (repo/'release').touch();await task
     finally:
      if not task.done():task.cancel();await asyncio.gather(task,return_exceptions=True)
    else:await cli.generate(service,'flow-fixture',payload,reference)
   self.assertEqual(len(launches),2 if mode in ('download_error','download_still_fails') else 1)
   if mode!='old_download_error':self.assertIn('fixture stderr retained',metadata['engine_diagnostics']['stderr'])
   calls=(repo/'calls').read_text().splitlines()
   self.assertEqual(sum(line.startswith('video ') for line in calls),0 if mode=='old_download_error' else 1)
   if mode in ('download_error','old_download_error'):self.assertIn('data download',calls)
   self.assertEqual(len(finished),0 if mode in ('error','download_still_fails','live_mismatch') else 1)
   if finished:self.assertEqual(finished[0][2]['provider_identity']['media_id'],MEDIA)
 async def test_download_error_recovers_same_media_without_regeneration(self):await self.scenario('download_error')
 async def test_existing_report_downloads_only_never_generates(self):await self.scenario('old_download_error')
 async def test_download_retry_failure_keeps_media_and_never_regenerates(self):await self.scenario('download_still_fails')
 async def test_new_preparation_passes_one_ref_without_native_upload(self):await self.scenario('cli_only_upload')
 async def test_frames_quality_landscape(self):await self.scenario('cli_only_upload',dict(kind='video',mode='frames',ratio='16:9',model='quality',outputs=1))
 async def test_ingredients_fast_landscape(self):await self.scenario('cli_only_upload',dict(kind='video',mode='ingredients',ratio='16:9',model='fast',outputs=1))
 async def test_live_id_arrives_before_cli_exit(self):await self.scenario('live_progress')
 async def test_final_id_must_match_live_id(self):await self.scenario('live_mismatch')
 async def test_cli_success_and_result(self):await self.scenario('success')
 async def test_cli_stderr_and_nonzero_exit(self):await self.scenario('error')
 def test_download_discovery_normalizes_windows_line_endings(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);repo=root/'Downloads'/'wrapper'/'GFlow-Studio-Portable';(repo/'app').mkdir(parents=True)
   (repo/'app/app.py').write_bytes(b'fixture\r\n')
   with patch.object(cli,'APP_SHA256',hashlib.sha256(b'fixture\n').hexdigest()):
    self.assertEqual(cli.find_repo([root/'Downloads']),[repo])
 def test_unsupported_settings_rejected_before_cli(self):
  for changes in (dict(outputs=2),dict(model='quality'),dict(duration=8)):
   cfg=dict(kind='video',mode='ingredients',ratio='9:16',model='lite',outputs=1);cfg.update(changes)
   with self.assertRaises(ValueError):cli.command('/repo','/image','prompt','project','/out',settings=cfg)
 def test_command_keeps_prompt_as_one_argument(self):
  args=cli.command('/repo','/image.png','$(not a command)','project','/out')
  self.assertEqual(args[:5],['py','-m','gflow_cli','video','r2v'])
  self.assertEqual(args[-2:],['--','$(not a command)'])

if __name__=='__main__':unittest.main()
