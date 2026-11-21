"""Check actual pre-dispatch guards report independent actionable failures."""
import ast
from pathlib import Path
from fastapi import HTTPException
source=Path('veo-node-v46/local_engine/gemini_chat.py').read_text();tree=ast.parse(source)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='GeminiChat');submit=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef)and n.name=='submit')
guards=[n for n in submit.body if isinstance(n,ast.If)and any(t in ast.unparse(n.test)for t in ('size >','len(self.tasks)','selection[\'available\']'))]
assert len(guards)==3
code=compile(ast.fix_missing_locations(ast.Module(body=guards,type_ignores=[])),'actual-guards','exec')
from types import SimpleNamespace
for size,count,available,status,fragment in [(25*1024**2,0,True,413,'24 MB'),(0,30,True,409,'30 việc'),(0,0,False,409,'Chưa có tài khoản')]:
 try:exec(code,{'size':size,'self':SimpleNamespace(tasks=[None]*count),'selection':{'available':available},'HTTPException':HTTPException})
 except HTTPException as e:assert e.status_code==status and fragment in e.detail and 'Chưa gửi'in e.detail
 else:raise AssertionError('Guard did not reject')
exec(code,{'size':0,'self':SimpleNamespace(tasks=[]),'selection':{'available':True},'HTTPException':HTTPException})
print('PASS no-account, oversize and queue-full are distinct before claim/dispatch; valid text request passes')
