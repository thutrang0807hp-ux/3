"""Real adapter methods: failed download survives restart and receives same request, no regeneration."""
import ast,asyncio,hashlib,json,os,re,tempfile,time,uuid
from pathlib import Path
from types import SimpleNamespace
from contextlib import asynccontextmanager,nullcontext
from fastapi import HTTPException
from fastapi.responses import FileResponse
from PIL import Image
source=ast.parse(Path('veo-node-v46/local_engine/gemini_chat.py').read_text());cls=next(n for n in source.body if isinstance(n,ast.ClassDef)and n.name=='GeminiChat')
names={'valid_id','lookup','conversation_room','run','_run','receive_image','_receive_image','file'}
class Base:
 def lookup(self,rid):
  state,result=self.states[rid];return {'request_id':rid,'state':state,'result':result}
ns=dict(Base=Base,asyncio=asyncio,hashlib=hashlib,json=json,os=os,re=re,time=time,uuid=uuid,Image=Image,HTTPException=HTTPException,FileResponse=FileResponse,nullcontext=nullcontext,conversation_key=lambda room,aid:room+'|'+aid,valid_metadata=lambda m:isinstance(m,list)and len(m)>1,safe_rejection=lambda r:False)
exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Adapter',bases=[ast.Name(id='Base',ctx=ast.Load())],keywords=[],body=[n for n in cls.body if getattr(n,'name','')in names],decorator_list=[])],type_ignores=[])),'actual-adapter','exec'),ns);Adapter=ns['Adapter']
@asynccontextmanager
async def slot(aid):yield
async def main():
 with tempfile.TemporaryDirectory()as d:
  secrets={};metadata={};states={};calls=[]
  def fresh():
   a=Adapter();a.root=Path(d);a.tasks={};a.phases={};a.conversation_locks={};a.states=states;a.require_sdk=lambda:None
   a.lock=lambda key:a.conversation_locks.setdefault(key,asyncio.Lock())
   a.image_slots=SimpleNamespace(slot=slot,limit=lambda:1);a.pool=SimpleNamespace(eligible=lambda row:True);a.accounts=lambda:[{'id':'account'}];a.account=lambda aid:{'id':aid}
   a.vault=SimpleNamespace(secret=lambda key:secrets.get(key),set_secret=lambda key,v:secrets.__setitem__(key,v),put=lambda *args:None)
   a.ledger=SimpleNamespace(storage=None,metadata=lambda rid:metadata.get(rid,{}),set_metadata=lambda rid,v:metadata.setdefault(rid,{}).update(v),finish=lambda rid,state,result:states.__setitem__(rid,(state,result)))
   async def runner(body):
    calls.append(body['operation'])
    if body['operation']=='generate':return {'ok':False,'accepted':None,'code':'GEMINI_IMAGE_DOWNLOAD_ERROR','conversation':{'metadata':['c_original','r_original','rc_original']},'image_result':{'metadata':['c_original','r_original','rc_original'],'image':{'url':'https://lh3.googleusercontent.com/private-original'}}}
    assert body['operation']=='receive_image'and 'prompt'not in body and 'references'not in body
    Image.new('RGB',(180,320),'blue').save(body['output'],format='PNG')
    return {'ok':True,'download_variant':'standard'}
   a.runner=runner;return a
  a=fresh();rid='gchat-'+str(uuid.uuid4());metadata[rid]={'room_id':'room','scene_id':'scene','kind':'image'};states[rid]=('submitted',None)
  await a.run(rid,'account',dict(kind='image',role='image',room_id='room',scene_id='scene',mode='selected',prompt='one generation',references=[],model=''))
  assert states[rid][0]=='unknown'and a.lookup(rid)['can_receive_image']
  assert secrets['gemini-image-result:'+rid]['image_result']['image']['url'].endswith('private-original')
  assert 'private-original'not in json.dumps(metadata),'signed URL leaked to ledger metadata'
  # Simulate restarting the adapter with its original durable vault/ledger.
  a=fresh();reply=await a.receive_image(rid,{});assert reply['state']=='downloading'
  await a.receive_image(rid,{}) # double click reuses the task
  await a.tasks[rid];await asyncio.sleep(0)
  out=a.lookup(rid);assert out['state']=='done'and out['result']['received_existing_image']
  assert out['result']['width']==180 and out['result']['download_variant']=='standard'
  assert Path(a.file(rid).path).is_file()
  assert calls==['generate','receive_image'],calls
  # Legacy .151 request: recover only if the retained cursor belongs to this exact ID.
  old='gchat-'+str(uuid.uuid4());states[old]=('unknown',None);metadata[old]={'room_id':'legacy','scene_id':'scene','last_error_code':'GEMINI_IMAGE_DOWNLOAD_ERROR'}
  secrets['legacy|account']={'request_id':old,'metadata':['c_old','r_old','rc_old']}
  await a.receive_image(old,{});await a.tasks[old];await asyncio.sleep(0);assert states[old][0]=='done'
  bad='gchat-'+str(uuid.uuid4());states[bad]=('unknown',None);metadata[bad]={'room_id':'legacy'}
  try:await a.receive_image(bad,{})
  except HTTPException as e:assert e.status_code==409
  else:raise AssertionError('wrong old cursor accepted')
 print('PASS one generation -> download failure -> adapter restart -> same request received as real image; double click deduped; exact legacy cursor only; no signed URL in plain ledger')
asyncio.run(main())
