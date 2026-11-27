"""Actual manual-approval click unlocks video packing using the selected original file."""
import functools,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(e.stack))
  html=(ROOT/'workflow.html').read_text().replace('<script id="frame-studio-node">','<script>if(!project)project=blankProject();</script><script id="frame-studio-node">')
  page.route('**/workflow.html*',lambda route:route.fulfill(body=html,content_type='text/html'))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('window.SFFrameImages&&window.SFFrameStudio')
  for rejected_quality in [False,True]:
   page.evaluate('''async rejected=>{
    storeProject=async()=>{};save=()=>{};window.approvalCalls=[];
    workflowLocalRequest=async(path,body)=>{if(path.includes('quality')||path.includes('/jobs')){approvalCalls.push(path);throw Error('No OCR or generation allowed on approval');}return {};};
    const canvas=document.createElement('canvas');canvas.width=572;canvas.height=1024;
    const make=async(color,key)=>{canvas.getContext('2d').fillStyle=color;canvas.getContext('2d').fillRect(0,0,572,1024);const image=canvas.toDataURL('image/jpeg',.3);const file=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));assets.set(key,file);return {id:key,asset:key,image,mime:'image/png',width:572,height:1024,status:'pending'};};
    project=blankProject();project.id='manual-frame-'+rejected;project.analysis.frameQualityRequired=true;
    const a=await make('red','selected-original'),b=await make('blue','latest-other');
    if(rejected)a.quality={can_quick_approve:false,warnings:['Below old HD threshold']};
    const s=sceneRecord(0,8,0,[a.image]);s.refsUsed=[];s.frames=[a,b];s.frameSelectionId=a.id;
    s.localWarnings=['Source measurement to review'];s.localReviewKey='source-warning';project.scenes=[s];project.approvalCleanupPending=[{sceneId:s.id,kind:'frame',part:null,keepId:b.id}];window.target=s;
    await SFFrameStudio.open(s.id);
   }''',rejected_quality)
   page.locator('[data-studio=approve]').click()
   page.wait_for_function("target.approvedFrame==='selected-original' && frameApproved(target)")
   assert page.locator('#frameCheckReal').count()==0
   assert not page.evaluate("document.querySelector('#modal')?.open")
   result=page.evaluate('''async()=>{
    const part=clipParts(target)[0];
    const refs=await SFPromptPipeline.generationRefs(target,part,false);
    return {frame:frameV3(target).id,approved:target.approvedFrame,valid:frameApproved(target),files:refs.length,exact:refs[0].data===await cpuEncode(assets.get('selected-original')),flowExact:await cpuEncode(await(await fetch(clipStartImage(target,part))).blob())===await cpuEncode(assets.get('selected-original')),videoState:SFVeoNode.tileState(SFVeoNode.slots()[0]).kind,pending:project.approvalCleanupPending,calls:approvalCalls,manual:target.manualFrameApproval,versions:target.frames.length};
   }''')
   assert result['frame']==result['approved']=='selected-original' and result['valid'],result
   assert result['files']==1 and result['exact'] and result['flowExact'] and result['calls']==[] and result['versions']==2,result
   assert result['videoState']!='blocked' and result['pending']==[],result
   assert result['manual']['frameId']=='selected-original' and result['manual']['sha256'],result
   # Missing original or changed inputs must not stay approved.
   assert page.evaluate("()=>{assets.delete('selected-original');return !frameApproved(target)}")
   assert page.evaluate("async()=>{try{await SFFrameImages.approve(target);return false}catch(e){return e.message.includes('Thiếu file')}}")
  assert not errors,errors
  browser.close()
 print('PASS real approval click without OCR/HD gate; selected older original file packed for video, versions retained, no generation, missing file rejected')
finally:server.shutdown()
