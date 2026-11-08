"""Real subprocess/protocol, fixture synthesis; verifies lifecycle, never model speed."""
import asyncio,importlib.util,json,os,sys,tempfile,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'veo-node-v46/local_engine'
async def main():
 spec=importlib.util.spec_from_file_location('runtime_fixture',SRC/'voice_runtime.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);runtime=root/'runtime';runtime.mkdir();(runtime/'model-status.json').write_text('{}');(root/'voice_runtime_worker.py').write_bytes((SRC/'voice_runtime_worker.py').read_bytes());m.__file__=str(root/'voice_runtime.py')
  (root/'voice_worker.py').write_text('''import json,time,hashlib,shutil,wave,os
from pathlib import Path
def load_model(runtime):
 os.write(1,b'native SDK startup noise\\n');print('Python SDK noise')
 p=Path(runtime)/'loads';p.write_text(str(int(p.read_text())+1) if p.exists() else '1');time.sleep(.08);return object()
def synthesize(model,beats,voice,output,workdir):
 text=beats[0]['text']
 if text=='fail':raise ValueError('fixture failure')
 if text=='slow':time.sleep(10)
 source=Path('''+repr(str(ROOT/'docs/voice-cpu-real.wav'))+''');shutil.copyfile(source,output)
 with wave.open(str(output)) as w:duration=w.getnframes()/w.getframerate()
 return {'duration':duration,'sha256':hashlib.sha256(Path(output).read_bytes()).hexdigest(),'segments':[{'id':b['id'],'start':i*duration/len(beats),'end':(i+1)*duration/len(beats)} for i,b in enumerate(beats)]}
''')
  pool=m.VoiceRuntime(idle_seconds=.15,timeout=.4);n=0
  async def job(text='hello',key='model-1'):
   nonlocal n;n+=1;request=root/(str(n)+'.json');output=root/(str(n)+'.wav');result=root/(str(n)+'-result.json');request.write_text(json.dumps({'beats':[{'id':'line','text':text}],'voice':'A'}));await pool.execute(sys.executable,runtime,key,request,output,result);return output
  ticks=0
  async def heartbeat():
   nonlocal ticks
   for _ in range(20):ticks+=1;await asyncio.sleep(.005)
  await asyncio.gather(job(),heartbeat());pid=pool.process.pid;await job();assert pool.process.pid==pid and (runtime/'loads').read_text()=='1' and ticks==20
  await job(key='model-2');assert pool.process.pid!=pid and (runtime/'loads').read_text()=='2'
  try:await job('fail',key='model-2');raise AssertionError('Expected failure')
  except RuntimeError:pass
  assert pool.process is None,'No hidden retry after inference failure'
  try:await job('slow');raise AssertionError('Expected timeout')
  except asyncio.TimeoutError:pass
  assert pool.process is None
  task=asyncio.create_task(job('slow'));await asyncio.sleep(.1);task.cancel()
  try:await task
  except asyncio.CancelledError:pass
  assert pool.process is None
  await job();await asyncio.sleep(.25);assert pool.process is None and pool.phase=='cold'
  # Exercise real parent result validation + asynchronous status path with same child.
  pkg=types.ModuleType('warm_tts_fixture');pkg.__path__=[str(SRC)];sys.modules[pkg.__name__]=pkg;sys.modules[pkg.__name__+'.voice_runtime']=m;m.RUNTIME=pool
  spec=importlib.util.spec_from_file_location(pkg.__name__+'.local_tts',SRC/'local_tts.py');tts=importlib.util.module_from_spec(spec);spec.loader.exec_module(tts)
  tts.engine_root=lambda _:root;tts.tts_status=lambda _:{'model_ready':True,'voices':[{'id':'A'}]};bin=root/'venv/bin';bin.mkdir(parents=True);(bin/'python').symlink_to(sys.executable);media=root/'media';media.mkdir()
  first=await tts.synthesize_isolated(root,media,[{'id':'line','text':'hello'}],'A');pid=pool.process.pid;second=await tts.synthesize_isolated(root,media,[{'id':'line','text':'again'}],'A');assert pool.process.pid==pid and first['url']!=second['url'] and first['duration']>0
  assert len(list(media.glob('*.wav')))==2
  try:await tts.synthesize_isolated(root,media,[{'id':'line','text':'fail'}],'A')
  except Exception as e:assert getattr(e,'status_code',None)==503
  assert len(list(media.glob('*.wav')))==2,'Failed request must not leave output or auto-retry'
  await pool.close()
 print('PASS actual private subprocess reused; one model load across requests; event loop remains active; model change, failure, timeout, cancellation, idle/shutdown cleanup; real WAV/hash/timing validation and failed-output cleanup (fixture model)')
asyncio.run(main())
