"""One real node button approves selected original files; partial failure does not block others."""
import functools,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1500,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(e.stack))
  html=(ROOT/'workflow.html').read_text().replace('<script id="frame-studio-node">','<script>if(!project)project=blankProject();</script><script id="frame-studio-node">')
  page.route('**/workflow.html*',lambda route:route.fulfill(body=html,content_type='text/html'))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('window.SFFrameStudio&&window.SFFrameImages')
  page.evaluate('''async()=>{
   storeProject=async()=>{};save=()=>{};window.bulkCalls=[];
   workflowLocalRequest=async(path,body)=>{if(path.includes('/jobs')||path.includes('quality')){bulkCalls.push(path);throw Error('Bulk approval must not generate, receive, or OCR');}return {};};
   const canvas=document.createElement('canvas');canvas.width=64;canvas.height=100;
   const make=async(id,color)=>{canvas.getContext('2d').fillStyle=color;canvas.getContext('2d').fillRect(0,0,64,100);const image=canvas.toDataURL('image/jpeg',.4),file=await new Promise(r=>canvas.toBlob(r,'image/png'));assets.set(id,file);return {id,asset:id,image,mime:'image/png',status:'pending'};};
   project=blankProject();project.id='bulk-approval';project.analysis.frameQualityRequired=true;project.analysis.semantic={fixture:true};
   const a=await make('selected-first','red'),b=await make('latest-second','blue'),c=await make('scene-two','green'),d={id:'missing',asset:'missing-file',image:a.image,mime:'image/png'},e=await make('already','white');
   project.source={poster:a.image,duration:40,name:'source.mp4'};project.scenes=Array.from({length:5},(_,i)=>sceneRecord(i*8,(i+1)*8,i,[a.image]));
   project.scenes.forEach(s=>s.refsUsed=[]);project.scenes[0].frames=[a,b];project.scenes[0].frameSelectionId=a.id;project.scenes[1].frames=[c];project.scenes[2].frames=[d];project.scenes[4].frames=[e];
   await SFFrameImages.approve(project.scenes[4]);render();
  }''')
  button=page.locator('[data-studio=approve-all]');assert '3 cảnh' in button.inner_text();button.click()
  page.wait_for_function("document.querySelector('[data-studio-progress]')?.textContent.includes('Đã duyệt 2/3')")
  result=page.evaluate('''()=>({approved:project.scenes.map(s=>frameApproved(s)),chosen:project.scenes[0].approvedFrame,versions:project.scenes[0].frames.length,calls:bulkCalls,text:document.querySelector('[data-studio-progress]').textContent})''')
  assert result['approved']==[True,True,False,False,True] and result['chosen']=='selected-first' and result['versions']==2,result
  assert result['calls']==[] and 'Cảnh 3' in result['text'],result
  # Only the previously missing file remains to approve on the next click.
  page.evaluate("assets.set('missing-file',assets.get('scene-two'))")
  assert '1 cảnh' in button.inner_text();button.click()
  page.wait_for_function('frameApproved(project.scenes[2])')
  assert page.evaluate('bulkCalls.length')==0
  assert button.is_disabled()
  assert not page.evaluate("document.querySelector('#modal')?.open")
  assert not errors,errors
  browser.close()
 print('PASS bulk node click: selected versions, skip already-approved/no-frame, partial missing-file report, retry remaining only, zero provider requests')
finally:server.shutdown()
