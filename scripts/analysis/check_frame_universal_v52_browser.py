"""Current frame owner sends V5.2 once, with current source/product bytes and no writer."""
import functools,http.server,threading,io
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
buf=io.BytesIO();Image.new('RGB',(180,320),'blue').save(buf,'JPEG');jpeg=buf.getvalue()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e.stack)))
  page.route('**/local-api/gemini-chat/files/*',lambda r:r.fulfill(body=jpeg,content_type='image/jpeg'))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html');page.wait_for_function('window.SFFrameImages&&window.SFUniversalFrame&&typeof project!=="undefined"&&project');errors.clear()  # Scope this test to prompt/send after existing async bootstrap.
  result=page.evaluate('''async()=>{
   storeProject=async()=>{};save=()=>{};SFProviderReceipts.persistIntent=async()=>{};
   const canvas=document.createElement('canvas');canvas.width=canvas.height=16;canvas.getContext('2d').fillRect(0,0,16,16);const image=canvas.toDataURL();
   project=blankProject();project.id='v52-frame-send';project.source={poster:image};project.script=[];project.refs.product={images:[{id:'product',image,primary:true}],description:'Transparent green glass; capacity 100 ml'};
   const s=sceneRecord(0,4,0,[image]);s.refsUsed=['product'];s.hasProduct=true;project.scenes=[s];const posts=[],replies={};
   workflowLocalRequest=async(path,body)=>{if(path.endsWith('/status'))return {installed:true,selection:{available:true,token:'v52'}};if(path==='gemini-chat/jobs'){posts.push(body);return replies[body.request_id]={state:'done',result:{mime_type:'image/jpeg',scene_id:s.id,room_id:project.id}};}if(path.startsWith('gemini-chat/jobs/'))return replies[path.split('/').at(-1)];return {};};
   await SFFrameImages.create([s]);if(posts.length!==1||posts[0].kind!=='image')throw Error('Writer/duplicate request');
   const request=posts[0];if(!request.prompt.startsWith('# UNIVERSAL REFERENCE IMAGE EDIT V5.2'))throw Error('V5.2 not sent');if(request.references.length!==2)throw Error('Reference order/count changed');if(!request.prompt.includes('R2: replacement product (PRIMARY PRODUCT)'))throw Error('Primary not bound');if(!request.prompt.includes('No unnecessary desaturation or oversaturation.'))throw Error('V5.2 color constraints missing');if(s.frames.length!==1)throw Error('Result not imported');
   await SFFrameImages.create([s]);if(posts.length!==1)throw Error('Matching result sent again');
   return {template:SFUniversalFrame.version,references:request.references.length,posts:posts.length,frames:s.frames.length};
  }''');assert not errors,errors;print('PASS',result);browser.close()
finally:server.shutdown()
