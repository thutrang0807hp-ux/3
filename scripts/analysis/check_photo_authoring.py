import threading,http.server,functools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
from playwright.sync_api import sync_playwright
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(f'http://127.0.0.1:{server.server_port}/photos.html');page.wait_for_function('!!window.SFStoryboardGuide&&!!window.SceneForgeWorkflow')
 result=page.evaluate(r'''async()=>{
 const check=(v,m)=>{if(!v)throw Error(m)};window.sent=[];window.mode='unknown';window.files=new Map();
 window.SceneForgeApp={photoBridge:{engine:async(path,body)=>{
  if(path==='ai/script-library/status')return {store_id:'test-store',ai_source:'gemini_chat'};
  if(path==='ai/script-library'){sent.push(structuredClone(body));if(mode==='unknown')throw Error('Fixture connection lost');return {body:'Đây là lời mới để bạn rà.',timing:'estimated'};}
  if(path.endsWith('/status'))return {};throw Error('Unexpected route '+path);
 },listRecipes:async()=>[],listScriptLibrary:async()=>[],saveDraft:async()=>{},saveDraftNow:async()=>{},getFile:async key=>files.get(key),putFile:async(key,file)=>{files.set(key,file)}}};
 const refs=Object.fromEntries(['person','outfit','product','background'].map(k=>[k,{images:[],description:k+' fixture'}]));
 const d=newDraft();check(d.storyboardLook.layered===true,'new-room default missing');d.storyboardLook={look:''};d.refs=refs;d.voice.mode='native';d.idea='Giới thiệu bàn chải xanh';d.beats=[{id:'b1',name:'Cảnh cũ',type:'wide',seconds:8,text:'Lời đang giữ',storyboardComposition:'medium shot',storyboardAction:'hold product'}];
 await SceneForgeWorkflow.openRoom({id:'authoring-fixture',name:'Authoring',refs,product:{id:'prod',name:'Bàn chải',sceneBank:[]},photoDraft:d});
 const b=draft.beats[0],part=photoParts(b)[0],before=SFStoryboard.fingerprint(b,part,'start');check(!SFPhotoPromptLayers.enabled(),'existing room silently opted in');
 check(!photoWritingPrompt([b]).includes('LAYERED MOTION DIRECTIONS'),'existing writer changed');
 const checkbox=document.querySelector('[data-photo-prompt-layers]');check(checkbox,'layer control missing');checkbox.checked=true;checkbox.dispatchEvent(new Event('change',{bubbles:true}));await new Promise(r=>setTimeout(r,80));
 check(SFPhotoPromptLayers.enabled(),'layer preference not saved');check(before!==SFStoryboard.fingerprint(b,part,'start'),'image fingerprint did not change after explicit choice');check(draft.beats[0].text==='Lời đang giữ','script mutated');
 const writing=photoWritingPrompt([b]),at=writing.indexOf('\n'),data=JSON.parse(writing.slice(at+1));check(data.promptLayers.version===1&&data.referenceBindings,'writer mapping lost');
 const text=SFStoryboardGuide.imagePrompt('KEEP MANUAL CAMERA',SFStoryboardGuide.context({refs:[],beats:[b],current:b,edge:'start'}));check(text.startsWith('KEEP MANUAL CAMERA')&&text.includes('LAYERED PHOTO DIRECTIONS'),'manual image guidance lost');
 const look=document.querySelector('[data-sb-shared-look]');look.value='Ánh sáng tự nhiên';look.dispatchEvent(new Event('change',{bubbles:true}));await new Promise(r=>setTimeout(r,80));check(SFPhotoPromptLayers.enabled(),'changing look cleared layer choice');
 document.querySelector('[data-is="ai"]').click();await new Promise(r=>setTimeout(r,50));
 const kind=document.querySelector('[data-is-kind]');check(kind&&kind.options.length===7,'script categories missing');kind.value='review';kind.dispatchEvent(new Event('change',{bubbles:true}));
 const facts=document.querySelector('[data-is-facts]');facts.value='Cán xanh, đầu nhỏ';facts.dispatchEvent(new Event('input',{bubbles:true}));
 document.querySelector('[data-is="write"]').click();await new Promise(r=>setTimeout(r,100));
 check(sent.length===1&&sent[0].script_kind==='review'&&sent[0].verified_facts==='Cán xanh, đầu nhỏ','authoring payload wrong');check(draft.beats[0].text==='Lời đang giữ','AI send overwrote script');
 const next=document.querySelector('[data-is-kind]');next.value='offer';next.dispatchEvent(new Event('change',{bubbles:true}));mode='done';document.querySelector('[data-is="recover"]').click();await new Promise(r=>setTimeout(r,100));
 check(sent.length===2&&sent[1].script_kind==='review'&&sent[1].recovery===true,'recovery changed frozen format');check(draft.scriptInput.candidate==='Đây là lời mới để bạn rà.'&&draft.beats[0].text==='Lời đang giữ','draft review not preserved');
 return {categories:7,legacyRoomOptIn:true,layeredWriting:true,manualDirectionsPreserved:true,originalScriptPreserved:true,frozenRecovery:true};
}''')
 assert not errors,errors
 print('PASS photo authoring UI',result)
 browser.close()
server.shutdown()
