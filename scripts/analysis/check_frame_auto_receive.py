"""Actual UI: one generation, failed transfer, reload with new blob URL, receive original bytes."""
import base64,functools,http.server,io,threading
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
buf=io.BytesIO();Image.new('RGB',(180,320),'blue').save(buf,'JPEG');output=buf.getvalue()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('**/local-api/gemini-chat/files/*',lambda r:r.fulfill(body=output,content_type='image/jpeg'))
  url=f'http://127.0.0.1:{server.server_port}/workflow.html';page.goto(url);page.wait_for_function('window.SFPromptPipeline&&window.SFMediaNodes')
  page.evaluate('''async()=>{storeProject=async()=>{};SFProviderReceipts.persistIntent=async()=>{};window.posts=[];window.receives=0;const c=document.createElement('canvas');c.width=c.height=16;const image=c.toDataURL();project=blankProject();project.id='auto-receive';project.source={poster:image};project.scenes=[sceneRecord(0,4,0,[image])];const s=project.scenes[0];s.refsUsed=[];s.sourceFrame={id:'source',asset:'fixed-source',image};assets.set('fixed-source',await(await fetch(image)).blob());
   workflowLocalRequest=async(path,body)=>{if(path.endsWith('/status'))return{installed:true,selection:{available:true,token:'same'}};if(path.endsWith('/receive')){receives++;return{state:'unknown',can_receive_image:true,code:'GEMINI_IMAGE_DOWNLOAD_ERROR',message:'Transfer failed'};}if(body){posts.push(body);}return{state:'unknown',can_receive_image:true,code:'GEMINI_IMAGE_DOWNLOAD_ERROR',message:'Transfer failed'};};render();SFMediaNodes.open('frame',s.id);}''')
  page.locator('[data-mn=create-product-frame]').click();page.wait_for_function('posts.length===1&&receives===1&&!SFPromptPipeline.isRunning()')
  assert page.evaluate('project.scenes[0].frames.length')==0
  original=page.evaluate('mediaUrl("fixed-source")');state=page.evaluate('JSON.stringify(project)');signature=page.evaluate('project.cloudJobs[0].signature')
  assert signature.startswith('sf-image-v2:')
  page.reload();page.wait_for_function('window.SFPromptPipeline&&window.SFMediaNodes')
  page.evaluate('''async data=>{project=JSON.parse(data);storeProject=async()=>{};SFProviderReceipts.persistIntent=async()=>{};const s=project.scenes[0];assets.set('fixed-source',await(await fetch(s.sourceFrame.image)).blob());window.posts=[];window.receives=0;window.ready=false;
   workflowLocalRequest=async(path,body)=>{if(path.endsWith('/receive')){receives++;ready=true;}else if(body)posts.push(body);return ready?{state:'done',result:{mime_type:'image/jpeg',scene_id:s.id,room_id:project.id,download_variant:'standard',received_existing_image:true}}:{state:'unknown',can_receive_image:true,code:'GEMINI_IMAGE_DOWNLOAD_ERROR'};};render();SFMediaNodes.open('frame',s.id);}''',state)
  assert page.evaluate('mediaUrl("fixed-source")')!=original
  assert page.evaluate('directSignature(project.scenes[0],"","image")')==signature
  assert page.locator('[data-mn=create-product-frame]').inner_text()=='Tải lại ảnh đã tạo'
  page.locator('[data-mn=create-product-frame]').click();page.wait_for_function('project.scenes[0].frames.length===1&&!SFPromptPipeline.isRunning()')
  assert page.evaluate('posts.length===0&&receives===1&&project.cloudJobs[0].state==="imported"')
  assert page.evaluate('!project.cloudJobs[0].error&&!project.cloudJobs[0].errorCode&&!project.cloudJobs[0].waitError&&!project.scenes[0].approvedFrame')
  assert page.locator('#modal').is_visible();assert not errors,errors;browser.close()
 print('PASS one generation only; bounded automatic receive; reload/new blob URL keeps signature; same old image imported; no new generation, no stale active errors, no automatic approval')
finally:server.shutdown()
