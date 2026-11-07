"""Generate preset previews once in the isolated SDK process, loading the model once."""
import argparse,hashlib,json,os
from pathlib import Path
from voice_worker import load_model,synthesize
TEXT='Xin chào, đây là giọng đọc thử cho video của bạn.'
def prepare(model,voices,output):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 for voice in voices:
  filename=hashlib.sha256(voice.encode()).hexdigest()+'.wav';path=output/filename
  marker=path.with_suffix('.json')
  if marker.is_file() and path.is_file():
   try:
    saved=json.loads(marker.read_text());
    if saved.get('sha256')==hashlib.sha256(path.read_bytes()).hexdigest():continue
   except (OSError,ValueError):pass
  result=synthesize(model,[{'id':'sample','text':TEXT}],voice,path,output)
  tmp=marker.with_suffix('.tmp');tmp.write_text(json.dumps({'id':voice,**result}),encoding='utf-8');os.replace(tmp,marker)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--voices',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 os.environ['HF_HOME']=str(a.runtime/'hf-cache');os.environ['HF_HUB_DISABLE_XET']='1';os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
 prepare(load_model(a.runtime),json.loads(a.voices.read_text(encoding='utf-8')),a.output)
