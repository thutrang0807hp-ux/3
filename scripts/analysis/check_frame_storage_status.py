"""Actual storage read-only inspector plus real frame-node diagnostics button."""
import threading,http.server,functools
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
shell=(ROOT/'index.html').read_text();a=shell.index(' async function inspectStatus(){');b=shell.index(' return {ready,inspectStatus,edit,',a);method=shell[a:b]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('window.SFPromptPipeline&&window.SFProviderReceipts')
  out=page.evaluate('''async method=>{
   const check=(v,m)=>{if(!v)throw Error(m)};
   let active=false,editing=false,error='Kho máy và trình duyệt có chỉnh sửa khác nhau.',revision=7,phase='',fail=false,calls=[];
   const api=async path=>{calls.push(path);if(fail)throw Error('connection lost');return {revision:7}};
   const inspect=eval('('+method.trim()+')');const result=await inspect();check(!result.ready&&result.connected&&result.reason===error,'local block lost');check(active===false&&revision===7,'inspector changed store');
   fail=true;const offline=await inspect();check(!offline.connected&&offline.reason.includes('connection lost'),'offline reason missing');fail=false;
   window.SceneForgeStorage={managed:true,state:{active:false,error},inspectStatus:inspect};
   const canvas=document.createElement('canvas');canvas.width=canvas.height=16;const source=canvas.toDataURL();project=blankProject();project.id='storage-diagnostics';project.source={poster:source};project.scenes=[sceneRecord(0,4,0,[source])];SFPromptPipeline.records().run={scope:'frame-node',state:'attention',total:1,completed:0,startedAt:Date.now(),finishedAt:Date.now(),phase:'Chưa gửi AI'};render();
   const panel=document.querySelector('.mnStorageIssue');check(panel?.textContent.includes(error),'root reason not shown on node');document.querySelector('[data-mn=storage-recheck]').click();await new Promise(r=>setTimeout(r,30));
   check(document.querySelector('.mnStorageIssue').textContent.includes('Kết nối máy: có'),'button did not display connection status');check(document.querySelector('.mnStorageIssue').textContent.includes('đang tạm dừng'),'blocked state missing');check(calls.every(x=>x==='status'),'inspector wrote or hydrated data');
   let blocked=false;try{await SFProviderReceipts.persistIntent({state:'prepared'},async()=>{},window.SceneForgeStorage)}catch(e){blocked=e.message.includes(error)}check(blocked,'pre-dispatch error lost root reason');
   active=true;error='';window.SceneForgeStorage.state={active:true,error:''};const ready=await inspect();check(ready.ready,'ready store reported blocked');
   return {reasonVisibleOnNode:true,readOnlyButton:true,noStoreMutation:true,connectionFailureExplained:true,preDispatchReasonPreserved:true};
  }''',method);assert not errors,errors;print('PASS',out);browser.close()
finally:server.shutdown()
