"""Exercise real FFmpeg muxing and bounded HTTP intake without downloading YouTube."""
import asyncio, importlib.util, json, subprocess, tempfile
from pathlib import Path
from unittest.mock import patch
import httpx
spec=importlib.util.spec_from_file_location('video_import',Path(__file__).with_name('video_import.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
async def main():
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);video=root/'silent.mp4';audio=root/'sound.m4a'
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=green:s=160x90:d=1','-an','-c:v','libx264','-pix_fmt','yuv420p',str(video)],check=True)
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=1','-c:a','aac',str(audio)],check=True)
  service=m.VideoImport(root)
  async def public(url):return m.checked_url(url)
  info={'title':'Short','duration':1,'formats':[
   {'url':'https://example.com/v','protocol':'https','vcodec':'h264','acodec':'none','height':720},
   {'url':'https://example.com/a','protocol':'https','vcodec':'none','acodec':'aac','abr':128,'http_headers':{'Cookie':'secret','Authorization':'secret','User-Agent':'test'}}]}
  async def metadata(jid,*args):return json.dumps(info).encode()
  real_subprocess=service.subprocess
  async def commands(jid,*args):
   if args[0].endswith('python') or 'yt_dlp' in args:return await metadata(jid,*args)
   return await real_subprocess(jid,*args)
  service.subprocess=commands
  async def handler(request):return httpx.Response(200,content=video.read_bytes() if request.url.path=='/v' else audio.read_bytes())
  with patch.object(m,'public_url',public),patch('importlib.util.find_spec',lambda _:True),patch.object(m,'public_transport',lambda:httpx.MockTransport(handler)):
   url,headers,meta=await service.resolve('test','https://www.youtube.com/shorts/test')
   assert set(meta['_audio']['headers'])=={'User-Agent'}
   job=await service.create({'url':'https://www.youtube.com/shorts/test'});jid=job['id'];await service.tasks[jid]
   result=service.get(jid);assert result['state']=='done',result
   assert result['merged_audio'] and '_audio' not in result,result
   probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(service.path(jid))]))
   assert {s['codec_type'] for s in probe['streams']}=={'video','audio'}
   assert not list(service.root.glob('*.picture')) and not list(service.root.glob('*.audio'))
   complete=service.path(jid).read_bytes()
   await service.release(jid);assert not list(service.root.iterdir())
   print('PASS split stream selection, header filtering, HTTP downloads, real MP4+audio merge, probe and cleanup')
   # Same combined byte budget applies to both streams, including unknown sizes.
   service.jobs['cap']={'bytes':0}
   with patch.object(m,'MAX_BYTES',len(video.read_bytes())+len(audio.read_bytes())-1):
    await service.download('cap','https://example.com/v',{},root/'v.part')
    try:await service.download('cap','https://example.com/a',{},root/'a.part')
    except ValueError:pass
    else:raise AssertionError('Combined byte cap ignored')
   print('PASS combined input size cap')
   service.jobs.pop('cap')
   # Failed second stream removes the first stream too.
   async def failed(request):return httpx.Response(200,content=video.read_bytes()) if request.url.path=='/v' else httpx.Response(403)
   with patch.object(m,'public_transport',lambda:httpx.MockTransport(failed)):
    job=await service.create({'url':'https://www.youtube.com/shorts/fail'});jid=job['id'];await service.tasks[jid]
    assert service.get(jid)['state']=='error';assert not list(service.root.glob(jid+'*'))
   print('PASS second-stream failure cleanup')
   # Prefer an existing complete format; direct file intake remains unchanged.
   info['formats'].append({'url':'https://example.com/complete','protocol':'https','vcodec':'h264','acodec':'aac','height':360})
   url,_,meta=await service.resolve('direct','https://youtu.be/test');assert url.endswith('/complete') and '_audio' not in meta
   assert await service.resolve('direct','https://example.com/movie.mp4')==('https://example.com/movie.mp4',{}, {})
   async def full(request):return httpx.Response(200,content=complete)
   with patch.object(m,'public_transport',lambda:httpx.MockTransport(full)):
    job=await service.create({'url':'https://example.com/movie.mp4'});jid=job['id'];await service.tasks[jid]
    assert service.get(jid)['state']=='done' and not service.get(jid).get('merged_audio')
    await service.release(jid)
   print('PASS complete formats and direct URL compatibility')
   # Cancelling between the two downloads cleans up partial sources.
   info['formats'].pop();original_download=service.download;started=asyncio.Event()
   async def stalled(jid,url,headers,destination=None):
    if url.endswith('/a'):
     destination.write_bytes(b'partial');started.set();await asyncio.Event().wait()
    return await original_download(jid,url,headers,destination)
   service.download=stalled
   job=await service.create({'url':'https://youtu.be/cancel'});jid=job['id'];await asyncio.wait_for(started.wait(),5)
   await service.release(jid);assert not list(service.root.glob(jid+'*')) and not service.processes
   print('PASS cancellation during audio download and temporary file cleanup')
asyncio.run(main())
