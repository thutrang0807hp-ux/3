"""Actual offline wrapper: original preservation, no-mark and invalid/error paths."""
import base64,importlib.util,io,subprocess,tempfile
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
from fastapi import HTTPException
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('watermark',ROOT/'veo-node-v46/local_engine/gemini_watermark.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
b=io.BytesIO();Image.new('RGB',(360,640),'blue').save(b,'PNG');raw=b.getvalue();encoded=base64.b64encode(raw).decode();calls=[]
def good(args,**kw):
 calls.append(args);folder=Path(kw['cwd']);assert (folder/args[2]).is_file();assert args[1::2]==['--input','--output']
 Image.new('RGB',(360,640),'red').save(folder/args[4],'PNG');return SimpleNamespace(returncode=0)
r=m.process(encoded,runner=good);assert r['changed']and(r['width'],r['height'])==(360,640);assert base64.b64decode(r['image'])!=raw;assert len(calls)==1
r=m.process(encoded,runner=lambda *a,**k:SimpleNamespace(returncode=1));assert not r['changed']and'image'not in r
for bad in [None,'bad base64','a'*100]:
 try:m.process(bad,runner=good);raise AssertionError('invalid input accepted')
 except HTTPException as e:assert e.status_code==400
def wrong(args,**kw):Image.new('RGB',(10,10)).save(Path(kw['cwd'])/args[4],'PNG');return SimpleNamespace(returncode=0)
def timeout(*args,**kw):raise subprocess.TimeoutExpired('fixture',30)
for runner in [wrong,timeout,lambda *a,**k:SimpleNamespace(returncode=2)]:
 try:m.process(encoded,runner=runner);raise AssertionError('bad tool result accepted')
 except HTTPException as e:assert e.status_code==502
assert raw==base64.b64decode(encoded)
print('PASS wrapper uses local fixed tool, full size retained, original bytes untouched, not-found returns unchanged, invalid input/dimensions/tool error/timeout handled')
