"""Real API/SQLite-free cache tests with fixture WAVs; no model inference claim."""
import asyncio,hashlib,importlib.util,json,sys,tempfile,types
from pathlib import Path
import httpx
from fastapi import FastAPI
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'veo-node-v46/local_engine';WAV=(ROOT/'docs/voice-cpu-real.wav').read_bytes()
pkg=types.ModuleType('prep_fixture');pkg.__path__=[str(SRC)];sys.modules[pkg.__name__]=pkg
local=types.ModuleType('prep_fixture.local_tts');machine=types.ModuleType('prep_fixture.machine_checks');sys.modules[local.__name__]=local;sys.modules[machine.__name__]=machine
async def main():
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);(root/'runtime').mkdir();(root/'runtime/model-status.json').write_text('{}');voices=[{'id':'Giọng A'},{'id':'Giọng B'}];calls=[];release=asyncio.Event()
  local.engine_root=lambda _:root;local.tts_status=lambda _:{'model_ready':True,'voices':voices}
  async def command(*args,**kw):
   calls.append(args);folder=Path(args[args.index('--output')+1]);await release.wait()
   for row in voices:
    key=hashlib.sha256(row['id'].encode()).hexdigest();(folder/(key+'.wav')).write_bytes(WAV);(folder/(key+'.json')).write_text(json.dumps({'id':row['id'],'sha256':hashlib.sha256(WAV).hexdigest()}))
   return 0,b'',b''
  machine.run_command=command
  spec=importlib.util.spec_from_file_location('prep_fixture.voice_previews',SRC/'voice_previews.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  app=FastAPI();lock=asyncio.Lock();shutdown=m.install_voice_previews(app,root,lock)
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://testserver') as c:
   async def get():return (await c.get('/local-api/tts/previews/status')).json()
   assert (await get())['state']=='not-prepared' and not calls
   key=hashlib.sha256(voices[0]['id'].encode()).hexdigest();assert (await c.get('/local-api/tts/previews/file/'+key)).status_code==404 and not calls
   await lock.acquire();assert (await c.post('/local-api/tts/previews/prepare',json={})).status_code==409;lock.release()
   assert (await c.post('/local-api/tts/previews/prepare',json={})).json()['state']=='running';await asyncio.sleep(.01);assert lock.locked() and len(calls)==1
   await c.post('/local-api/tts/previews/prepare',json={});assert len(calls)==1
   await c.post('/local-api/tts/previews/cancel',json={});assert not lock.locked() and (await get())['state']=='not-prepared'
   release.set();await c.post('/local-api/tts/previews/prepare',json={});await asyncio.sleep(.02);state=await get();assert state['state']=='ready' and len(state['ready'])==2
   before=len(calls)
   for _ in range(2):
    r=await c.get(state['ready'][0]['url']);assert r.status_code==200 and r.content==WAV
   await c.post('/local-api/tts/previews/prepare',json={});assert len(calls)==before,'Ready playback/preparation must not invoke CPU worker'
   # Restart service with same engine folder retains samples across projects/sessions.
   fresh=FastAPI();m.install_voice_previews(fresh,root,asyncio.Lock())
   async with httpx.AsyncClient(transport=httpx.ASGITransport(app=fresh),base_url='http://testserver') as f:assert len((await f.get('/local-api/tts/previews/status')).json()['ready'])==2
   # Corrupt files are not offered; marker/model change gets a fresh cache namespace.
   file=next((root/'previews').glob('*/*.wav'));file.write_bytes(b'corrupt');assert len((await get())['ready'])==1
   (root/'runtime/model-status.json').write_text('{"changed":true}');assert not (await get())['ready']
   release.clear();await c.post('/local-api/tts/previews/prepare',json={});await asyncio.sleep(.01);assert lock.locked();await shutdown();assert not lock.locked()
 # Real worker loop with synthesis fixture: one call per missing preset; cached resume skips completed WAV.
 sys.path.insert(0,str(SRC));spec=importlib.util.spec_from_file_location('preview_worker_fixture',SRC/'voice_previews_worker.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w);made=[]
 def synth(model,beats,voice,output,workdir):made.append(voice);Path(output).write_bytes(WAV);return {'sha256':hashlib.sha256(WAV).hexdigest()}
 w.synthesize=synth
 with tempfile.TemporaryDirectory() as tmp:
  w.prepare(object(),['A','B'],tmp);w.prepare(object(),['A','B'],tmp);assert made==['A','B']
 print('PASS explicit preparation only; single worker/lock; cancel; durable shared previews; HTTP WAV playback without synthesis; cache integrity/model binding; worker resumes missing presets')
asyncio.run(main())
