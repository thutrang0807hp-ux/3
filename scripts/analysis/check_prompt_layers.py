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
  result=page.evaluate('''async()=>{
 const check=(v,m)=>{if(!v)throw Error(m)};
 storeProject=async()=>{};window.ppCalls=[];
 SFProviderReceipts.persistIntent=async(job,save)=>{await save();};
 const resultImage={promptFrame:{vi:'BẢN VIỆT KIỂM: giữ đúng bàn chải và ánh sáng.',en:'Keep the referenced toothbrush geometry and source lighting.'},used_refs:['R1','R2','R3'],warnings:[]};
 const resultVideo={visual:{vi:{},en:{}},motion:{vi:{camera:'Máy quay giữ nguyên.',initial:'Đang cầm bàn chải.',action:'Đưa bàn chải lên.',final:'Giữ tay.'},en:{camera:'Keep the camera fixed.',initial:'The person holds the toothbrush.',action:'Raise the toothbrush while maintaining the grip.',final:'Hold the final pose.'}},used_refs:['R1','R2','R3'],warnings:[]};
 for(const lang of ['vi','en'])for(const key of SFPromptContract.visual)resultVideo.visual[lang][key]=key==='composition'?'Keep the approved composition.':'';
 resultVideo.used_refs=['R1'];
 let lastResult=resultImage;
 workflowLocalRequest=async(path,body)=>{
  ppCalls.push({path,body});
  if(path==='gemini-chat/status')return {installed:true,selection:{available:true,token:'test-token'}};
  if(path==='gemini-chat/jobs'&&body){lastResult=body.prompt.includes('"stage":"video"')?resultVideo:resultImage;return {state:'done',result:{text:JSON.stringify(lastResult)}};}
  if(path.startsWith('gemini-chat/jobs/'))return {state:'done',result:{text:JSON.stringify(lastResult)}};
  if(path.endsWith('/status'))return {installed:false,models:[]};throw Error('Unexpected network path '+path);
 };
 const c=document.createElement('canvas');c.width=c.height=16;c.getContext('2d').fillRect(0,0,16,16);const source=c.toDataURL('image/png'),file=await new Promise(r=>c.toBlob(r,'image/png'));
 project=blankProject();project.id='prompt-layers';project.refs.person={images:[{id:'p',image:source}],description:'Nhân vật chính'};project.refs.product={images:[{id:'q',image:source}],description:'Bàn chải xanh'};
 const s=sceneRecord(0,8,0,[source]);s.refsUsed=['person','product'];s.frames=[{id:'approved',asset:'approved-file',image:source,version:1,status:'approved'}];s.approvedFrame='approved';s.frameSelectionId='approved';assets.set('approved-file',file);project.scenes=[s];project.script=[];render();
 const pack=await SFPromptPipeline.pack(s,'image');check(pack.prompt.includes('LAYERED PRODUCTION BRIEF'),'no layered instructions');check(pack.prompt.includes('finger contact'),'no object contact guidance');check(pack.prompt.includes('Do not invent a 4K setting'),'false quality promise');check(pack.bindings[1].role==='person'&&pack.bindings[2].role==='product','roles changed');
 const slot=s.id+':image:';
 const old={template:2,applied:true,input:SFPromptPipeline.snapshot(s,'image',null,2),job:{id:'old',state:'applied'},result:resultImage};SFPromptPipeline.records().records[slot]=old;
 check(SFPromptPipeline.current(s,'image'),'unchanged older prompt invalidated');
 const before=ppCalls.length;await SFPromptPipeline.prepareImage(s);check(ppCalls.length===before,'old prompt rewritten automatically');
 s.frameManualInput=SFPromptPipeline.snapshot(s,'image',null,2);s.framePromptOverride='Custom English identity details';await SFPromptPipeline.prepareImage(s);check(s.framePromptOverride==='Custom English identity details','manual overwritten');
 s.promptRevision={image:'GIỮ BÀN CHẢI XANH, SỬA ÁNH SÁNG'};
 await SFPromptPipeline.rewriteImage(s);
 check(s.approvedFrame==='approved'&&assets.has('approved-file'),'approved media modified');
 const posted=ppCalls.filter(x=>x.path==='gemini-chat/jobs');check(posted.length===1,'duplicate write');check(posted[0].body.prompt.includes('GIỮ BÀN CHẢI XANH'),'review edit not sent to writer');check(SFPromptPipeline.reviewText(s,'image').includes('BẢN VIỆT KIỂM'),'review text lost');
 const finalImage=imageFramePrompt(s);check(finalImage.includes(resultImage.promptFrame.en),'English missing');check(!finalImage.includes('BẢN VIỆT KIỂM')&&!finalImage.includes('GIỮ BÀN CHẢI XANH'),'Vietnamese translation leaked to generation');
 const p=clipParts(s)[0];s.extraRequest='YÊU CẦU VIỆT CHỈ CHO AI VIẾT';await SFPromptPipeline.prepareVideo(s,p);
 const finalVideo=makePrompt(s,p);check(finalVideo.includes(resultVideo.motion.en.action),'English motion missing');check(!finalVideo.includes('Đưa bàn chải')&&!finalVideo.includes(s.extraRequest),'Vietnamese writing context leaked to video generation');check(!/R[2-9]/.test(finalVideo),'extra video references leaked');
 check(ppCalls.every(x=>!(x.path.startsWith('flow/')&&x.body)),'writer created media');
 render();const tile=document.querySelector('#node-frames [data-mn="open"]');check(tile,'frame inspector entry missing');tile.click();await new Promise(r=>setTimeout(r,50));check(document.querySelector('#mnVietnamesePrompt'),'Vietnamese inspector missing');
 check(document.querySelector('[data-mn="prepare-image-prompt"]'),'explicit rewrite action missing');
 return {writerRequests:ppCalls.filter(x=>x.path==='gemini-chat/jobs').length,approvedMediaPreserved:true,legacyPromptPreserved:true,englishOnlyGeneration:true};
  }''')
  page.screenshot(path='/tmp/v120-prompt-inspector.png')
  assert not errors,errors
  print('PASS',result);browser.close()
finally:server.shutdown()
