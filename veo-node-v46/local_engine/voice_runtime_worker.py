"""Private stdio worker: retain one offline CPU model between explicit requests."""
import argparse,contextlib,json,os,sys
from pathlib import Path
from voice_worker import load_model,synthesize

def serve(runtime,source,sink):
 model=None
 for line in source:
  try:
   request=json.loads(line);nonce=request['nonce']
   with contextlib.redirect_stdout(sys.stderr):
    if model is None:model=load_model(runtime)
    body=json.loads(Path(request['request']).read_text(encoding='utf-8'))
    result=synthesize(model,body['beats'],body.get('voice'),Path(request['output']),Path(request['request']).parent)
    Path(request['result']).write_text(json.dumps(result),encoding='utf-8')
   reply={'nonce':nonce,'ok':True}
  except Exception:
   reply={'nonce':request.get('nonce') if isinstance(locals().get('request'),dict) else None,'ok':False}
  sink.write(json.dumps(reply)+'\n');sink.flush()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);a=p.parse_args()
 os.environ['HF_HOME']=str(a.runtime/'hf-cache');os.environ['HF_HUB_DISABLE_XET']='1';os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
 # Native ONNX/SDK code can write directly to fd 1, bypassing redirect_stdout.
 # Keep a private duplicate for replies, and send all library stdout to stderr.
 sink=os.fdopen(os.dup(sys.stdout.fileno()),'w',buffering=1,encoding='utf-8')
 os.dup2(sys.stderr.fileno(),sys.stdout.fileno())
 serve(a.runtime,sys.stdin,sink)
