"""Select TikTok playback metadata rather than a marked download; no pixel claim."""
import asyncio,importlib.util,json,tempfile,subprocess
from pathlib import Path
from unittest.mock import patch
import httpx
spec=importlib.util.spec_from_file_location('video_import',Path(__file__).with_name('video_import.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
async def main():
 with tempfile.TemporaryDirectory()as td:
  root=Path(td);media=root/'source.mp4'
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=160x90:d=1','-f','lavfi','-i','sine=frequency=330:duration=1','-c:v','libx264','-c:a','aac','-pix_fmt','yuv420p','-shortest',str(media)],check=True)
  service=m.VideoImport(root);real=service.subprocess;formats=[];extractor='TikTok';fetched=[]
  async def public(url):return m.checked_url(url)
  async def commands(jid,*args):
   if 'yt_dlp'in args:return json.dumps({'extractor_key':extractor,'title':'Test','duration':1,'formats':formats}).encode()
   return await real(jid,*args)
  async def handler(request):fetched.append(str(request.url));return httpx.Response(200,content=media.read_bytes())
  def fmt(id,height,**kw):return {'format_id':id,'url':'https://cdn.example.com/'+id,'vcodec':'h264','acodec':'aac','height':height,'protocol':'https',**kw}
  service.subprocess=commands
  with patch.object(m,'public_url',public),patch.object(m,'public_transport',lambda:httpx.MockTransport(handler)),patch('importlib.util.find_spec',lambda _:True):
   formats[:]=[fmt('download',1080,format_note='watermarked'),fmt('play',720)]
   job=await service.create({'url':'https://vt.tiktok.com/test'});jid=job['id'];await service.tasks[jid];done=service.get(jid)
   assert done['state']=='done'and done['tiktok_source_kind']=='playback',done
   assert fetched==['https://cdn.example.com/play'],fetched
   assert service.path(jid).read_bytes()==media.read_bytes()and done['watermark_pixels_checked']is False
   assert done['source_diagnostics']['selected_format_id']=='play'
   await service.release(jid)
   print('PASS 720p playback beats 1080p watermarked download, selected bytes preserved and no false pixel-removal claim')
   # Codec metadata omission must not make a marked complete stream win.
   formats[:]=[fmt('download',1080,format_note='watermarked'),fmt('play',540,acodec=None)]
   url,_,meta=await service.resolve('probe','https://vt.tiktok.com/test');assert url.endswith('/play')and meta['codec_metadata_incomplete']
   # Known split playback plus audio outranks a watermarked muxed download.
   formats[:]=[fmt('download',1080,format_note='watermarked'),fmt('play_addr_h264',720,acodec='none'),fmt('audio',0,vcodec='none',acodec='aac')]
   url,_,meta=await service.resolve('split','https://vt.tiktok.com/test');assert url.endswith('/play_addr_h264')and meta['_audio']['url'].endswith('/audio')
   # An unusable split playback source must not hide a usable complete fallback.
   formats[:]=[fmt('download',1080,format_note='watermarked'),fmt('play_addr',720,acodec='none')]
   url,_,meta=await service.resolve('fallback','https://vt.tiktok.com/test');assert url.endswith('/download')and meta['source_notice']and meta['tiktok_source_kind']=='watermarked'
   formats[:]=[fmt('download',1080,format_note='watermarked',width=1920),fmt('play',1920,width=1080)]
   url,_,meta=await service.resolve('portrait','https://vt.tiktok.com/test');assert url.endswith('/play')
   assert m.supported_video_size({'width':720,'height':1280}) and m.supported_video_size({'width':1080,'height':1920})
   assert not m.supported_video_size({'width':2160,'height':3840})
   print('PASS incomplete/split playback priorities, explicit marked fallback and portrait 1080p selection')
   # API metadata and unknown evidence are distinguished; unrelated sites keep resolution selection.
   formats[:]=[fmt('download_addr',1080,has_watermark=True),fmt('api_clean',540,has_watermark=False)]
   url,_,meta=await service.resolve('api','https://vt.tiktok.com/test');assert url.endswith('/api_clean')and meta['tiktok_source_kind']=='declared_unwatermarked'
   formats[:]=[fmt('unknown',720)];_,_,meta=await service.resolve('unknown','https://vt.tiktok.com/test');assert meta['tiktok_source_kind']=='unknown'and meta['source_notice']
   extractor='Youtube';formats[:]=[fmt('download',1080,format_note='watermarked'),fmt('play',720)]
   url,_,meta=await service.resolve('yt','https://www.youtube.com/watch?v=x');assert url.endswith('/download')and 'tiktok_source_kind'not in meta
   print('PASS explicit API flags, unknown-source notice, non-TikTok selection unchanged')
asyncio.run(main())
