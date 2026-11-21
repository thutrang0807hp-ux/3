"""Reproduce missing product attachment and empty browser capture, without live AI."""
import functools,http.server,threading,tempfile,subprocess,base64,io
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with tempfile.TemporaryDirectory()as folder:
  video=Path(folder)/'source.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=180x320:r=24','-t','3','-c:v','libx264','-pix_fmt','yuv420p',str(video)],check=True)
  buf=io.BytesIO();Image.new('RGB',(180,320),'blue').save(buf,'JPEG');jpeg=buf.getvalue();fallback=[]
  with sync_playwright()as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1450,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.route('**/frame-source.mp4',lambda r:r.fulfill(body=video.read_bytes(),content_type='video/mp4'))
   page.route('**/local-api/gemini-chat/files/*',lambda r:r.fulfill(body=jpeg,content_type='image/jpeg'))
   def native(route):
    assert route.request.post_data_buffer==video.read_bytes();assert route.request.headers['x-frame-time']=='1.4';fallback.append(1);route.fulfill(body=jpeg,content_type='image/jpeg')
   page.route('**/local-api/analysis/frame-capture',native)
   page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html');page.wait_for_function('window.SFFrameRefs&&window.SFFrameCapture')
   page.evaluate('''async()=>{storeProject=async()=>{};save=()=>{};window.posts=[];window.receipts={};workflowLocalRequest=async(path,body)=>{if(path.endsWith('/status'))return{installed:true,models:[],selection:{available:true,token:'fixture'}};if(path==='gemini-chat/jobs'&&body){posts.push(structuredClone(body));return receipts[body.request_id]={state:'done',result:body.kind==='text'?{text:JSON.stringify({promptFrame:{en:'Replace the product using R2; preserve the source camera and lighting.',vi:'Thay sản phẩm theo R2, giữ bố cục và ánh sáng.'},used_refs:['R1','R2'],warnings:[]})}:{mime_type:'image/jpeg'}};}if(path.startsWith('gemini-chat/jobs/'))return receipts[path.split('/').at(-1)];throw Error('Unexpected route '+path);};
    const c=document.createElement('canvas');c.width=c.height=16;c.getContext('2d').fillStyle='red';c.getContext('2d').fillRect(0,0,16,16);const thumbnail=c.toDataURL();const file=await(await fetch('/frame-source.mp4')).blob();project=blankProject();project.id='repair-frame';project.source={asset:'source',duration:3,width:180,height:320,poster:thumbnail};assets.set('source',file);project.refs.product={images:[{id:'product1',name:'Sản phẩm của tôi',image:thumbnail}],description:'Replacement product'};window.target=sceneRecord(0,2.8,0,[thumbnail]);target.hasProduct=false;target.refsUsed=[];project.scenes=[target];render();}''')
   assert page.evaluate('refsFor(target).includes("product")')
   page.evaluate('SFMediaNodes.open("frame",target.id)')
   result=page.evaluate('''async()=>{await SFPromptPipeline.rewriteImage(target);if(posts.length!==1||posts[0].kind!=='text'||posts[0].references.length!==2)throw Error('Writer attachment mismatch');if(target.sourceFrame.width!==180||target.sourceFrame.height!==320)throw Error('Writer used thumbnail');const packed=await SFPromptPipeline.pack(target,'image');if(packed.bindings[1].role!=='product')throw Error('Product binding missing');await SFPromptPipeline.runImages([target],{regenerate:true});return {writer:posts.filter(x=>x.kind==='text').length,image:posts.filter(x=>x.kind==='image').length,frames:target.frames.length,approved:target.approvedFrame,receipt:project.cloudJobs.at(-1).state};}''')
   assert result['writer']==1 and result['image']==1 and result['frames']==1 and not result['approved']and result['receipt']=='imported',result
   repaired=page.evaluate('''async()=>{const versions=target.frames.length;target.sourceFrame={id:'source',image:target.thumbs[0]};target.frameSelectionId='source';const old=HTMLCanvasElement.prototype.toBlob;HTMLCanvasElement.prototype.toBlob=function(cb){cb(null)};try{const [a,b]=await Promise.all([SFFrameCapture.source(target),SFFrameCapture.source(target)]);if(a!==b)throw Error('Duplicate capture');return {engine:a.captureEngine,width:a.width,height:a.height,versions:target.frames.length,originalVersions:versions};}finally{HTMLCanvasElement.prototype.toBlob=old;}}''')
   assert repaired['engine']=='ffmpeg'and repaired['width']==180 and repaired['height']==320 and repaired['versions']==repaired['originalVersions']==1 and len(fallback)==1,repaired
   unknown=page.evaluate('''async()=>{const r=SFPromptPipeline.records().records[target.id+':image:'];r.job.state='unknown';r.applied=false;receipts[r.job.id]={state:'running'};const n=posts.length;try{await SFPromptPipeline.rewriteImage(target);return false}catch(e){return posts.length===n&&target.frames.length===1}}''');assert unknown
   stopped=page.evaluate('''async()=>{target.sourceFrame=null;const use=useVideo;let release;useVideo=()=>new Promise(r=>release=r);const pending=SFFrameCapture.source(target);SFPromptPipeline.pause();let stopped=false;try{await pending}catch(e){stopped=e.message.includes('dừng')};release(assets.get(target.frames[0].asset));await new Promise(r=>setTimeout(r,30));useVideo=use;return stopped&&!target.sourceFrame&&target.frames.length===1;}''');assert stopped
   assert not errors,errors;print('PASS automatic shared product references without scene wiring; one writer -> one image -> imported unapproved version; full-size source; empty-canvas FFmpeg fallback deduped; versions preserved',result,repaired)
   browser.close()
finally:server.shutdown()
