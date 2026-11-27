"""Real UI handoff with fixture media: TTS timing, manual captions, errors and host acknowledgement."""
import functools,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1450,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  html=(ROOT/'workflow.html').read_text().replace('<script id="frame-studio-node">','<script>if(!project)project=blankProject();</script><script id="frame-studio-node">')
  page.route('**/workflow.html*',lambda route:route.fulfill(body=html,content_type='text/html'))
  page.route('**/test-host',lambda route:route.fulfill(content_type='text/html',body='''<iframe src="/workflow.html?mode=reference&host=1&room=voice-test" style="width:1400px;height:950px"></iframe><script>window.received=[];window.addEventListener('message',e=>{if(e.data?.type==='sceneforge:workflow-open-editor'){received.push(e.data.payload);setTimeout(()=>e.source.postMessage({type:'sceneforge:workflow-import-result',...(window.rejectTransfer?{error:'Fixture import failed'}:{})},location.origin),100)}})</script>'''))
  page.goto(f'http://127.0.0.1:{server.server_port}/test-host');frame=page.frames[1];frame.wait_for_function('!!window.SFAudioNodes&&!!window.SFMergeOrder')
  frame.evaluate('''()=>{
   storeProject=async()=>{};save=()=>{};project=blankProject();project.id='voice-test';project.merge.musicMode='off';project.merge.captions=true;
   const image='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
   const s=sceneRecord(0,8,0,[image]);s.approvedFrame='source';s.sourceFrame={id:'source',image};s.clipPlanning={mode:'legacy',continuity:false};s.clips=[{id:'clip',asset:'clip-file',part:'a',version:1,duration:8,reviewDecision:{status:'accepted'}}];s.chosen={a:'clip'};project.scenes=[s];project.merge.order=[s.id];
   assets.set('clip-file',new File(['fixture-video'],'clip.mp4',{type:'video/mp4'}));assets.set('voice-file',new File(['fixture-audio'],'voice.wav',{type:'audio/wav'}));
   project.script=[{id:'l1',start:0,end:3,original:'Câu mẫu',newText:'Lời đọc thực tế'}];
   project.voiceOver={mode:'separate',origin:'vieneu',assetId:'voice-file',fileName:'voice.wav',duration:8,appliedSpeed:1,speedWanted:1,clipSound:'mute',segments:[{id:'l1',start:1.2,end:6.4}],spokenRows:[{id:'l1',text:'Lời đọc thực tế'}],versions:[]};project.merge.audioChanged=true;render();
  }''')
  cues=frame.evaluate('SFAudioNodes.currentCues()');assert cues==[{'start':1.2,'end':6.4,'text':'Lời đọc thực tế','manual':False}],cues
  # Speed-adjusted real segments replace automatic timings; source script stays unchanged.
  frame.evaluate("project.voiceOver.appliedSpeed=project.voiceOver.speedWanted=2;project.voiceOver.duration=4;project.voiceOver.segments=[{id:'l1',start:.6,end:3.2}];project.merge.audioChanged=true")
  assert frame.evaluate('SFAudioNodes.currentCues()[0].start')==.6
  assert frame.evaluate('project.script[0].start')==0
  frame.evaluate("render();const n=document.querySelector('#node-merge');view.z=1;view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView()")
  frame.locator('[data-nd=handoff]').click();page.wait_for_function('received.length===1')
  page.wait_for_function("document.querySelector('iframe').contentWindow.document.querySelector('#node-merge .ndSuccess')!==null")
  result=page.evaluate("({p:received[0].captions,roles:received[0].audio.map(a=>a.role),bytes:received[0].audio[0].file.size,muted:received[0].clipVolume})")
  assert result['p'][0]['start']==.6 and result['p'][-1]['end']==3.2,result
  assert result['roles']==['voice'] and result['bytes']==13 and result['muted']==0,result
  # Preserve manually edited subtitles. A stale edit blocks with an error at the clicked node.
  frame.evaluate("project.merge.captionDraft=[{start:2,end:3,text:'Sửa tay',manual:true}];project.merge.captionDraftSignature='old';project.merge.audioChanged=true;render()")
  assert frame.evaluate('SFAudioNodes.currentCues()[0].text')=='Sửa tay'
  frame.locator('[data-nd=handoff]').click();frame.wait_for_function("document.querySelector('#node-merge .ndError')?.textContent.includes('Rà phụ đề')")
  assert page.evaluate('received.length')==1
  # Host-side import failure must also be shown, rather than claiming success.
  frame.evaluate("delete project.merge.captionDraft;delete project.merge.audioCueSignature;project.merge.audioChanged=true;render()")
  page.evaluate('window.rejectTransfer=true');frame.locator('[data-nd=handoff]').click()
  frame.wait_for_function("document.querySelector('#node-merge .ndError')?.textContent.includes('Fixture import failed')")
  assert page.evaluate('received.length')==2
  assert not errors,errors
  browser.close();print('PASS: TTS segment timing, speed, actual voice/clip/caption handoff, manual edit protection, visible preparation/import errors.')
finally:server.shutdown()
