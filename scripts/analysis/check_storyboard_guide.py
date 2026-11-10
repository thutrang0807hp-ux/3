import threading,http.server,functools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
from playwright.sync_api import sync_playwright
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(f'http://127.0.0.1:{server.server_port}/photos.html');page.wait_for_function('!!window.SFStoryboardGuide&&!!window.SceneForgeWorkflow')
 result=page.evaluate('''async()=>{
 window.saved=0;window.calls=[];window.SceneForgeApp={photoBridge:{engine:async(path)=>{calls.push(path);return{}},listRecipes:async()=>[],saveDraft:async()=>{saved++},getFile:async()=>null,putFile:async()=>{}}};
 const refs=Object.fromEntries(['person','outfit','product','background'].map(k=>[k,{images:[],description:k+' fixture'}]));
 const d=newDraft();d.refs=refs;d.voice.mode='native';d.beats=[{id:'b1',name:'Giới thiệu',type:'wide',seconds:8,text:'Đây là sản phẩm của tôi',storyboardComposition:'medium shot',storyboardAction:'hold product'},{id:'b2',name:'Chi tiết',type:'detail',seconds:8,text:'Xem phần tay cầm',storyboardComposition:'close-up',storyboardAction:'show handle'}];
 await SceneForgeWorkflow.openRoom({id:'guide-fixture',name:'Guide',refs,product:{id:'prod',name:'Sản phẩm',sceneBank:[]},photoDraft:d});
 const b=draft.beats[0],part=photoParts(b)[0];const before=SFStoryboard.fingerprint(b,part,'start');const overall=photoOverallImagePrompt();const writing=photoWritingPrompt(draft.beats);const at=writing.indexOf('\\n');const data=JSON.parse(writing.slice(at+1));const production=JSON.parse(photoProductionInput());
 if(!Array.isArray(production.beats))throw Error('production shape changed');
 const start=SFStoryboardGuide.context({refs:photoRefsFor(b),beats:draft.beats,current:b,edge:'start'});if(start.next.id!=='b2'||start.previous!==null)throw Error('wrong neighbor context');
 const manual='KEEP MY CUSTOM CAMERA';const prompt=SFStoryboardGuide.imagePrompt(manual,start);if(!prompt.startsWith(manual))throw Error('manual composition lost');
 document.querySelector('[data-sb-shared-look]').value='ánh sáng dịu, màu chân thực';document.querySelector('[data-sb-shared-look]').dispatchEvent(new Event('change',{bubbles:true}));await new Promise(r=>setTimeout(r,100));
 const after=SFStoryboard.fingerprint(b,part,'start');
 const row=SFStoryboard.slots()[0];row.s.prompts.start='CUSTOM CAMERA: low angle, keep the real product';
 const canvas=document.createElement('canvas');canvas.width=16;canvas.height=16;canvas.getContext('2d').fillRect(0,0,16,16);const file=new File([await new Promise(resolve=>canvas.toBlob(resolve))],'fixture.png',{type:'image/png'});
 const image=await SFStoryboard.importImage(row.id,'start',file);if(!image.prompt.includes('STORYBOARD ART DIRECTION v1')||!image.prompt.includes('CUSTOM CAMERA')||!image.prompt.includes('Xem phần tay cầm'))throw Error('actual frame prompt lost guide/manual/neighbor');
 if(before===after)throw Error('style edit did not stale images');if(!draft.beats.every(b=>b.promptDirty))throw Error('prompts not marked for review');
 return {hasUI:!!document.querySelector('[data-sb-shared-look]'),hasPlan:!!data.storyboardArtDirection,hasIdentity:overall.includes('Product references define'),preservedText:draft.beats[0].text,style:draft.storyboardLook.look,saved,calls};
}''')
 assert result['hasUI'] and result['hasPlan'] and result['hasIdentity'] and result['saved']>0,result
 assert not any('/jobs' in x or x.endswith('/generate') for x in result['calls']),result
 assert not errors,errors
 print('PASS real photo room render; script + refs planning; manual camera preserved; shared style saved; frame fingerprints invalidate; prompt review; no generation dispatched',result)
 browser.close()
server.shutdown()
