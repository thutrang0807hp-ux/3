"""Assembly drag order + real media payload, captions, audio offsets and history; no generation."""
import threading,http.server,functools,tempfile,subprocess,base64
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with tempfile.TemporaryDirectory() as tmp:
  mp4=Path(tmp)/'clip.mp4';red=Path(tmp)/'red.mp4';wav=Path(tmp)/'voice.wav'
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=green:s=180x320:r=24','-t','8','-c:v','libx264','-pix_fmt','yuv420p','-an',str(mp4)],check=True)
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=red:s=180x320:r=24','-t','8','-c:v','libx264','-pix_fmt','yuv420p','-an',str(red)],check=True)
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:sample_rate=24000','-t','16',str(wav)],check=True)
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1450,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('!!window.SFMergeOrder')
   result=page.evaluate('''async({mp4,red,wav})=>{
    project=blankProject();project.id='order-test';window.persisted=null;window.saveCalls=0;storeProject=async()=>{persisted=structuredClone(project);saveCalls++};
    const image='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';const video=new File([Uint8Array.from(atob(mp4),c=>c.charCodeAt(0))],'clip.mp4',{type:'video/mp4'}),voice=new File([Uint8Array.from(atob(wav),c=>c.charCodeAt(0))],'voice.wav',{type:'audio/wav'});assets.set('video1',video);assets.set('video2',new File([Uint8Array.from(atob(red),c=>c.charCodeAt(0))],'red.mp4',{type:'video/mp4'}));assets.set('voice',voice);
    project.scenes=[0,1].map(i=>{const s=sceneRecord(i*8,(i+1)*8,i,[image]);s.approvedFrame='source';s.sourceFrame={id:'source',image};s.clipPlanning={mode:'legacy',continuity:false};s.clips=[{id:'c'+i,asset:'video'+(i+1),part:'a',duration:8,version:1,reviewDecision:{status:'accepted'}}];s.chosen={a:'c'+i};return s;});project.merge.order=project.scenes.map(s=>s.id);project.script=[{id:'speech1',start:0,end:8,original:'Lời cảnh một',newText:'Lời cảnh một'},{id:'speech2',start:8,end:16,original:'Lời cảnh hai',newText:'Lời cảnh hai'}];project.merge.captions=true;project.merge.captionDraft=[{start:1,end:3,text:'Lời cảnh một',manual:true},{start:9,end:11,text:'Lời cảnh hai',manual:true}];project.merge.captionDraftSignature=productionCaptionSignature();project.merge.musicMode='off';project.voiceOver={mode:'separate',origin:'file',assetId:'voice',duration:16,fileName:'voice.wav',clipSound:'mute',versions:[]};render();const n=document.querySelector('#node-merge');view.z=1;view.x=20-n.offsetLeft;view.y=80-n.offsetTop;applyView();window.sceneIDs=project.scenes.map(s=>s.id);window.oldScript=JSON.stringify(project.script);return SFMergeOrder.rows().map(r=>r.key);
   }''',{'mp4':base64.b64encode(mp4.read_bytes()).decode(),'red':base64.b64encode(red.read_bytes()).decode(),'wav':base64.b64encode(wav.read_bytes()).decode()})
   page.wait_for_timeout(300)
   page.evaluate("const n=document.querySelector('#node-merge');view.z=1;view.x=50-n.offsetLeft;view.y=180-n.offsetTop;applyView()")
   page.screenshot(path='/tmp/merge-order-preview.png')
   tiles=page.locator('#node-merge [data-merge-clip]');assert tiles.count()==2
   tiles.nth(0).drag_to(tiles.nth(1),timeout=5000);page.wait_for_function('(key)=>project.merge.clipOrder?.[0]===key',arg=result[1])
   payload=page.evaluate('''async()=>{const clips=SFMergeOrder.rows().map(r=>({sceneId:r.sceneId,part:r.part,start:r.start,duration:r.duration,file:assets.get('video1')}));const payload={clips,audio:[{file:assets.get('voice'),role:'voice',start:0,duration:16}],captions:productionCues()};await SFAudioNodes.preparePayload(payload,{preview:true});return{scenes:payload.clips.map(c=>c.sceneId),voice:payload.audio.map(a=>[a.start,a.sourceIn,a.duration]),captions:payload.captions,saved:!!persisted.merge.clipOrder,sourceSame:JSON.stringify(project.scenes.map(s=>s.id))===JSON.stringify(sceneIDs),scriptSame:JSON.stringify(project.script)===oldScript};}''')
   assert payload['scenes']==list(reversed(page.evaluate('sceneIDs'))),payload
   assert payload['voice']==[[0,8,8],[8,0,8]],payload
   assert payload['captions'][0]['text']=='Lời cảnh hai' and payload['captions'][0]['start']==1 and payload['captions'][1]['start']==9,payload
   assert payload['saved'] and payload['sourceSame'] and payload['scriptSame'],payload
   page.evaluate('SFAudioNodes.playAssembly(()=>true)')
   page.wait_for_function("!!document.querySelector('#anCaptionDialog video[data-cap-active]')&&document.querySelector('#anCaptionDialog video[data-cap-active]').readyState>=2",timeout=15000)
   pixel=page.evaluate("(()=>{const v=document.querySelector('#anCaptionDialog video[data-cap-active]'),c=document.createElement('canvas');c.width=c.height=2;c.getContext('2d').drawImage(v,0,0,2,2);return [...c.getContext('2d').getImageData(0,0,1,1).data]})()")
   assert pixel[0]>200 and pixel[1]<40,pixel
   page.locator('[data-cap-close]').click();page.wait_for_function('SFAudioNodes.getState().captionPreview===null')
   # Restore persisted order without regenerating any clip; keyboard alternative and reset.
   page.evaluate('project=structuredClone(persisted);render()');assert page.evaluate('SFMergeOrder.rows()[0].key')==result[1]
   page.locator('[data-mo=undo]').click();page.wait_for_function('(key)=>SFMergeOrder.rows()[0].key===key',arg=result[0])
   assert page.evaluate('project.merge.captionDraft[0].text')=='Lời cảnh một'
   first=page.locator('#node-merge [data-merge-clip]').nth(0);first.focus();page.keyboard.press('Alt+ArrowRight');page.wait_for_function('(key)=>SFMergeOrder.rows()[0].key===key',arg=result[1])
   pieces=page.evaluate("SFMergeOrder.mapCues([{start:7,end:9,text:'một hai ba bốn'}],SFMergeOrder.base(),SFMergeOrder.rows())")
   assert sum(len(c['text'].split()) for c in pieces)==4,pieces
   extra=page.evaluate('''async original=>{assets.set('voice-new',assets.get('voice'));project.voiceOver.assetId='voice-new';delete project.merge.voiceOrderSource;await SFMergeOrder.setOrder(original);const p={clips:SFMergeOrder.rows().map(r=>({sceneId:r.sceneId,part:r.part,start:r.start,duration:r.duration})),audio:[{role:'voice',file:assets.get('voice-new'),start:0,duration:16}],captions:[]};SFMergeOrder.apply(p);if(p.audio.length!==1||(p.audio[0].sourceIn||0)!==0)throw Error('new voice inherited old reordered offsets');
    project.voiceOver.mode='flow';delete project.voiceOver.assetId;delete project.merge.captionDraft;project.merge.captions=false;const s=project.scenes[0];s.clipPlan={start:s.start,end:s.end,parts:[{id:'a',start:0,end:4,duration:4},{id:'b',start:4,end:8,duration:4}]};const all=SFMergeOrder.base(),keys=all.map(r=>r.key);await SFMergeOrder.setOrder([keys[1],keys[2],keys[0]]);return {parts:SFMergeOrder.rows().map(r=>r.part),scenes:SFMergeOrder.rows().map(r=>r.sceneId)};}''',result)
   assert extra['parts']==['b','a','a'] and extra['scenes'][0]==extra['scenes'][2],extra
   assert not errors,errors
   print('PASS real drag + keyboard, persisted clip order, unchanged source/script, manual captions move, separate voice sourceIn moves, undo, cross-boundary words preserved',payload)
   browser.close()
finally:server.shutdown()
