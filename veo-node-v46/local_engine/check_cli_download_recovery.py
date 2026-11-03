"""Actual report route, ledger, ffprobe and file endpoint; local CLI fixture only."""
import asyncio,hashlib,json,shutil,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import httpx
from fastapi import FastAPI
from .simple_flow import install_simple_flow,MODEL
from .request_ledger import RequestLedger
from . import flow_gflow_cli as cli

async def main():
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);repo=root/'repo';repo.mkdir();(repo/'runtime').mkdir();(repo/'runtime/python.exe').write_bytes(b'fixture')
  profile=repo/'data/profiles/profile_default';profile.mkdir(parents=True);(profile/'.gflow_account').write_text('selected@example.com')
  movie=repo/'ready.mp4'
  process=await asyncio.create_subprocess_exec('ffmpeg','-loglevel','error','-f','lavfi','-i','color=c=blue:s=90x160:r=12','-t','8','-c:v','libx264','-pix_fmt','yuv420p',str(movie))
  assert await process.wait()==0
  module=repo/'gflow_cli';module.mkdir();(module/'__main__.py').write_text("""import sys,json,pathlib,shutil
args=sys.argv[1:]
assert args[:2]==['data','download'],args
with pathlib.Path('calls').open('a') as log:log.write('download\\n')
out=pathlib.Path(args[args.index('--out')+1])/'clip.mp4';shutil.copyfile('ready.mp4',out)
print(json.dumps(dict(media_id=args[2],project_id='11111111-1111-4111-8111-111111111111',profile='default',workflow_id=None,path=str(out))))
""")
  ledger=RequestLedger(root);vault=SimpleNamespace(secret=lambda key:None,set_secret=lambda *args:None)
  app=FastAPI();provider=SimpleNamespace(account_service=None)
  service=install_simple_flow(app,root,vault,ledger,provider)
  service.account_bridge=SimpleNamespace(background=True,binding=lambda aid:dict(email='selected@example.com'),selection=lambda:dict(available=True,account_id='account'))
  rid='flow-existing-download';media='22222222-2222-4222-8222-222222222222'
  payload=dict(room_id='room',scene_id='scene',part='part',account_id='account',model=MODEL,kind='video')
  ledger.claim(rid,payload);ledger.set_metadata(rid,dict(transport='simple_flow',engine='gflow-cli-direct',part='part',prompt='prompt',cli={'cwd':str(repo)},native_inputs={'uploaded_media_project':'11111111-1111-4111-8111-111111111111'},engine_diagnostics={'exit_code':6,'stdout':'MediaDownloadError: Run gflow data download '+media,'stderr':''}));ledger.finish(rid,'unknown')
  original=asyncio.create_subprocess_exec
  async def launch(*args,**kwargs):
   if len(args)>2 and args[1:3]==('-m','gflow_cli'):return await original(sys.executable,*args[1:],**kwargs)
   return await original(*args,**kwargs)
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
   base='/local-api/flow/simple/diagnostics/'+rid
   with patch.object(asyncio,'create_subprocess_exec',launch):
    wrong=await client.get(base,params=dict(store_id=ledger.store_id,room_id='other',download_existing='true'))
    assert wrong.json()['code']=='different_room' and not(repo/'calls').exists()
    read=await client.get(base,params=dict(store_id=ledger.store_id,room_id='room'))
    assert read.json()['record']['state']=='unknown' and not(repo/'calls').exists()
    done=await client.get(base,params=dict(store_id=ledger.store_id,room_id='room',download_existing='true'))
    record=done.json()['record'];assert record['state']=='done',done.text
    assert record['result']['scene_id']=='scene' and record['result']['part']=='part'
    file=await client.get('/local-api/flow/simple/files/'+rid)
    assert hashlib.sha256(file.content).digest()==hashlib.sha256(movie.read_bytes()).digest()
    again=await client.get(base,params=dict(store_id=ledger.store_id,room_id='room',download_existing='true'))
    assert again.json()['record']['state']=='done' and (repo/'calls').read_text().splitlines()==['download']
  print('PASS real diagnostics route -> download only -> ffprobe -> durable done -> same-scene file; no replay, cross-room rejected')
if __name__=='__main__':asyncio.run(main())
