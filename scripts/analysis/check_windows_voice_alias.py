"""Reproduce Windows backend_alias paths with real SQLite and PCM WAV retrieval.
No model inference or Windows installer execution is simulated as successful.
"""
import ast,asyncio,importlib.util,sqlite3,sys,tempfile,types,uuid,wave
import httpx
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
root=Path(__file__).resolve().parents[2]
pkg=types.ModuleType('voice_alias_fixture');pkg.__path__=[];sys.modules[pkg.__name__]=pkg
life=types.ModuleType(pkg.__name__+'.storage_lifecycle');life.owner=lambda row:None;life.SAFE_JOBS=set();sys.modules[life.__name__]=life
spec=importlib.util.spec_from_file_location(pkg.__name__+'.storage_jobs',root/'veo-node-v46/local_engine/storage_jobs.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as tmp:
 path=Path(tmp);source=root/'docs/voice-cpu-real.wav';wav=path/'canonical.wav';wav.write_bytes(source.read_bytes())
 class Library:
  def db(self):return sqlite3.connect(path/'library.db')
  def read_asset_path(self,h):assert h=='fixture-hash';return wav
 lib=Library()
 with lib.db() as db:db.execute('CREATE TABLE backend_alias(path TEXT PRIMARY KEY, request_id TEXT, hash TEXT)')
 jobs=module.StorageJobs.__new__(module.StorageJobs);jobs.lib=lib
 filename=str(uuid.uuid4())+'.wav'
 for sep in ('\\','/'):
  with lib.db() as db:
   db.execute('DELETE FROM backend_alias');db.execute('INSERT INTO backend_alias VALUES(?,?,?)',('media'+sep+filename,'tts-fixture','fixture-hash'))
   legacy=db.execute('SELECT hash FROM backend_alias WHERE path=?',('media/'+filename,)).fetchone()
   if sep=='\\':assert legacy is None,'Fixture must reproduce pre-fix Windows lookup failure'
  result=jobs.voice_file(filename);assert result==wav and result.read_bytes()==source.read_bytes()
  with wave.open(str(result)) as audio:assert audio.getnframes()>0 and audio.getsampwidth()==2
  assert jobs.voice_file('other.wav') is None
  # Exercise the real server media handler, not a duplicated response fixture.
  tree=ast.parse((root/'veo-node-v46/local_engine/server.py').read_text())
  handler=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='media')
  app=FastAPI();env={'app':app,'MEDIA':path/'media','STORAGE_JOBS':jobs,'FileResponse':FileResponse,'HTTPException':HTTPException}
  exec(compile(ast.Module(body=[handler],type_ignores=[]),'real-media-handler','exec'),env)
  async def check_http():
   async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://testserver') as client:
    response=await client.get('/local-api/media/'+filename)
    assert response.status_code==200 and response.content==source.read_bytes()
    assert response.headers['content-type']=='audio/wav'
    assert (await client.get('/local-api/media/missing.wav')).status_code==404
  asyncio.run(check_http())
 wav.unlink();assert jobs.voice_file(filename) is None
print('PASS legacy Windows alias reproduces failed old lookup; fixed lookup serves exact PCM WAV for Windows/POSIX paths; missing aliases/files remain missing')
