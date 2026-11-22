"""Image entry points share the same queue, local recipe, sender and original-result importer."""
import functools,http.server,io,threading
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
buf=io.BytesIO();Image.new('RGB',(180,320),'blue').save(buf,'JPEG');output=buf.getvalue()
seed='''async()=>{storeProject=async()=>{};save=()=>{};SFProviderReceipts.persistIntent=async()=>{};const c=document.createElement('canvas');c.width=c.height=16;const image=c.toDataURL();project=blankProject();project.id='unified-frame-'+crypto.randomUUID();project.source={poster:image};project.analysis.semantic={fixture:true};project.scenes=[sceneRecord(0,4,0,[image])];window.target=project.scenes[0];target.refsUsed=[];project.script=[];window.posts=[];window.receipts={};window.reads=[];workflowLocalRequest=async(path,body)=>{if(path.endsWith('/status'))return{installed:true,models:[],selection:{available:true,token:'same'}};if(path==='gemini-chat/jobs'&&body){posts.push(structuredClone(body));return receipts[body.request_id]={state:'done',result:{mime_type:'image/jpeg',scene_id:target.id,room_id:project.id}};}if(path.startsWith('gemini-chat/jobs/')){reads.push(path);return receipts[path.split('/').at(-1)];}return {};};render();}'''
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('**/local-api/gemini-chat/files/*',lambda r:r.fulfill(body=output,content_type='image/jpeg'))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html');page.wait_for_function('window.SFFrameImages&&window.SFMediaNodes')
  # Legacy caller now uses the shared flow without a separate confirmation/sender.
  page.evaluate(seed);page.evaluate("directDialog([target],{source:'gemini-chat',regenerate:true})")
  assert page.evaluate("posts.length===1&&posts[0].kind==='image'&&target.frames.length===1")
  assert page.locator('#directSend').count()==0
  # The old picker delegates its image click to the same owner.
  page.evaluate(seed);page.evaluate('directDialog([target])');page.locator('#directPrepare').click();page.wait_for_function('target.frames.length===1&&!SFFrameImages.isRunning()')
  assert page.evaluate("posts.length===1&&posts[0].kind==='image'")
  # Compatibility preparation is local only. Explicit create emits one image, no writer.
  page.evaluate(seed);page.evaluate("SFPromptPipeline.prepareImage(target,{token:'same'})")
  assert page.evaluate('posts.length===0&&SFPromptPipeline.current(target,"image")')
  page.evaluate('SFFrameImages.create([target])');assert page.evaluate('posts.length===1&&target.frames.length===1')
  # Repeated create without regeneration reuses the unapproved matching result.
  page.evaluate('SFFrameImages.create([target])');assert page.evaluate('posts.length===1&&target.frames.length===1')
  # Automatic frame stage uses that same existing result and only performs its own review.
  page.evaluate("()=>{SFMediaNodes.checkFrame=async s=>{const f=frameV3(s);f.quality={can_quick_approve:true,sha256:f.sha256,expected_label:s.expectedLabel||''};s.localWarnings=[];};}")
  page.evaluate('SFPromptPipeline.run("frames")');assert page.evaluate('posts.length===1&&!!target.approvedFrame')
  # Optional legacy prompt button uses the same writer slot as the inspector.
  page.evaluate(seed)
  page.evaluate("""()=>{selected=0;const request=workflowLocalRequest;workflowLocalRequest=async(path,body)=>{if(path==='gemini-chat/jobs'&&body?.kind==='text'){posts.push(body);return receipts[body.request_id]={state:'done',result:{text:JSON.stringify({promptFrame:{en:'Keep the exact source composition.',vi:'Giữ đúng bố cục nguồn.'},used_refs:['R1'],warnings:[]})}};}return request(path,body);};}""")
  page.evaluate('referencePromptDialog()');page.locator('#referencePromptPrepare').click()
  page.wait_for_function('SFPromptPipeline.records().records[target.id+":image:"]?.applied&&!SFFrameImages.isRunning()')
  assert page.evaluate("posts.length===1&&posts[0].kind==='text'&&!(project.referencePromptJobs||[]).length")
  page.evaluate("()=>{const r=SFPromptPipeline.records().records[target.id+':image:'];r.applied=false;r.job.state='submitted';}")
  page.evaluate('SFFrameImages.readPrompt(target)');assert page.evaluate('posts.length===1')
  page.evaluate('SFFrameImages.create([target])');assert page.evaluate("posts.length===2&&posts[1].kind==='image'&&target.frames.length===1")
  # A second entry point cannot dispatch while the first is waiting on its image POST.
  page.evaluate(seed)
  result=page.evaluate('''async()=>{const request=workflowLocalRequest;workflowLocalRequest=async(path,body)=>{const reply=await request(path,body);if(body?.kind==='image')await new Promise(r=>window.finishShared=r);return reply;};const first=SFFrameImages.create([target]);while(!window.finishShared)await new Promise(r=>setTimeout(r,10));let blocked=false;try{await directDialog([target],{source:'gemini-chat'});}catch(e){blocked=e.message.includes('Đợi lượt ảnh');}const count=posts.length;finishShared();await first;return {blocked,count,frames:target.frames.length};}''')
  assert result=={'blocked':True,'count':1,'frames':1},result
  # Existing download error through a legacy entry receives its request; no new generation.
  page.evaluate(seed)
  page.evaluate('''async()=>{await SFFrameImages.prepare(target);const id='gchat-old';project.cloudJobs=[{id,kind:'image',provider:'gemini-chat',sceneId:target.id,part:'',signature:await directSignature(target,'','image'),state:'unknown',canReceiveImage:true,errorCode:'GEMINI_IMAGE_DOWNLOAD_ERROR'}];workflowLocalRequest=async(path,body)=>{if(path.endsWith('/status'))return{installed:true,selection:{available:false}};if(path.endsWith('/receive'))return{state:'done',result:{mime_type:'image/jpeg'}};if(body)posts.push(body);return{state:'done',result:{mime_type:'image/jpeg'}};};}''')
  page.evaluate("directDialog([target],{source:'gemini-chat'})");assert page.evaluate('posts.length===0&&target.frames.length===1&&project.cloudJobs[0].state==="imported"')
  page.evaluate('SFFrameImages.receive(target)');assert page.evaluate('posts.length===0&&target.frames.length===1')
  # An explicit old caller can import a legacy receipt only after one review confirmation.
  page.evaluate(seed)
  page.evaluate("""async()=>{await SFFrameImages.prepare(target);project.cloudJobs=[{id:'gchat-legacy',kind:'image',provider:'gemini-chat',sceneId:target.id,part:'',signature:'old-blob-dependent-hash',state:'unknown',canReceiveImage:true,errorCode:'GEMINI_IMAGE_DOWNLOAD_ERROR'}];workflowLocalRequest=async(path,body)=>{if(path.endsWith('/status'))return{installed:true,selection:{available:false}};if(body&&!path.endsWith('/receive'))posts.push(body);return{state:'done',result:{mime_type:'image/jpeg',scene_id:target.id,room_id:project.id}};};}""")
  page.once('dialog',lambda d:d.accept())
  page.evaluate("directDialog([target],{source:'gemini-chat'})")
  assert page.evaluate('posts.length===0&&target.frames.length===1&&!target.approvedFrame')
  assert not errors,errors;browser.close()
 print('PASS legacy/picker/local prepare/automatic/node share one image owner; no mandatory writer; matching result reused; concurrent entry blocked; old image received without generation or duplicate import')
finally:server.shutdown()
