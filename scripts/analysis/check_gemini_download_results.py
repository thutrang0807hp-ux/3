"""Pinned SDK download/read-chat behavior, no Google connections or new generation."""
import asyncio,importlib.util,io,tempfile
from pathlib import Path
from types import SimpleNamespace
from gemini_webapi import GeneratedImage,GeminiClient
from gemini_webapi.types import ModelOutput,Candidate,ChatHistory,ChatTurn
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
helper=load('images',ROOT/'veo-node-v46/local_engine/gemini_image_results.py');worker=load('worker',ROOT/'veo-node-v46/local_engine/gemini_chat_worker.py')
buf=io.BytesIO();Image.new('RGB',(180,320),'blue').save(buf,'PNG');data=buf.getvalue();requests=[]
class Transport:
 async def get(self,url,**kwargs):
  requests.append(url);bad='=s2048-rj'in url
  return SimpleNamespace(status_code=403 if bad else 200,reason='Forbidden'if bad else'OK',content=data,http_version=2,headers={'content-type':'image/png'})
def output(rid,rcid,url):
 return ModelOutput(metadata=['c_original',rid],candidates=[Candidate(rcid=rcid,text='image',generated_images=[GeneratedImage(url=url,title='image',alt='image')])])
old=output('r_original','rc_original','https://lh3.googleusercontent.com/original=s1024-rj')
latest=output('r_later','rc_later','https://lh3.googleusercontent.com/wrong-later=s1024-rj')
history=ChatHistory(cid='c_original',turns=[ChatTurn(role='model',text='later',model_output=latest),ChatTurn(role='model',text='original',model_output=old)])
class Fake(GeminiClient):
 async def init(self,**kwargs):
  self.access_token='fixture';self._cookie_source='Base Cookies';self._running=True
  t=Transport();t.cookies=self._cookies;self.client=t
 def list_models(self):return []
 async def read_chat(self,cid,**kwargs):
  assert cid=='c_original';return history
 async def generate_content(self,*args,**kwargs):raise AssertionError('recovery generated new content')
 async def close(self,*args,**kwargs):pass
async def main():
 with tempfile.TemporaryDirectory()as d:
  image=old.images[0];path=Path(d)/'same.partial'
  variant=await helper.download_existing(image,SimpleNamespace(client=Transport()),path)
  assert variant=='standard'and path.read_bytes()==data and len(requests)==2
  pointer={'metadata':['c_original','r_original','rc_original']}
  client=SimpleNamespace(read_chat=lambda cid,**kwargs:asyncio.sleep(0,result=history))
  exact=await helper.find_exact_image(client,pointer);assert '/original='in exact.url and '/wrong-later'not in exact.url
  try:await helper.find_exact_image(client,{'metadata':['c_original','r_missing','rc_missing']})
  except ValueError:pass
  else:raise AssertionError('latest turn was substituted')
  result=await worker.execute({'_workspace':d,'operation':'receive_image','kind':'image','image_result':pointer,'session':{'cookies':{'__Secure-1PSID':'fixture'}},'output':str(path)},Fake)
  assert result['ok'] and result['download_variant']=='standard'and path.read_bytes()==data
  error=Exception('Error downloading image: 403 Forbidden')
  assert worker.error_detail(error,'download_image')['http_status']==403
 print('PASS actual SDK full-size HTTP403 -> same image standard file; exact old history turn only; worker receive calls no generation; status recovered without raw exception logging')
asyncio.run(main())
