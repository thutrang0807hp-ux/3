"""Pair accepted != account verified: actual adapter and bridge completion with fake SDK."""
import ast,asyncio,hashlib,json,time
from pathlib import Path
from contextlib import asynccontextmanager
from types import SimpleNamespace
from fastapi import HTTPException
ROOT=Path(__file__).resolve().parents[2]
def method(file,cls,names,ns):
 tree=ast.parse((ROOT/file).read_text());c=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name==cls)
 exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name=cls,bases=[],keywords=[],body=[n for n in c.body if getattr(n,'name','')in names],decorator_list=[])],type_ignores=[])),'actual-connection','exec'),ns);return ns[cls]
@asynccontextmanager
async def exclusive(aid):yield
async def main():
 rows={};secrets={};mode='ok';selected=[]
 ns=dict(asyncio=asyncio,hashlib=hashlib,json=json,time=time,HTTPException=HTTPException)
 G=method('veo-node-v46/local_engine/gemini_chat.py','GeminiChat',{'import_session'},ns);g=G()
 g.image_slots=SimpleNamespace(exclusive=exclusive);g.lock=lambda aid:exclusive(aid);g.accounts=lambda:list(rows.values());g.require_sdk=lambda:None
 g.vault=SimpleNamespace(secret=lambda k:secrets.get(k),set_secret=lambda k,v:secrets.__setitem__(k,v),put=lambda table,r:rows.__setitem__(r['id'],r))
 g.account=lambda aid:rows[aid]
 g.pool=SimpleNamespace(select=lambda b:selected.append(b));g.select=g.pool.select
 async def runner(body):
  if mode=='timeout':raise TimeoutError()
  if mode=='auth':return {'ok':False,'reason':'auth'}
  return {'ok':True,'session':body['session'],'models':[]}
 g.runner=runner
 B=method('veo-node-v46/local_engine/browser_bridge.py','BrowserBridge',{'finish'},ns);b=B();b.gemini=g
 for case in ['ok','auth','timeout']:
  mode=case;rows.clear();p={'service':'gemini_chat','services':['gemini_chat'],'name':'Fixture','state':'checking'}
  await b.finish(p,[{'domain':'.google.com','path':'/','name':'__Secure-1PSID','value':'PRIVATE_TEST_ONLY'}])
  if case=='ok':assert p['state']=='done'and p['account_id']in rows and rows[p['account_id']]['session_verified']
  else:
   assert p['state']=='failed'and not rows
   assert p['results']['gemini_chat']['code']==('GEMINI_SESSION_AUTH_REJECTED'if case=='auth'else'GEMINI_SESSION_CHECK_TIMEOUT')
   assert 'PRIVATE_TEST_ONLY'not in json.dumps(p)
 print('PASS actual bridge -> adapter -> account storage and selection; auth and timeout remain explicit failures without fake ready accounts or credential leakage')
asyncio.run(main())
