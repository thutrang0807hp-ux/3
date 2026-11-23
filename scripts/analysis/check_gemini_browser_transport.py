"""Real broker HTTP endpoints + actual Gemini job/import methods; simulated authenticated extension."""
import ast,asyncio,base64,hashlib,importlib.util,io,json,os,re,tempfile,time,uuid
from pathlib import Path
from types import SimpleNamespace
from contextlib import asynccontextmanager,nullcontext
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
import httpx
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('gb',ROOT/'veo-node-v46/local_engine/gemini_browser.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
@asynccontextmanager
async def slot(aid):yield
class Base:
 def lookup(self,rid):state,result=self.states[rid];return {'request_id':rid,'state':state,'result':result}
ns=dict(Base=Base,asyncio=asyncio,base64=base64,hashlib=hashlib,json=json,os=os,re=re,time=time,uuid=uuid,Image=Image,Path=Path,HTTPException=HTTPException,FileResponse=FileResponse,nullcontext=nullcontext,conversation_key=lambda room,aid:room+'|'+aid,valid_metadata=lambda v:bool(v),safe_rejection=lambda v:False)
tree=ast.parse((ROOT/'veo-node-v46/local_engine/gemini_chat.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='GeminiChat');names={'valid_id','lookup','conversation_room','run','_run','browser_generate','receive_image','file'}
exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Adapter',bases=[ast.Name(id='Base',ctx=ast.Load())],keywords=[],body=[n for n in cls.body if getattr(n,'name','')in names],decorator_list=[])],type_ignores=[])),'actual-job','exec'),ns)
async def main():
 with tempfile.TemporaryDirectory()as directory:
  secrets={};metadata={};states={};a=ns['Adapter']();a.data=Path(directory);a.root=a.data/'files';a.root.mkdir();a.tasks={};a.phases={};a.conversation_locks={};a.states=states
  a.vault=SimpleNamespace(secret=lambda k:secrets.get(k),set_secret=lambda k,v:secrets.__setitem__(k,v),put=lambda *args:None)
  a.ledger=SimpleNamespace(storage=None,metadata=lambda rid:metadata.get(rid,{}),set_metadata=lambda rid,v:metadata.setdefault(rid,{}).update(v),finish=lambda rid,state,result:states.__setitem__(rid,(state,result)))
  a.image_slots=SimpleNamespace(slot=slot,exclusive=slot,limit=lambda:1);a.lock=lambda aid:slot(aid);a.lane=slot('lane');a.pool=SimpleNamespace(eligible=lambda row:True)
  app=FastAPI();broker=m.GeminiBrowser(app,a);a.browser=broker;link=broker.issue();route=link['id'];row={'id':'browser-account','transport':'browser','browser_route':route};a.account=lambda aid:row;a.accounts=lambda:[row]
  async def forbidden(*args,**kwargs):raise AssertionError('SDK/cookies must not be used')
  a.runner=forbidden
  buf=io.BytesIO();Image.new('RGB',(108,192),'blue').save(buf,'PNG');png=buf.getvalue();encoded=base64.b64encode(png).decode()
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://127.0.0.1')as client:
   auth={'id':route,'key':link['browser_key']}
   assert (await client.post('/local-api/browser-bridge/gemini-poll',json={**auth,'key':'wrong'})).status_code==403
   await client.post('/local-api/browser-bridge/gemini-poll',json={**auth,'hello':True})
   payload=dict(kind='image',role='image',room_id='room',scene_id='scene',mode='selected',plan=[row['id']],prompt='USE SOURCE AND PRODUCT REFERENCE',references=[{'mime_type':'image/png','data':encoded}]*2,model='')
   rid='gchat-'+str(uuid.uuid4());states[rid]=('submitted',None);metadata[rid]={'room_id':'room','scene_id':'scene'}
   task=asyncio.create_task(a.run(rid,row['id'],payload));await asyncio.sleep(.01)
   packet=(await client.post('/local-api/browser-bridge/gemini-poll',json=auth)).json()['job'];assert packet['id']==rid and packet['request']['references']==payload['references']
   assert packet['request']['prompt']==payload['prompt']
   result={'ok':True,'image':encoded,'mime':'image/png'}
   assert (await client.post('/local-api/browser-bridge/gemini-result',json={**auth,'job_id':rid,'result':result})).status_code==200
   await task;assert states[rid][0]=='done';assert Path(a.file(rid).path).read_bytes()==png;assert states[rid][1]['scene_id']=='scene'and states[rid][1]['download_variant']=='browser-authenticated'
   # Existing result is idempotent across receive and broker restart; no new prompt.
   a.browser=m.GeminiBrowser(FastAPI(),a);assert a.browser.read(rid)is None
   assert (await a.receive_image(rid,{}))['state']=='done'
   assert a.browser.jobs[rid]['completed']
   assert (await client.post('/local-api/browser-bridge/gemini-result',json={**auth,'job_id':rid,'result':result})).status_code==200
   assert (await client.post('/local-api/browser-bridge/gemini-result',json={**auth,'job_id':rid,'result':{'ok':False}})).status_code==409
   # Attachment failure is proof no Gemini prompt was sent, so don't offer a phantom image Receive.
   a.browser=broker
   blocked='gchat-'+str(uuid.uuid4());states[blocked]=('submitted',None);metadata[blocked]={'room_id':'room','scene_id':'scene'}
   pending=asyncio.create_task(a.run(blocked,row['id'],payload));await asyncio.sleep(.01)
   no_send=(await client.post('/local-api/browser-bridge/gemini-poll',json=auth)).json()['job']
   await client.post('/local-api/browser-bridge/gemini-result',json={**auth,'job_id':blocked,'result':{'ok':False,'accepted':False,'code':'GEMINI_BROWSER_ATTACH_FAILED'}});await pending
   assert states[blocked][0]=='failed'and not a.lookup(blocked).get('can_receive_image')
   assert 'prompt'not in json.dumps(metadata)and 'USE SOURCE'not in json.dumps(secrets)
   # Transfer failed after generation: receive targets the original browser turn only.
   a.browser=broker;old='gchat-'+str(uuid.uuid4());states[old]=('submitted',None);metadata[old]={'room_id':'room','scene_id':'scene'}
   task=asyncio.create_task(a.run(old,row['id'],payload));await asyncio.sleep(.01);job=(await client.post('/local-api/browser-bridge/gemini-poll',json=auth)).json()['job']
   await client.post('/local-api/browser-bridge/gemini-result',json={**auth,'job_id':old,'result':{'ok':False,'accepted':True,'code':'GEMINI_BROWSER_TRANSFER_FAILED'}});await task;assert states[old][0]=='unknown'
   receiving=await a.receive_image(old,{});assert receiving['state']=='downloading';await asyncio.sleep(.01);recovery=(await client.post('/local-api/browser-bridge/gemini-poll',json=auth)).json()['job']
   assert recovery['request']=={'operation':'receive','target_job':old,'kind':'image'}
   assert 'prompt'not in recovery['request']and 'references'not in recovery['request']
   await client.post('/local-api/browser-bridge/gemini-result',json={**auth,'job_id':recovery['id'],'result':result});await a.tasks[old];assert states[old][0]=='done'and Path(a.file(old).path).read_bytes()==png
 print('PASS browser route auth; exact prompt + source/product refs; real PNG imported into original scene via existing job path; SDK never called; cached/restarted receipt idempotent; receive reads original turn without generation')
asyncio.run(main())
