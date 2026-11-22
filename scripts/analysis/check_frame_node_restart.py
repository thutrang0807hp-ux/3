"""Real frame node: stop a stuck POST, restart all including unknown, ignore late reply."""
import threading,http.server,functools
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('window.SFPromptPipeline&&window.SFMediaNodes')
  out=page.evaluate('''async()=>{
   const check=(v,m)=>{if(!v)throw Error(m)},delay=ms=>new Promise(r=>setTimeout(r,ms));
   window.confirm=()=>true;storeProject=async()=>{};SFProviderReceipts.persistIntent=async()=>{};
   const canvas=document.createElement('canvas');canvas.width=canvas.height=16;canvas.getContext('2d').fillRect(0,0,16,16);const source=canvas.toDataURL();
   project=blankProject();project.id='restart-frames';project.scenes=[sceneRecord(0,4,0,[source]),sceneRecord(4,8,1,[source])];project.script=[];project.scenes.forEach(s=>{s.refsUsed=[];s.frames=[{id:'keep-'+s.id,image:source,version:1}];});
   let stuck=true,release,posted=[],failNext=false;const replies=new Map();
   const text={promptFrame:{vi:'Khung mới',en:'Fresh frame composition'},used_refs:['R1'],warnings:[]};
   workflowLocalRequest=async(path,body)=>{
    if(path==='gemini-chat/status')return {installed:true,selection:{available:true,token:'same'}};
    if(path==='gemini-chat/jobs'){
     posted.push(structuredClone(body));if(failNext){failNext=false;throw Error('Lỗi thử nghiệm ở một cảnh');}if(stuck)return new Promise(r=>release=r);
     const reply={state:'done',result:body.kind==='text'?{text:JSON.stringify(text)}:{images:[]}};replies.set(body.request_id,reply);return reply;
    }
    if(path.startsWith('gemini-chat/jobs/'))return replies.get(path.split('/').at(-1))||{state:'unknown'};
    return {};
   };
   directRecover=async()=>{for(const job of project.cloudJobs||[])if(job.state==='done')job.state='imported';};
   const first=SFPromptPipeline.runImages(project.scenes).catch(e=>e.message);
   while(!release)await delay(10);render();check(document.querySelector('[data-frame-progress] progress')?.max===2,'progress missing');check(document.querySelector('[data-frame-progress]').textContent.includes('ĐANG HOẠT ĐỘNG'),'active state missing');check(document.querySelector('[data-mn=pause-frames]'),'stop button missing');check(document.querySelector('[data-mn=rerun-node]').textContent.includes('2'),'all-scene count wrong');
   document.querySelector('[data-mn=pause-frames]').click();const stopped=await Promise.race([first,delay(500).then(()=>{throw Error('stop hung on network')})]);check(!SFPromptPipeline.isRunning(),'still running after stop');check(stopped.includes('dừng'),'stop reason missing');
   const old=project.cloudJobs[0];check(old.state==='unknown','stopped intent missing');
   // A separate old media request must also stop blocking the same scene.
   project.cloudJobs=[old,{id:'old-unknown',kind:'image',provider:'gemini-chat',sceneId:project.scenes[1].id,state:'unknown'}];stuck=false;
   await SFPromptPipeline.restartImagesAll();const fresh=posted.slice(1);check(fresh.filter(x=>x.kind==='text').length===0,'unexpected writer request');check(fresh.filter(x=>x.kind==='image').length===2,'did not create both frames');check(fresh.filter(x=>x.kind==='image').every(x=>x.conversation_scope),'whole-node retry did not isolate conversations');
   check(project.cloudJobs[0].state==='abandoned'&&project.cloudJobs[0].previousState==='unknown','old media receipt lost');check(project.cloudJobs.some(x=>x.id===old.id&&x.state==='abandoned'),'old image receipt lost');check(project.scenes.every(s=>s.frames[0].id==='keep-'+s.id),'old frame versions deleted');
   const stable=JSON.stringify(SFPromptPipeline.records().records);release({state:'done',result:{text:JSON.stringify({promptFrame:{vi:'CŨ',en:'LATE OLD'},used_refs:['R1'],warnings:[]})}});await delay(40);check(stable===JSON.stringify(SFPromptPipeline.records().records),'late old response changed current records');
   // A second click starts another full run, with fresh request IDs.
   await SFPromptPipeline.restartImagesAll();check(posted.filter(x=>x.kind==='image').length===5,'next rerun did not create all frames');check(new Set(posted.map(x=>x.request_id)).size===posted.length,'request ID reused');
   failNext=true;const partial=await SFPromptPipeline.restartImagesAll();check(partial.failures.length===1&&partial.completed===1,'one failed scene blocked remaining scene');check(SFPromptPipeline.records().run.state==='attention','partial run marked successful');check(document.querySelector('[data-frame-progress] progress').value===2,'completed/error count wrong');check(document.querySelector('[data-frame-progress]').textContent.includes('1 ảnh nhận được'),'real completed count missing');
   const savedRequest=workflowLocalRequest;let blockedPosts=0;workflowLocalRequest=async(path,body)=>{if(path==='gemini-chat/jobs'){blockedPosts++;throw Error('Kho máy chưa sẵn sàng; chưa gửi AI.');}return savedRequest(path,body);};
   try{await SFPromptPipeline.restartImagesAll()}catch(e){check(e.message.includes('Kho máy'),'wrong storage failure');}check(blockedPosts===1,'retried storage failure across scenes');check(document.querySelector('[data-frame-progress]').textContent.includes('Chưa gửi AI'),'storage block not visible');check(!SFPromptPipeline.isRunning(),'storage error left spinner active');
   return {stoppedWhilePostHung:true,allFramesIncludingUnknown:true,lateReplyIgnored:true,historyAndVersionsPreserved:true,repeatClickWorks:true};
  }''');assert not errors,errors;print('PASS',out);browser.close()
finally:server.shutdown()
