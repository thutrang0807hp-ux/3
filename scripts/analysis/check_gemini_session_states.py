"""Real pinned SDK types, fake init transport; session diagnosis must not conflate availability with auth."""
import asyncio,importlib.util,json,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from gemini_webapi import GeminiClient
from gemini_webapi.exceptions import AuthError
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('worker',ROOT/'veo-node-v46/local_engine/gemini_chat_worker.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
mode='ok';calls=[]
class Fake(GeminiClient):
 async def init(self,**kwargs):
  calls.append('init')
  if mode=='init_auth':raise AuthError('PRIVATE_COOKIE_URL')
  self.access_token=''if mode=='token'else'PRIVATE_TOKEN';self._running=True;self._cookie_source='Guest'if mode=='guest'else'Base Cookies'
  self.account_status=SimpleNamespace(name='UNAVAILABLE')
 def _check_account_status(self):return mode not in ['unavailable','unsafe_status']
 def list_models(self):return []
 async def close(self,*args,**kwargs):self._running=False
 async def generate_content(self,*args,**kwargs):raise AssertionError('check must never generate')
async def main():
 global mode
 with tempfile.TemporaryDirectory()as d:
  body={'_workspace':d,'operation':'check','session':{'cookies':{'__Secure-1PSID':'PRIVATE_COOKIE'}}}
  for mode,code in [('init_auth','GEMINI_SESSION_INIT_FAILED'),('guest','GEMINI_SESSION_GUEST'),('token','GEMINI_SESSION_TOKEN_MISSING'),('unavailable','GEMINI_ACCOUNT_UNAVAILABLE'),('ok',None)]:
   result=await w.execute(body,client_type=Fake)
   if code:
    assert result['code']==code,result
    assert 'PRIVATE'not in json.dumps(result),result
   else:assert result['ok']and result['session']['cookies']['__Secure-1PSID']=='PRIVATE_COOKIE'
   if mode=='unavailable':assert result['reason']=='account_unavailable'and result['account_status']=='UNAVAILABLE'
  before=len(calls);result=await w.execute({**body,'session':{}},client_type=Fake);assert result['code']=='GEMINI_SESSION_COOKIE_MISSING'and len(calls)==before
 print('PASS missing cookie / SDK auth-init failure / guest / missing token / account unavailable / valid session distinguished; no generation or raw secrets in failures')
asyncio.run(main())
