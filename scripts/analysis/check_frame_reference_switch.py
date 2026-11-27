"""Click actual frame reference controls without receiving or generating the old job."""
import threading,http.server,functools
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(e.stack))
  # The host normally supplies a project before mounting this editor.
  html=(ROOT/'workflow.html').read_text().replace('<script id="frame-studio-node">','<script>if(!project)project=blankProject();</script><script id="frame-studio-node">')
  page.route('**/workflow.html*',lambda route:route.fulfill(body=html,content_type='text/html'))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('window.SFFrameStudio&&window.SFFrameImages')
  for status in ['unknown','done','queued']:
   page.evaluate('''async status=>{
    storeProject=async()=>{};window.referenceCalls=[];
    workflowLocalRequest=async(path,body)=>{if(path.startsWith('gemini-chat/jobs')){referenceCalls.push(path);throw Error('No receive or generation allowed for a reference change');}return {};};
    const canvas=document.createElement('canvas');canvas.width=canvas.height=32;const image=canvas.toDataURL();
    project=blankProject();project.id='switch-'+status;
    const s=sceneRecord(0,3,0,[image]);project.scenes=[s];s.refsUsed=['product'];
    s.frames=[{id:'retained-frame',image,version:1}];
    project.refs.product.images=[{id:'shared-product',name:'common',image}];
    s.frameReferenceChoices={product:{mode:'custom',images:[{id:'custom-product',name:'private',image}]}};
    project.cloudJobs=[{id:'old-job',sceneId:s.id,kind:'image',frameStudioVersion:164,state:status,signature:'old-inputs'}];
    window.referenceScene=s;
    await SFFrameStudio.open(s.id);
   }''',status)
   button=page.locator('[data-studio="ref-mode"][data-role="product"][data-mode="shared"]');button.click()
   page.wait_for_function("referenceScene.referenceRoleOverrides?.product===true && !referenceScene.frameReferenceChoices?.product")
   page.wait_for_function('!SFFrameImages.isRunning()')
   result=page.evaluate('''()=>({calls:referenceCalls,job:project.cloudJobs[0],frames:referenceScene.frames.map(f=>f.id),current:SFFrameImages.job(referenceScene)?.id})''')
   assert result['calls']==[],result
   assert result['job']['state']=='abandoned' and result['job']['previousState']==status,result
   assert result['job']['archivedBy']=='reference-change' and result['frames']==['retained-frame'],result
   assert result.get('current') is None,result
   assert 'Nhận xong lượt đang chờ' not in page.locator('#studioSceneStatus').inner_text()
   # Switching again is a local edit and creates no receipt or provider request.
   page.locator('[data-studio="ref-mode"][data-role="product"][data-mode="keep"]').click()
   page.wait_for_function("referenceScene.frameReferenceChoices.product.mode==='keep'")
   assert page.evaluate('referenceCalls.length')==0
   assert page.evaluate('project.cloudJobs.length')==1
   page.locator('[data-studio="ref-mode"][data-role="product"][data-mode="custom"]').click()
   page.wait_for_function("referenceScene.frameReferenceChoices.product.mode==='custom'")
   assert page.evaluate('referenceCalls.length')==0
  page.evaluate('''async()=>{
   const s=referenceScene,job={id:'late-old',sceneId:s.id,kind:'image',frameStudioVersion:164,state:'submitted'};
   project.cloudJobs=[job];let release;
   workflowLocalRequest=async path=>new Promise(resolve=>{release=resolve;});
   const pending=SFFrameImages.receive(s,{readOnly:true});
   while(!release)await new Promise(resolve=>setTimeout(resolve,0));
   SFFrameImages.detachForEdit(s);
   release({state:'done',result:{scene_id:s.id,room_id:project.id}});
   const outcome=await pending;
   if(!outcome.archived||job.state!=='abandoned'||s.frames.length!==1)throw Error('Late old result changed edited scene');
  }''')
  assert not errors,errors
  browser.close()
 print('PASS real UI: shared/custom/keep switch with unknown/done/queued old jobs; zero receive/generate requests, receipts and existing frames retained')
finally:server.shutdown()
