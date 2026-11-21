"""Read-only login readiness never captures credentials or verifies early."""
import ast,asyncio
from pathlib import Path
from types import SimpleNamespace
from fastapi import HTTPException
source=Path('veo-node-v46/local_engine/gemini_chat.py').read_text()
cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef)and n.name=='GeminiChat')
method=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef)and n.name=='login_status')
ns={'HTTPException':HTTPException};exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'status','exec'),ns)
async def main():
 state={'closed':False};context=SimpleNamespace(deferred_capture=True,process=SimpleNamespace(poll=lambda:0 if state['closed']else None))
 service=SimpleNamespace(logins={'pending':{'context':context}})
 assert await ns['login_status'](service,'pending')=={'ready_to_capture':False}
 state['closed']=True;assert await ns['login_status'](service,'pending')=={'ready_to_capture':True}
 try:await ns['login_status'](service,'missing')
 except HTTPException as e:assert e.status_code==409
 else:raise AssertionError('missing login accepted')
 print('PASS read-only native process readiness, missing login rejected')
asyncio.run(main())
