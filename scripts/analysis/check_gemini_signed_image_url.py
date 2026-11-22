"""Real SDK: signed provider URL works, SDK size suffix corrupts it; no live Google."""
import asyncio,importlib.util,io,tempfile
from pathlib import Path
from types import SimpleNamespace
from gemini_webapi import GeneratedImage
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('images',ROOT/'veo-node-v46/local_engine/gemini_image_results.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
buf=io.BytesIO();Image.new('RGB',(180,320),'blue').save(buf,'PNG');data=buf.getvalue()
URL='https://lh3.googleusercontent.com/generated?token=fixture-signed-token'
class Transport:
 def __init__(self):self.urls=[];self.block=False
 async def get(self,url,**kwargs):
  self.urls.append(url);ok=url==URL and not self.block
  return SimpleNamespace(status_code=200 if ok else 403,reason='OK'if ok else'Forbidden',content=data if ok else b'denied',headers={},http_version=2)
async def main():
 with tempfile.TemporaryDirectory()as d:
  t=Transport();image=GeneratedImage(url=URL,title='generated',alt='generated');client=SimpleNamespace(client=t)
  # Reproduce the current SDK's URL transformation and 403 with the same URL.
  try:await image.save(path=d,filename='bad.partial',client=t,full_size=True)
  except Exception:pass
  else:raise AssertionError('fixture expected SDK suffix failure')
  assert t.urls[-1]!=URL
  image.url=URL;t.urls=[]
  variant=await helper.download_existing(image,client,Path(d)/'received.partial')
  assert variant=='provided'and t.urls==[URL]and image.url==URL
  assert(Path(d)/'received.partial').read_bytes()==data
  t.block=True;t.urls=[]
  try:await helper.download_existing(image,client,Path(d)/'denied.partial')
  except helper.ImageDownloadError as error:assert error.status_code==403
  else:raise AssertionError('genuine denial hidden')
  assert t.urls==[URL]and not(Path(d)/'denied.partial').exists(),'signed URL was modified or retried blindly'
  # An expired signed link can still use the authenticated full-image RPC.
  calls=[]
  async def rpc(**kwargs):
   assert kwargs==dict(cid='c_original',rid='r_original',rcid='rc_original',image_id='original-image')
   return 'https://lh3.googleusercontent.com/rpc-original'
  class ExpiredTransport:
   async def get(self,url,**kwargs):
    calls.append(url);status=403 if url==URL else 200
    text='https://lh3.googleusercontent.com/rpc-step?key=fresh'if 'rpc-original' in url else 'https://lh3.googleusercontent.com/final-image?token=fresh'
    def check():
     if status!=200:raise helper.ImageDownloadError(status)
    return SimpleNamespace(status_code=status,reason='OK',content=data,headers={},http_version=2,text=text,raise_for_status=check)
  image=GeneratedImage(url=URL,title='generated',alt='generated',cid='c_original',rid='r_original',rcid='rc_original',image_id='original-image',client_ref=SimpleNamespace(_get_full_size_image=rpc))
  path=Path(d)/'renewed.partial'
  variant=await helper.download_existing(image,SimpleNamespace(client=ExpiredTransport()),path)
  assert variant=='full-size'and path.read_bytes()==data and len(calls)==4
  assert not any(url.startswith(URL+'=s')for url in calls)and image.url==URL
  # SDK's replace-size branch must also be blocked when size occurs before the query.
  async def no_rpc(**kwargs):return None
  t=Transport();t.block=True
  path_url='https://lh3.googleusercontent.com/image=s1024-rj?token=fixture'
  image=GeneratedImage(url=path_url,title='generated',alt='generated',cid='c_original',rid='r_original',rcid='rc_original',image_id='original-image',client_ref=SimpleNamespace(_get_full_size_image=no_rpc))
  try:await helper.download_existing(image,SimpleNamespace(client=t),Path(d)/'blocked.partial')
  except helper.ImageDownloadError as error:assert error.status_code==403
  else:raise AssertionError('mutated signed path was accepted')
  assert t.urls==[path_url]and image.url==path_url
 print('PASS actual SDK signed URL suffix -> 403; exact provider URL downloads identical bytes in one GET; genuine 403 remains explicit; expired link renews via exact image RPC without corrupting query or generating again')
asyncio.run(main())
