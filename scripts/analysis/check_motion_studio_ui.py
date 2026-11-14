"""Real browser fixture: reference bytes/order, image-only anchor, clothing rules and guards."""
import threading,http.server,functools
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('!!window.SFFrameIdentity&&!!window.SFPromptPipeline')
  import base64
  video=base64.b64encode(Path('/tmp/motion-ui-fixture.mp4').read_bytes()).decode()
  result=page.evaluate(r'''async video=>{
   const check=(v,m)=>{if(!v)throw Error(m)};window.saved=0;window.sent=[];storeProject=async()=>{saved++};SFProviderReceipts.persistIntent=async(job,save)=>save();
   const c=document.createElement('canvas');c.width=c.height=16;c.getContext('2d').fillRect(0,0,16,16);const png=c.toDataURL('image/png'),image=await new Promise(r=>c.toBlob(r,'image/png'));
   const file=new File([Uint8Array.from(atob(video),c=>c.charCodeAt(0))],'source.mp4',{type:'video/mp4'});
   project=blankProject();project.id='motion-test';project.workflowVariant='motion';project.source={asset:'source',duration:4,name:'source.mp4'};assets.set('source',file);project.refs.person={images:[{id:'person',image:png}],description:'Người tham khảo'};project.refs.product={images:[{id:'product',image:png}],description:'Sản phẩm'};
   const s=sceneRecord(0,4,0,[png]);s.refsUsed=['person','product'];project.scenes=[s];project.script=[];render();
   check(document.querySelector('#node-motion-kit')&&document.querySelector('#node-motion-clips'),'motion nodes absent');check(!document.querySelector('#node-clips'),'old generator still visible');check(clipParts(s)[0].generationDuration===4,'motion edit forced eight seconds');
   let blocked=false;try{workflowLocalRequest('flow/simple/jobs',{confirm_send:true})}catch(e){blocked=e.message.includes('không gửi nhầm')};check(blocked,'wrong i2v transport not blocked');
   const fetchBefore=fetch;window.fetch=async(url,options={})=>{
    const u=String(url);if(u==='/local-api/motion-studio/sources'){sent.push({path:'local-upload',size:options.body.size});return new Response(JSON.stringify({id:'msrc-'+'a'.repeat(32),duration:4,sha256:'abc'}),{headers:{'Content-Type':'application/json'}});}
    if(u.startsWith('/local-api/gemini-chat/files/'))return new Response(image,{headers:{'Content-Type':'image/png'}});
    if(u.startsWith('/local-api/motion-studio/clips/'))return new Response(file,{headers:{'Content-Type':'video/mp4'}});
    return fetchBefore(url,options);
   };
   workflowLocalRequest=async(path,body)=>{sent.push({path,body});if(path==='motion-studio/clips')return {id:'mclip-'+'b'.repeat(32),duration:body.end-body.start,start:body.start,end:body.end};if(path==='gemini-chat/status')return {installed:true,selection:{available:true,token:'token'}};if(path==='gemini-chat/jobs')return {state:'done',result:{mime_type:body.kind==='image'?'image/png':'text/plain',text:JSON.stringify({en:'Replace the person; keep the camera and action.',vi:'Thay người, giữ camera và động tác.'})}};if(path.endsWith('/status'))return {};throw Error('Unexpected '+path);};
   document.querySelector('[data-ms="approve"]').click();await new Promise(r=>setTimeout(r,70));check(frameApproved(s),'reference approval not accepted');
   document.querySelector('[data-ms="prepare"]').click();await new Promise(r=>setTimeout(r,100));check(document.querySelector('#msDownload'),'handoff missing');check(!document.querySelector('#modal [data-ms="write"]').disabled,'writer remains disabled after preparation');
   check(sent.find(x=>x.path==='motion-studio/clips').body.end===4,'clip bounds wrong');check(SFMotionStudio.state().rows[s.id+':a'].en.includes('source-clip.mp4'),'English default missing');check(sent.filter(x=>x.path==='local-upload').length===1,'source sent more than once');
   document.querySelector('#msVi').value='Thay mặt, giữ nguyên áo';document.querySelector('#msVi').dispatchEvent(new Event('input'));
   document.querySelector('#modal [data-ms="write"]').click();await new Promise(r=>setTimeout(r,100));check(document.querySelector('#msEn').value==='Replace the person; keep the camera and action.','new English overwritten by stale editor');check(document.querySelector('#msVi').value.includes('giữ camera'),'Vietnamese review missing');
   closeModal();render();
   const angle=document.querySelector('#msAngle');angle.value='back';document.querySelector('[data-ms="kit-create"]').click();await new Promise(r=>setTimeout(r,150));
   const job=sent.filter(x=>x.path==='gemini-chat/jobs').at(-1);check(job.body.kind==='image'&&job.body.prompt.includes('back view'),'kit angle reset during render');check(SFMotionStudio.state().kit.length===1&&!SFMotionStudio.state().kit[0].approved,'AI kit auto-approved');
   check(!sent.some(x=>x.path?.startsWith('flow/')&&x.body?.confirm_send),'generated on wrong Flow route');
   // Restore a clean approved reference state for the file import test.
   document.querySelector('[data-ms="approve"]').click();await new Promise(r=>setTimeout(r,70));
   window.motionFixture={scene:s.id,part:'a'};
   return {nodes:true,sourceUploads:sent.filter(x=>x.path==='local-upload').length,writingOnly:true,kitUnapproved:true,refsApproved:frameApproved(s)};
  }''',video)
  page.locator('[data-ms="import"]').first.click()
  page.locator('input[data-motion-result]').set_input_files('/tmp/motion-ui-fixture.mp4')
  page.wait_for_function('project.scenes[0].clips.length===1')
  assert page.evaluate('readyCount()')==0
  page.locator('[data-ms="view"]').first.click();page.locator('#msAcceptResult').click()
  imported=page.evaluate('({clips:project.scenes[0].clips.length,ready:readyCount(),duration:project.scenes[0].clips[0].duration,chosen:project.scenes[0].chosen.a,model:project.scenes[0].clips[0].model})')
  assert imported['ready']==1 and imported['model']=='flow-edit-imported',imported
  page.locator('[data-ms="import"]').first.click();page.locator('input[data-motion-result]').set_input_files('/tmp/motion-ui-fixture.mp4');page.wait_for_function('project.scenes[0].clips.length===2')
  assert page.evaluate('project.scenes[0].clips[0].id!==project.scenes[0].clips[1].id')
  page.screenshot(path='/tmp/motion-studio-workspace.png')
  assert not errors,errors
  print('PASS Motion UI',result,imported);browser.close()
finally:server.shutdown()
