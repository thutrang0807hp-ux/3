"""Direct image creation skips even a pending text writer; preserves references and receipts."""
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
   page.evaluate("""()=>{const s=target;project.productScript={brief:{name:'Cloud Mountain Series No.5',facts:'Real product facts'}};project.promptPipeline={version:1,records:{[s.id+':image:']:{input:'old-input',applied:false,job:{id:'old-writer-pending',sceneId:s.id,stage:'image',provider:'gemini-chat',state:'submitted'}}},run:null};receipts['old-writer-pending']={state:'running'};}""")
   page.evaluate('SFMediaNodes.open("frame",target.id)')
   page.evaluate('''()=>{const request=workflowLocalRequest;workflowLocalRequest=async(path,body)=>{const reply=await request(path,body);if(body?.kind==='image')await new Promise(resolve=>window.finishImage=resolve);return reply;};}''')
   page.locator('[data-mn=create-product-frame]').click()
   page.wait_for_function('typeof finishImage==="function"')
   assert page.locator('#modal').is_visible()
   assert page.locator('[data-mn=create-product-frame]').is_disabled()
   assert page.evaluate('posts.length')==1
   page.evaluate('finishImage()')
   page.wait_for_function('!SFPromptPipeline.isRunning()&&target.frames.length===1')
   assert page.locator('#modal').is_visible()
   result=page.evaluate("""()=>{const r=SFPromptPipeline.records().records[target.id+':image:'],old=SFPromptPipeline.records().history.find(x=>x.job?.id==='old-writer-pending');return{writer:posts.filter(x=>x.kind==='text').length,image:posts.filter(x=>x.kind==='image').length,refs:posts[0]?.references.length,prompt:posts[0]?.prompt,oldState:old?.job.state,local:r.localRecipe,width:target.sourceFrame.width,approved:target.approvedFrame};}""")
   assert result['writer']==0 and result['image']==1 and result['refs']==2 and result['oldState']=='submitted' and result['local'] and result['width']==180 and not result['approved'],result
   assert 'Cloud Mountain Series No.5' not in result['prompt']
   assert page.evaluate('project.productScript.brief.name')=='Cloud Mountain Series No.5'
   packed=page.evaluate("async()=>{const p=await SFPromptPipeline.pack(target,'image');return p.prompt}")
   assert 'Cloud Mountain Series No.5' not in packed and 'visual_name_policy' in packed
   assert 'PRODUCT LOCK' in result['prompt'] and 'R2' in result['prompt'] and 'lighting' in result['prompt']
   page.evaluate('SFMediaNodes.open("frame",target.id)')
   page.locator('[data-frame-technical] > summary').click()
   assert 'Đã gửi · chờ phản hồi' in page.locator('[data-frame-inspector-progress]').inner_text()
   page.locator('[data-mn=frame-inspector-refresh]').click()
   page.wait_for_function('!target.frameInspectorCheck.busy')
   assert page.evaluate('posts.length')==1
   # An unresolved image receipt must block a new image, independent of writer state.
   page.evaluate("""()=>{target.promptRevision={image:'Giữ nhãn thật'};receipts['image-pending']={state:'unknown',message:'Lượt ảnh cũ chưa rõ; kiểm tra trước khi gửi mới.'};project.cloudJobs.push({id:'image-pending',kind:'image',provider:'gemini-chat',sceneId:target.id,state:'submitted'});} """)
   blocked=page.evaluate("""async()=>{try{await SFPromptPipeline.runImages([target],{regenerate:true});return false}catch(e){return e.message.includes('Lượt ảnh cũ')&&posts.length===1}}""");assert blocked
   page.evaluate("project.cloudJobs.at(-1).state='not_submitted'")
   repaired=page.evaluate('''async()=>{const versions=target.frames.length;target.sourceFrame={id:'source',image:target.thumbs[0]};target.frameSelectionId='source';const old=HTMLCanvasElement.prototype.toBlob;HTMLCanvasElement.prototype.toBlob=function(cb){cb(null)};try{const [a,b]=await Promise.all([SFFrameCapture.source(target),SFFrameCapture.source(target)]);if(a!==b)throw Error('Duplicate capture');return {engine:a.captureEngine,width:a.width,height:a.height,versions:target.frames.length,originalVersions:versions};}finally{HTMLCanvasElement.prototype.toBlob=old;}}''')
   assert repaired['engine']=='ffmpeg'and repaired['width']==180 and repaired['height']==320 and repaired['versions']==repaired['originalVersions']==1 and len(fallback)==1,repaired
   retained=page.evaluate("""async()=>{target.referenceRoleOverrides={product:false};await SFPromptPipeline.prepareFrameDirect(target);const text=SFPromptPipeline.records().records[target.id+':image:'].result.promptFrame.en;if(text.includes('PRODUCT LOCK:'))throw Error('Explicit product opt-out ignored');target.framePromptOverride='MY EXACT MANUAL FRAME PROMPT';if(!imageFramePrompt(target).includes(target.framePromptOverride))throw Error('Manual prompt lost');delete target.framePromptOverride;return posts.length===1;}""");assert retained
   stopped=page.evaluate('''async()=>{target.sourceFrame=null;const use=useVideo;let release;useVideo=()=>new Promise(r=>release=r);const pending=SFFrameCapture.source(target);SFPromptPipeline.pause();let stopped=false;try{await pending}catch(e){stopped=e.message.includes('dừng')};release(assets.get(target.frames[0].asset));await new Promise(r=>setTimeout(r,30));useVideo=use;return stopped&&!target.sourceFrame&&target.frames.length===1;}''');assert stopped
   assert not errors,errors;print('PASS direct frame: zero text POST, one image POST, actual source + product, pending writer retained/readable, pending image blocks duplicate, fallback and old versions preserved')
   browser.close()
finally:server.shutdown()
