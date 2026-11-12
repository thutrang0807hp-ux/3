"""Incomplete TikTok-like format metadata must reach a real media probe."""
import asyncio,importlib.util,json,tempfile,subprocess
from pathlib import Path
from unittest.mock import patch
import httpx
spec=importlib.util.spec_from_file_location('video_import',Path(__file__).with_name('video_import.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
async def main():
 with tempfile.TemporaryDirectory()as td:
  root=Path(td);media=root/'complete.mp4'
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=160x90:d=1','-f','lavfi','-i','sine=frequency=330:duration=1','-c:v','libx264','-c:a','aac','-pix_fmt','yuv420p','-shortest',str(media)],check=True)
  service=m.VideoImport(root);real=service.subprocess;formats=[]
  async def public(url):return m.checked_url(url)
  async def commands(jid,*args):
   if 'yt_dlp' in args:return json.dumps({'extractor_key':'TikTok','title':'Test','duration':1,'formats':formats}).encode()
   return await real(jid,*args)
  service.subprocess=commands
  async def handler(request):return httpx.Response(200,content=media.read_bytes())
  with patch.object(m,'public_url',public),patch.object(m,'public_transport',lambda:httpx.MockTransport(handler)),patch('importlib.util.find_spec',lambda _:True):
   for i,codec in enumerate([{'vcodec':'h264'},{'acodec':'aac'},{}]):
    formats[:]=[{'url':'https://cdn.example.com/video','height':720,'ext':'mp4',**codec}]
    job=await service.create({'url':'https://vt.tiktok.com/test'+str(i)});jid=job['id'];await service.tasks[jid];done=service.get(jid)
    assert done['state']=='done'and done['codec_metadata_incomplete'],done
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(service.path(jid))]))
    assert {s['codec_type']for s in probe['streams']}=={'video','audio'}
    assert done['source_diagnostics']['extractor']=='TikTok'
    safe=json.dumps(done['source_diagnostics']);assert 'cdn.example.com'not in safe and 'http_headers'not in safe
    await service.release(jid)
   print('PASS missing audio/video/both codecs and protocol: downloads/imports real MP4 with audio; sanitized diagnostic metadata')
   # Known audio-only, manifests and DRM must not be relabelled as complete files.
   for f in [dict(vcodec='none',acodec='aac'),dict(protocol='m3u8_native'),dict(protocol='http_dash_segments',fragments=[{}]),dict(has_drm=True)]:
    formats[:]=[{'url':'https://cdn.example.com/file',**f}]
    try:await service.resolve('invalid','https://www.tiktok.com/@test/video/1')
    except ValueError:pass
    else:raise AssertionError(('Unsupported source accepted',f))
   # A page masquerading as MP4 still fails validation and is cleaned up.
   formats[:]=[{'url':'https://cdn.example.com/file'}]
   async def html(request):return httpx.Response(200,content=b'<html>not a video</html>')
   with patch.object(m,'public_transport',lambda:httpx.MockTransport(html)):
    job=await service.create({'url':'https://vt.tiktok.com/html'});jid=job['id'];await service.tasks[jid]
    assert service.get(jid)['state']=='error'and not service.path(jid).exists()
   print('PASS explicit audio-only/manifest/DRM rejection, actual file validation and failed-download cleanup')
asyncio.run(main())
