"""Real Frame Studio button: new local version, original retained, no Gemini job."""
import base64,functools,http.server,io,threading
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
b=io.BytesIO();Image.new('RGB',(360,640),'red').save(b,'PNG');clean=base64.b64encode(b.getvalue()).decode()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=browser.new_page();p.goto(f'http://127.0.0.1:{server.server_port}/workflow.html');p.wait_for_function('window.SFFrameStudio&&window.SFFrameImages&&typeof project!=="undefined"&&project')
  setup=p.evaluate('''async clean=>{
   storeProject=async()=>{};save=()=>{};const canvas=document.createElement('canvas');canvas.width=360;canvas.height=640;canvas.getContext('2d').fillStyle='blue';canvas.getContext('2d').fillRect(0,0,360,640);const image=canvas.toDataURL();
   project=blankProject();project.id='watermark';project.source={poster:image};project.script=[];project.scenes=[sceneRecord(0,4,0,[image])];const s=project.scenes[0];s.refsUsed=[];
   const raw=await(await fetch(image)).blob();await addFrame(new File([raw],'original.png',{type:'image/png'}),s.id);const original=s.frames[0];window.watermarkTest={original,originalAsset:original.asset,calls:[],image:await cpuEncode(raw)};
   workflowLocalRequest=async(path,body)=>{watermarkTest.calls.push({path,body});if(path!=='gemini-chat/remove-watermark')throw Error('Unexpected provider call');await new Promise(r=>setTimeout(r,300));return{changed:true,image:clean,mime_type:'image/png',width:360,height:640};};
   await SFFrameStudio.open(s.id);return s.id;
  }''',clean)
  button=p.locator('[data-studio="remove-watermark"]');assert button.is_visible();assert button.inner_text()=='Xóa logo Gemini';button.click();p.wait_for_function('document.querySelector("[data-studio=remove-watermark]").disabled');p.evaluate('document.querySelector("[data-studio=remove-watermark]").click()');p.wait_for_function('project.scenes[0].frames.length===2')
  result=p.evaluate('''()=>{const t=watermarkTest,s=project.scenes[0],f=s.frames[1];if(t.calls.length!==1||t.calls[0].body.image!==t.image)throw Error('Wrong file or duplicate request');if(s.frames[0]!==t.original||s.frames[0].asset!==t.originalAsset||!assets.has(t.originalAsset))throw Error('Original changed');if(f.watermarkSourceId!==t.original.id||f.width!==360||f.height!==640||s.frameSelectionId!==f.id)throw Error('New version missing');if(s.approvedFrame===f.id)throw Error('Auto-approved edited image');return{versions:s.frames.length,calls:t.calls.map(c=>c.path),button:document.querySelector('[data-studio="remove-watermark"]').textContent};}''')
  p.wait_for_function('document.querySelector("[data-studio=remove-watermark]").textContent==="Đã xử lý logo"');print('PASS real UI: full original file sent once to local processing; original/version retained; cleaned version selected pending approval; no Gemini call',result);browser.close()
finally:server.shutdown()
