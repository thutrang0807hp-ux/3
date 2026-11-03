"""Real submit/prepare/receipt/CLI/ffprobe completion with local CLI and browser doubles."""
import asyncio,base64,hashlib,io,json,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
from PIL import Image
from fastapi import HTTPException
from .simple_flow import SimpleFlow
from .request_ledger import RequestLedger
from .flow_video_options import model_id
from . import flow_gflow_cli as cli
PROJECT='11111111-1111-4111-8111-111111111111'

async def scenario(settings):
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);repo=root/'repo';repo.mkdir();(repo/'runtime').mkdir();(repo/'runtime/python.exe').write_bytes(b'fixture')
  profile=repo/'data/profiles/profile_default';profile.mkdir(parents=True);(profile/'.gflow_account').write_text('selected@example.com')
  shape='160x90' if settings['ratio']=='16:9' else '90x160'
  ff=await asyncio.create_subprocess_exec('ffmpeg','-loglevel','error','-f','lavfi','-i','color=c=blue:s='+shape+':r=12','-t','8','-c:v','libx264','-pix_fmt','yuv420p',str(repo/'ready.mp4'))
  assert await ff.wait()==0
  (repo/'expected.json').write_text(json.dumps(settings))
  package=repo/'gflow_cli';package.mkdir();(package/'__main__.py').write_text("""import sys,json,pathlib,shutil,time
args=sys.argv[1:];cfg=json.loads(pathlib.Path('expected.json').read_text())
assert args[:2]==['video','i2v' if cfg['mode']=='frames' else 'r2v']
assert args[args.index('--aspect')+1]==cfg['ratio'] and args[args.index('--model')+1]=='veo-'+cfg['model']
assert '--duration' not in args and args[args.index('--count')+1]=='1'
image=pathlib.Path(args[args.index('--ref')+1] if cfg['mode']=='ingredients' else args[-2]);assert image.is_file()
with pathlib.Path('calls').open('a') as log:log.write('generate\\n')
for event in [dict(event='migrated.dispatch',project_id='11111111-1111-4111-8111-111111111111'),dict(event='migrated.submit_observed',media_id='22222222-2222-4222-8222-222222222222',workflow_id='33333333-3333-4333-8333-333333333333',status=6),dict(event='migrated.status',status=2)]:print(json.dumps(dict(level='info',**event)),file=sys.stderr,flush=True)
time.sleep(.5)
out=pathlib.Path(args[args.index('--out-dir')+1])/'video.mp4';shutil.copyfile('ready.mp4',out)
print(json.dumps(dict(command='video '+args[1],succeeded=True,media_id='22222222-2222-4222-8222-222222222222',local_path=str(out))))
""")
  ledger=RequestLedger(root);service=SimpleFlow(root,SimpleNamespace(secret=lambda key:None,set_secret=lambda *args:None),ledger)
  service.cli_driver_enabled=True;service.native_pipeline_enabled=True
  service.page=SimpleNamespace(url='https://flow.google.com/project/'+PROJECT,is_closed=lambda:False,remove_listener=lambda *args:None)
  service.account_bridge=SimpleNamespace(background=True,selection=lambda:dict(available=True,account_id='account',token='token'),binding=lambda aid:dict(email='selected@example.com'))
  service.restore=AsyncMock();service.assert_ready=AsyncMock();service.capture_preview=AsyncMock()
  image=io.BytesIO();Image.new('RGB',(32,48),'blue').save(image,format='PNG')
  body=dict(request_id='flow-config-fixture',model=model_id(settings),kind='video',prompt='fixture prompt',references=[dict(mime_type='image/png',data=base64.b64encode(image.getvalue()).decode())],room_id='room',scene_id='scene',part='a',confirm_send=True,selection_token='token',native_pipeline=True,settings=dict(settings))
  native=SimpleNamespace(warmup=AsyncMock(),upload=AsyncMock())
  original=asyncio.create_subprocess_exec
  async def launch(*args,**kwargs):
   if args[1:3]==('-m','gflow_cli'):return await original(sys.executable,*args[1:],**kwargs)
   return await original(*args,**kwargs)
  with patch.object(cli,'REPO_DIRECTORY',str(repo)),patch('local_engine.flow_native_pipeline.NativeProjectSession',return_value=native),patch.object(asyncio,'create_subprocess_exec',launch):
   await service.submit(body)
   task=service.tasks[body['request_id']]
   async with asyncio.timeout(4):
    while not ledger.metadata(body['request_id']).get('provider_task'):await asyncio.sleep(.01)
   early=service.lookup(body['request_id']);assert early['submitted'] is True and not task.done(),early
   assert early['provider_task']['media_id']=='22222222-2222-4222-8222-222222222222'
   await task
   record=service.lookup(body['request_id']);assert record['state']=='done',record
   assert record['result']['settings']==settings and record['result']['model']==model_id(settings)
   assert ledger.metadata(body['request_id'])['generation_settings']==settings
   native.upload.assert_not_called()
   duplicate=await service.submit(body);assert duplicate['state']=='done'
   assert (repo/'calls').read_text().splitlines()==['generate']
   changed={**body,'settings':{**settings,'ratio':'9:16' if settings['ratio']=='16:9' else '16:9'}};changed['model']=model_id(changed['settings'])
   try:await service.submit(changed)
   except HTTPException as exc:assert exc.status_code==409
   else:raise AssertionError('Changed settings reused request ID')
  print('PASS actual submit -> prepared snapshot -> CLI -> ffprobe -> done; early durable ID before exit, pinned settings, no duplicate:',settings)

async def main():
 for mode,model,ratio in [('ingredients','fast','16:9'),('frames','quality','9:16')]:await scenario(dict(kind='video',mode=mode,model=model,ratio=ratio,outputs=1))
if __name__=='__main__':asyncio.run(main())
