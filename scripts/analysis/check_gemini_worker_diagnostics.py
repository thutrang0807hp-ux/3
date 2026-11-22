"""Run with the pinned SDK on PYTHONPATH; real SDK models, fake transport only."""
import ast,asyncio,importlib.util,socket,tempfile,re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from gemini_webapi import GeminiClient,GeneratedImage
from gemini_webapi.types import ModelOutput,Candidate
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('worker',root/'veo-node-v46/local_engine/gemini_chat_worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
mode='upload';calls=[]
class Fake(GeminiClient):
 async def init(self,**kwargs):
  if mode=='init':raise RuntimeError('PRIVATE_COOKIE_AND_URL')
  self.access_token='fixture';self._running=True;self._cookie_source='Base Cookies'
 def list_models(self):return [SimpleNamespace(model_name='fixture')]
 async def generate_content(self,prompt,**kwargs):
  calls.append(prompt)
  if mode=='upload':raise OSError('PRIVATE_PROMPT_AND_PATH')
  self._sf_generate_started=True
  if mode=='generate':raise TimeoutError('PRIVATE_URL')
  return ModelOutput(metadata=['c_fixture','r_fixture','rc_fixture'],candidates=[Candidate(rcid='rc_fixture',text='result',generated_images=[GeneratedImage(url='https://lh3.googleusercontent.com/fixture',title='x',alt='x')])])
 async def close(self,*args,**kwargs):self._running=False
class HTTPError(Exception):
 def __init__(self):self.response=SimpleNamespace(status_code=503);super().__init__('PRIVATE_URL')
async def bad_save(*args,**kwargs):raise HTTPError()
async def main():
 global mode
 socket.socket.connect=lambda *a,**k: (_ for _ in ()).throw(AssertionError('network forbidden'))
 with tempfile.TemporaryDirectory()as d,patch.object(worker,'single_send_type',lambda base:Fake),patch.object(GeneratedImage,'save',bad_save):
  body={'_workspace':d,'operation':'generate','kind':'image','session':{'cookies':{'__Secure-1PSID':'PRIVATE_COOKIE'}},'prompt':'PRIVATE_PROMPT','model':'fixture','references':[],'output':str(Path(d)/'out.partial')}
  for mode,code,accepted in [('init','GEMINI_INIT_ERROR',False),('upload','GEMINI_UPLOAD_ERROR',False),('generate','GEMINI_GENERATE_ERROR',None),('download','GEMINI_IMAGE_DOWNLOAD_ERROR',None)]:
   before=len(calls);result=await worker.execute(body)
   assert result['code']==code and result['accepted']is accepted,result
   assert 'PRIVATE'not in str(result),result
   assert len(calls)-before==(0 if mode=='init'else 1),'worker resent generation'
   if mode=='download':assert result['http_status']==503 and result['error_type']=='HTTPError'
 print('PASS real SDK types: init/upload/generation/download distinguished; pre-dispatch proof; HTTP status retained; no raw secrets or automatic resends')
asyncio.run(main())
source=ast.parse((root/'veo-node-v46/local_engine/gemini_chat.py').read_text());cls=next(n for n in source.body if isinstance(n,ast.ClassDef)and n.name=='GeminiChat');lookup=next(n for n in cls.body if getattr(n,'name','')=='lookup')
class Base:
 def lookup(self,rid):return {'state':'failed'}
ns={'Base':Base,'re':re};exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Adapter',bases=[ast.Name(id='Base',ctx=ast.Load())],keywords=[],body=[lookup],decorator_list=[])],type_ignores=[])),'actual-lookup','exec'),ns)
a=ns['Adapter']();a.ledger=SimpleNamespace(metadata=lambda rid:{'last_error_code':'GEMINI_IMAGE_DOWNLOAD_ERROR','error_type':'HTTPError','http_status':503})
result=a.lookup('fixture');assert 'HTTPError' in result['message'] and '503' in result['message'] and result['code']=='GEMINI_IMAGE_DOWNLOAD_ERROR'
print('PASS actual adapter exposes safe download-stage error type and HTTP status')
