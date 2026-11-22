import asyncio,importlib.util,tempfile
from types import SimpleNamespace
from pathlib import Path
from gemini_webapi import GeneratedImage
ROOT=Path(__file__).resolve().parents[2]
import ast,re,subprocess
source=subprocess.check_output(['git','show','5a5a306:veo-node-v46/local_engine/gemini_chat_worker.py'],cwd=ROOT,text=True)
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=='error_detail')
ns={'re':re};exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'baseline-error-detail','exec'),ns)
worker=SimpleNamespace(error_detail=ns['error_detail'])
class Transport:
 def __init__(self):self.urls=[]
 async def get(self,url,**kwargs):
  self.urls.append(url);bad='=s2048-rj'in url
  return SimpleNamespace(status_code=403 if bad else 200,reason='Forbidden'if bad else'OK',content=b'original-image-bytes',http_version=2,headers={'content-type':'image/png'})
async def main():
 with tempfile.TemporaryDirectory()as d:
  t=Transport();image=GeneratedImage(url='https://lh3.googleusercontent.com/fixture=s1024-rj',title='x',alt='x')
  try:await image.save(path=d,filename='result.partial',client=t,full_size=True)
  except Exception as e:
   detail=worker.error_detail(e,'download_image');assert detail['error_type']=='HTTPError'and 'http_status'not in detail
   print('REPRO: real SDK HTTP 403 loses structured status; app cannot show it:',detail)
  else:raise AssertionError('expected full-size failure')
  assert len(t.urls)==1 and not(Path(d)/'result.partial').exists()
  path=await image.save(path=d,filename='result.partial',client=t,full_size=False)
  assert Path(path).read_bytes()==b'original-image-bytes'
  print('REPRO: same generated image has downloadable standard-size variant, while app full_size-only path stopped; no generation was sent')
asyncio.run(main())
