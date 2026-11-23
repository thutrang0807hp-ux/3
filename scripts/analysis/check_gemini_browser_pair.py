"""Actual bridge pairing protocol, Origin guard and browser-verified account selection, no SDK/cookie import."""
import ast,asyncio,base64,hashlib,importlib.util,json,os,re,secrets,tempfile,time
from pathlib import Path
from types import SimpleNamespace
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
import httpx
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('broker',ROOT/'veo-node-v46/local_engine/gemini_browser.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
tree=ast.parse((ROOT/'veo-node-v46/local_engine/browser_bridge.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='BrowserBridge');ns=dict(asyncio=asyncio,base64=base64,hashlib=hashlib,json=json,os=os,Path=Path,re=re,secrets=secrets,time=time,HTTPException=HTTPException,Request=Request,FileResponse=FileResponse,JSONResponse=JSONResponse,NATIVE_PATHS=set(),GEMINI_PATHS=m.PATHS)
exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Bridge',bases=[],keywords=[],body=[n for n in cls.body if getattr(n,'name','')!='__init__'],decorator_list=[])],type_ignores=[])),'actual-bridge','exec'),ns)
async def main():
 with tempfile.TemporaryDirectory()as directory:
  secret={};rows={};selected=[]
  vault=SimpleNamespace(secret=lambda k:secret.get(k),set_secret=lambda k,v:secret.__setitem__(k,v),put=lambda table,row:rows.__setitem__(row['id'],row))
  def forbidden(*a,**k):raise AssertionError('SDK/cookie import called')
  service=SimpleNamespace(vault=vault,data=Path(directory),accounts=lambda:list(rows.values()),require_sdk=forbidden,import_session=forbidden,pool=SimpleNamespace(select=lambda body:selected.append(body)))
  app=FastAPI();b=ns['Bridge']();b.gemini=service;b.gemini_browser=m.GeminiBrowser(app,service);b.pairs={};b.tasks=set();b.bad_attempts=[];b.origin='chrome-extension://fixture';b.extension_id='fixture';b.root=ROOT/'veo-node-v46/scripts/browser-extension';b.relay=SimpleNamespace(issue=lambda *a:({'id':'flow-browser'},{'id':'flow-engine'}));b.install(app)
  @app.middleware('http')
  async def guard(request,call_next):
   return await b.extension_request(request,call_next)if request.url.path in m.PATHS|{'/local-api/browser-bridge/claim','/local-api/browser-bridge/complete'}else await call_next(request)
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://127.0.0.1:8840')as c:
   prefix='/local-api/browser-bridge/';p=(await c.post(prefix+'pairs',json={'service':'gemini_chat','services':['gemini_chat'],'name':'Browser account'})).json()
   wrong=await c.post(prefix+'claim',json={'code':p['code'],'protocol':5},headers={'Origin':'chrome-extension://wrong','X-SceneForge-Bridge':'1'});assert wrong.status_code==403
   headers={'Origin':b.origin,'X-SceneForge-Bridge':'1'}
   claimed=(await c.post(prefix+'claim',json={'code':p['code'],'protocol':5},headers=headers)).json();assert claimed['protocol']==5
   auth={'id':claimed['relay']['id'],'key':claimed['relay']['browser_key']}
   await c.post(prefix+'gemini-poll',json={**auth,'hello':True},headers=headers)
   reply=await c.post(prefix+'complete',json={'code':p['code'],'submission':claimed['submission'],'protocol':5},headers=headers);assert reply.json()['state']=='checking'
   packet=(await c.post(prefix+'gemini-poll',json=auth,headers=headers)).json()['job'];assert packet['request']=={'operation':'identity'}
   await c.post(prefix+'gemini-result',json={**auth,'job_id':packet['id'],'result':{'ok':True}},headers=headers);await asyncio.sleep(.03)
   done=(await c.get(prefix+'pairs/'+p['id'])).json();assert done['state']=='done',done
   account=rows[done['account_id']];assert account['transport']=='browser'and account['session_verified']and selected[-1]['account_id']==account['id']
   assert not any('session' in k for k in secret),'cookie session was stored'
   # Existing Flow UI pairing still negotiates protocol 4 with the upgraded extension.
   flow=(await c.post(prefix+'pairs',json={'service':'flow','services':['flow'],'name':'Flow'})).json();flow_claim=(await c.post(prefix+'claim',json={'code':flow['code'],'protocol':5},headers=headers)).json();assert flow_claim['protocol']==4
   for task in b.tasks:task.cancel()
 print('PASS protocol5 browser pairing, exact extension Origin, no SDK/cookie import, browser account stored/selected; Flow protocol4 retained')
asyncio.run(main())
