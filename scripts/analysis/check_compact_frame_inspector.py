"""One visible primary action, collapsed advanced controls, same-request recovery and no duplicate error."""
import functools,http.server,io,threading
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
buf=io.BytesIO();Image.new('RGB',(180,320),'#38585b').save(buf,'PNG');image=buf.getvalue()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':950});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('**/local-api/gemini-chat/files/*',lambda r:r.fulfill(body=image,content_type='image/png'))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html');page.wait_for_function('window.SFFrameImages&&window.SFMediaNodes')
  page.evaluate('''async()=>{storeProject=async()=>{};SFProviderReceipts.persistIntent=async()=>{};const c=document.createElement('canvas');c.width=180;c.height=320;c.getContext('2d').fillStyle='#38585b';c.getContext('2d').fillRect(0,0,180,320);const source=c.toDataURL();project=blankProject();project.id='compact-frame';project.source={poster:source};project.scenes=[sceneRecord(0,4,0,[source])];const s=project.scenes[0];s.refsUsed=[];await SFFrameImages.prepare(s);const message='TRANSFER_FIXTURE_403';project.cloudJobs=[{id:'gchat-'+crypto.randomUUID(),kind:'image',provider:'gemini-chat',sceneId:s.id,part:'',signature:await directSignature(s,'','image'),state:'unknown',canReceiveImage:true,errorCode:'GEMINI_IMAGE_DOWNLOAD_ERROR',error:message+' HTTP 403'}];s.frameActionError={message:'wrapped '+message+' HTTP 403',at:Date.now()};window.receives=0;window.generations=0;workflowLocalRequest=async(path,body)=>{if(path.endsWith('/receive')){receives++;return new Promise(resolve=>window.finishReceive=()=>resolve({state:'done',result:{mime_type:'image/png',room_id:project.id,scene_id:s.id}}));}if(body){generations++;throw Error('Unexpected generation');}return{state:'done',result:{mime_type:'image/png',room_id:project.id,scene_id:s.id}};};render();SFMediaNodes.open('frame',s.id);}''')
  assert page.locator('#modal [data-frame-main]').inner_text()=='Tải lại ảnh'
  assert page.locator('#modal button.primary:visible').count()==1
  assert not page.locator('#frameInspectorAdvanced').get_attribute('open')
  assert not page.locator('#modal [data-mn=prepare-image-prompt]').is_visible()
  assert page.locator('#modal [data-mn=receive-scene-image]').count()==0
  assert page.locator('#frameInspectorAdvanced [data-mn=retry-scene-image]').count()==1
  assert not page.locator('#frameInspectorAdvanced [data-mn=retry-scene-image]').is_visible()
  assert page.locator('#modal [data-mn=pause-frames]').count()==0
  assert page.locator('#modal').text_content().count('TRANSFER_FIXTURE_403')==1
  page.screenshot(path='/tmp/frame154-compact-error.png')
  # A receive preflight failure must supersede the saved 403, and survive reopening.
  page.evaluate('''()=>{window.realRequest=workflowLocalRequest;workflowLocalRequest=async(path,body)=>{if(path.endsWith('/receive'))throw Error('HTTP 409: Không còn dấu ảnh chính xác của lượt cũ để nhận lại.');return realRequest(path,body);};}''')
  page.locator('#modal [data-frame-main]').click()
  page.wait_for_function('project.cloudJobs[0].receiveAttempt?.state==="failed"&&!SFFrameImages.isRunning()')
  assert 'HTTP 409' in page.locator('#modal').text_content()
  assert 'TRANSFER_FIXTURE_403' not in page.locator('#modal').text_content()
  assert page.evaluate('generations===0&&receives===0')
  page.evaluate('SFMediaNodes.open("frame",project.scenes[0].id)')
  assert 'HTTP 409' in page.locator('#modal').text_content()
  page.evaluate('()=>{workflowLocalRequest=realRequest;}')
  page.locator('#modal [data-frame-main]').click();page.wait_for_function('typeof finishReceive==="function"')
  page.wait_for_function('!!document.querySelector("#modal [data-mn=pause-frames]")')
  assert page.locator('#modal [data-frame-main]').is_disabled()
  assert page.evaluate('receives===1&&generations===0')
  page.evaluate('finishReceive()');page.wait_for_function('!SFFrameImages.isRunning()&&project.scenes[0].frames.length===1')
  assert page.locator('#modal [data-frame-main]').inner_text()=='Duyệt ảnh'
  assert page.locator('#modal button.primary:visible').count()==1
  assert page.locator('#modal [data-mn=pause-frames]').count()==0
  assert not page.evaluate('!!project.scenes[0].approvedFrame')
  assert 'TRANSFER_FIXTURE_403'not in page.locator('#modal').text_content()
  assert not errors,errors;browser.close()
 print('PASS compact scene: one visible primary action, technical editing collapsed, one error, stop only while active; receives original file without generation and requires review')
finally:server.shutdown()
