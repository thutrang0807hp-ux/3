"""Real FFmpeg renders via modern/legacy file options; only syntax errors may retry."""
import asyncio,importlib,json,os,shutil,subprocess,sys,tempfile,zipfile
from pathlib import Path
import httpx
from fastapi import FastAPI

async def main():
 with tempfile.TemporaryDirectory(prefix='sf filter compat ') as td:
  root=Path(td);package=root/'compat_runtime';package.mkdir();(package/'__init__.py').write_text('')
  with zipfile.ZipFile('/workspace/3/downloads/v46/SceneForge-Veo-v46-Source.zip') as archive:
   for name in ['local_jobs.py','schema.py']:(package/name).write_bytes(archive.read('local_engine/'+name))
  source=Path('local_engine/timeline_export.py');source=source if source.is_file() else Path('/workspace/3/veo-node-v46/local_engine/timeline_export.py');(package/'timeline_export.py').write_bytes(source.read_bytes())
  media=root/'source.mp4';real=shutil.which('ffmpeg');subprocess.run([real,'-v','error','-f','lavfi','-i','color=c=red:size=240x426:rate=30','-t','0.3','-c:v','libx264','-pix_fmt','yuv420p',str(media)],check=True)
  modefile=root/'mode';log=root/'calls.jsonl';binpath=root/'bin';binpath.mkdir();wrapper=binpath/'ffmpeg'
  wrapper.write_text('#!'+sys.executable+'\n'+f"""import os,sys,json
from pathlib import Path
args=sys.argv[1:];mode=Path({str(modefile)!r}).read_text()
option=next((o for o in ['-/filter_complex','-filter_complex_script']if o in args),None)
if option:
 with open({str(log)!r},'a')as f:f.write(json.dumps(option)+'\\n')
 if mode=='graph-error':
  sys.stderr.write("No such filter: fixture_failure\\n");sys.exit(1)
 if (mode=='modern'and option=='-filter_complex_script')or(mode=='legacy'and option=='-/filter_complex'):
  sys.stderr.write("Unrecognized option '"+option.lstrip('-')+"'.\\n");sys.exit(1)
 if option=='-/filter_complex':args[args.index(option)]='-filter_complex_script'
os.execv({real!r},[{real!r},*args])
""");wrapper.chmod(0o755);old_path=os.environ['PATH'];os.environ['PATH']=str(binpath)+os.pathsep+old_path
  sys.path.insert(0,td);renderer=importlib.import_module('compat_runtime.timeline_export');app=FastAPI();renderer.install_timeline_exports(app,root);data=media.read_bytes()
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local')as client:
   async def render():
    body={'width':240,'height':426,'fps':30,'duration':.3,'clips':[{'kind':'video','asset':'red','bytes':len(data),'start':0,'duration':.3}]}
    r=await client.post('/local-api/export/timeline',json=body);assert r.status_code==200,r.text;rid=r.json()['id'];assert(await client.put('/local-api/export/timeline/'+rid+'/assets/red',content=data)).status_code==200
    await client.post('/local-api/export/timeline/'+rid+'/start')
    for _ in range(500):
     row=(await client.get('/local-api/export/timeline/'+rid)).json()
     if row['state']in ['done','error','cancelled']:break
     await asyncio.sleep(.02)
    return rid,row
   modefile.write_text('modern');rid,row=await render();assert row['state']=='done',row;assert json.loads(log.read_text().splitlines()[-1])=='-/filter_complex'
   output=root/'verified.mp4';output.write_bytes((await client.get('/local-api/export/timeline/'+rid+'/file')).content);meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(output)]));assert meta['streams'][0]['codec_name']=='h264'
   modefile.write_text('legacy');before=len(log.read_text().splitlines());rid,row=await render();assert row['state']=='done',row;calls=[json.loads(v)for v in log.read_text().splitlines()[before:]];assert calls==['-/filter_complex','-filter_complex_script'],calls
   before=len(log.read_text().splitlines());rid,row=await render();assert row['state']=='done',row;assert len(log.read_text().splitlines())-before==1,'Reuse supported option'
   modefile.write_text('graph-error');before=len(log.read_text().splitlines());rid,row=await render();assert row['state']=='error'and 'fixture_failure'in row['error'],row;assert len(log.read_text().splitlines())-before==1,'Graph errors must never retry encoding'
  os.environ['PATH']=old_path
 print('PASS real MP4 with modern-only and legacy-only FFmpeg option shims; spaces in paths; cached option; no retry for filter-graph failures')
if __name__=='__main__':asyncio.run(main())
