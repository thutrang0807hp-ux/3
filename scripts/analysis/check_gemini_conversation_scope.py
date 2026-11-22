"""Exercise real adapter dispatch methods: explicit scope bypasses a stale cursor, never resets it."""
import ast,asyncio,hashlib,json,tempfile,time,os,re,uuid
from pathlib import Path
from types import SimpleNamespace
from contextlib import nullcontext,asynccontextmanager
from PIL import Image
from fastapi import HTTPException
src=Path('veo-node-v46/local_engine/gemini_chat.py').read_text();tree=ast.parse(src);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='GeminiChat')
methods=[n for n in cls.body if getattr(n,'name','')in ('conversation_room','run','_run')]
code=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Adapter',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[]))
ns=dict(asyncio=asyncio,hashlib=hashlib,json=json,time=time,os=os,Image=Image,conversation_key=lambda room,aid:room+'|'+aid,valid_metadata=lambda m:isinstance(m,list)and bool(m),safe_rejection=lambda r:False,nullcontext=nullcontext)
exec(compile(code,'actual-adapter','exec'),ns);Adapter=ns['Adapter']
@asynccontextmanager
async def slot(aid):yield
async def test():
 with tempfile.TemporaryDirectory()as folder:
  a=Adapter();a.root=Path(folder);a.conversation_locks={};a.phases={};a.image_slots=SimpleNamespace(slot=slot,limit=lambda:1);a.pool=SimpleNamespace(eligible=lambda row:True);a.accounts=lambda:[{'id':'account'}]
  secrets={'room|account':{'state':'unknown','request_id':'old','metadata':['old-chat']}}
  a.vault=SimpleNamespace(secret=lambda k:secrets.get(k),set_secret=lambda k,v:secrets.__setitem__(k,v),put=lambda *args:None)
  states={};metadata={};a.ledger=SimpleNamespace(set_metadata=lambda rid,row:metadata.setdefault(rid,{}).update(row),finish=lambda rid,state,result:states.__setitem__(rid,(state,result)))
  calls=[]
  async def runner(body):
   calls.append(body);Image.new('RGB',(16,16)).save(body['output'],format='PNG');return {'ok':True,'conversation':{'metadata':['new-chat']}}
  a.runner=runner
  base=dict(kind='image',role='image',room_id='room',scene_id='scene',mode='selected',prompt='same prompt',references=[],model='')
  await a.run('blocked','account',base)
  assert not calls and metadata['blocked']['last_error_code']=='CHAT_TURN_UNRESOLVED'
  scoped={**base,'conversation_scope':str(uuid.uuid4())};await a.run('new','account',scoped)
  assert states['new'][0]=='done'and states['new'][1]['room_id']=='room'and len(calls)==1
  assert secrets['room|account']=={'state':'unknown','request_id':'old','metadata':['old-chat']}
  key=a.conversation_room(scoped)+'|account';assert secrets[key]['state']=='ready'
  await a.run('next','account',scoped);assert calls[1]['conversation']['metadata']==['new-chat']
  assert a.conversation_room(base)=='room'and a.conversation_room({**scoped,'room_id':'other'})!=a.conversation_room(scoped)
  # Run actual validation statements before ledger claim, with valid and malformed input.
  submit=next(n for n in cls.body if getattr(n,'name','')=='submit');start=next(i for i,n in enumerate(submit.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='scope'for t in n.targets));guard=compile(ast.fix_missing_locations(ast.Module(body=submit.body[start:start+2],type_ignores=[])),'actual-scope-validation','exec')
  for scope,kind,valid in [(None,'image',True),(scoped['conversation_scope'],'image',True),('bad','image',False),(scoped['conversation_scope'],'text',False)]:
   payload={};env=dict(body={'conversation_scope':scope,'kind':kind},payload=payload,uuid=uuid,re=re,HTTPException=HTTPException)
   try:exec(guard,env)
   except HTTPException as e:assert not valid and e.status_code==400
   else:assert valid and ('conversation_scope'in payload)==(scope is not None)
asyncio.run(test());print('PASS actual adapter: stale default cursor blocks; explicit scoped retry dispatches and resumes new cursor; original cursor/room unchanged; invalid scopes rejected')
