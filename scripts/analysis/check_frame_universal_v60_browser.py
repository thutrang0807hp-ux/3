"""Current frame owner sends V6.0 once, with current source/product bytes and no writer."""
import functools,http.server,threading,io,json
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
   const canvas=document.createElement('canvas');canvas.width=canvas.height=16;canvas.getContext('2d').fillRect(0,0,16,16);const image=canvas.toDataURL(),colored=color=>{canvas.getContext('2d').fillStyle=color;canvas.getContext('2d').fillRect(0,0,16,16);return canvas.toDataURL();},product=colored('red'),nail=colored('pink'),other=colored('yellow'),side=colored('blue'),outfit=colored('gray'),environment=colored('green');
   project=blankProject();project.id='v60-frame-send';project.source={poster:image};project.script=[];project.refs.product={images:[{id:'product',image:product,primary:true}],description:'Transparent green glass; capacity 100 ml'};
   const s=sceneRecord(0,4,0,[image]);project.refs.person={images:[{id:'side',image:side,personId:'p1'},{id:'nail',image:nail,personId:'p1',primary:true},{id:'other',image:other,personId:'p2',primary:true}],people:[{id:'p1',description:'left visible hand; nude pink nails'},{id:'p2',description:'person on the right'}],description:''};project.refs.outfit={images:[{id:'outfit',image:outfit,personId:'p2'}],description:'coat for person on the right'};project.refs.background={images:[{id:'environment',image:environment}],description:'new sunlit environment'};s.referencePeople=['p1','p2'];s.refsUsed=['product','person','outfit','background'];s.hasProduct=true;project.scenes=[s];const posts=[],replies={};
   workflowLocalRequest=async(path,body)=>{if(path.endsWith('/status'))return {installed:true,selection:{available:true,token:'v60'}};if(path==='gemini-chat/jobs'){posts.push(body);return replies[body.request_id]={state:'done',result:{mime_type:'image/jpeg',scene_id:s.id,room_id:project.id}};}if(path.startsWith('gemini-chat/jobs/'))return replies[path.split('/').at(-1)];return {};};
   await SFFrameImages.create([s]);if(posts.length!==1||posts[0].kind!=='image')throw Error('Writer/duplicate request');
   const request=posts[0];const expected=[image,product,nail,other,side,outfit,environment].map(i=>i.split(',')[1]);if(JSON.stringify(request.references.map(r=>r.data))!==JSON.stringify(expected))throw Error('Actual reference bytes/order wrong');if(!request.prompt.includes('ENVIRONMENT is active:'))throw Error('Lighting authority wrong');if(!request.prompt.includes('group=person:p1')||!request.prompt.includes('group=person:p2'))throw Error('Person groups missing');if(!request.prompt.startsWith('# UNIVERSAL REFERENCE IMAGE EDIT V6.0'))throw Error('V6.0 not sent');if(request.references.length!==7)throw Error('Reference order/count changed');if(!request.prompt.includes('R2: PRODUCT; PRIMARY'))throw Error('Primary not bound');if(!request.prompt.includes('Nail shape, length, color and nail design.')||!request.prompt.includes('visible hand; nude pink nails')||!request.prompt.trimEnd().endsWith('Return only the finished edited image.')||!request.prompt.includes('No unnecessary desaturation or oversaturation.'))throw Error('V6.0 color constraints missing');if(s.frames.length!==1)throw Error('Result not imported');
   await SFFrameImages.create([s]);if(posts.length!==1)throw Error('Matching result sent again');
   return {template:SFUniversalFrame.version,references:request.references.length,posts:posts.length,frames:s.frames.length,prompt:request.prompt,manifest:project.cloudJobs.at(-1).referenceManifest};
  }''');assert not errors,errors;(ROOT/'diagnostics/v60-prompt-audit').mkdir(parents=True,exist_ok=True);(ROOT/'diagnostics/v60-prompt-audit/actual-node-request.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('PASS',{k:v for k,v in result.items()if k not in ('prompt','manifest')});browser.close()
finally:server.shutdown()
