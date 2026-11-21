"""Backend owns Gemini capture independently of any settings dialog."""
import ast,asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from fastapi import HTTPException
source=Path('veo-node-v46/local_engine/gemini_chat.py').read_text();cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef)and n.name=='GeminiChat')
methods=[n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))and n.name in ('web_login_status','watch_login','login_status','confirm','cancel_login')]
ns={'asyncio':asyncio,'HTTPException':HTTPException};exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Service',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[])),'backend','exec'),ns)
async def main():
 s=ns['Service']();closed=False
 context=SimpleNamespace(deferred_capture=True,process=SimpleNamespace(poll=lambda:0 if closed else None),cookies=AsyncMock(return_value=[]))
 s.logins={'pending':{'context':context,'name':'Gemini','browser':SimpleNamespace(close=AsyncMock()),'pw':SimpleNamespace(stop=AsyncMock())}};s.login_locks={'pending':asyncio.Lock()};s.login_results={'pending':{'id':'pending','state':'waiting'}};s.login_tasks={};s.import_session=AsyncMock(return_value={'id':'verified'})
 task=asyncio.create_task(s.watch_login('pending'));s.login_tasks['pending']=task
 await asyncio.sleep(.01);context.cookies.assert_not_called();closed=True;await asyncio.wait_for(task,2)
 assert (await s.login_status('pending'))['state']=='done';s.import_session.assert_awaited_once()
 assert await s.confirm({'id':'pending'})=={'id':'verified'};s.import_session.assert_awaited_once()
 # Failure retains login for an explicit retry, no automatic loop.
 s.logins['failed']={'context':context,'name':'Gemini','browser':SimpleNamespace(close=AsyncMock()),'pw':SimpleNamespace(stop=AsyncMock())};s.login_locks['failed']=asyncio.Lock();s.import_session.side_effect=HTTPException(409,'verification failed')
 await s.watch_login('failed');assert s.login_results['failed']['state']=='failed'and 'failed'in s.logins
 s.import_session.side_effect=None;await s.confirm({'id':'failed'});assert s.login_results['failed']['state']=='done'
 print('PASS backend capture survives absent UI, waits for close, commits once, failure retained and explicit retry succeeds')
asyncio.run(main())
