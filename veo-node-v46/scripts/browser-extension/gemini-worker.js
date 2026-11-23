/* Authenticated browser transport. Never export Google cookies to the app. */
const geminiLoops=new Set();let geminiTurn=Promise.resolve();
async function geminiWire(link,path,body={}){
 const r=await fetch(link.base+'/local-api/browser-bridge/gemini-'+path,{method:'POST',credentials:'omit',redirect:'error',headers:{'Content-Type':'application/json','X-SceneForge-Bridge':'1'},body:JSON.stringify({id:link.id,key:link.browser_key,...body}),signal:AbortSignal.timeout(25000)});
 if(r.status===403){const saved=(await chrome.storage.local.get('geminiLinks')).geminiLinks||{};delete saved[link.id];await chrome.storage.local.set({geminiLinks:saved});throw Error('revoked');}
 if(!r.ok)throw Error('bridge');return r.json();
}
async function geminiTabJob(link,job){
 const key='geminiJob:'+job.id,prior=(await chrome.storage.local.get(key))[key];
 if(prior?.result)return prior.result;
 // A restarted worker never repeats a prompt whose send may already have occurred.
 if(prior?.started)return {ok:false,accepted:null,code:'GEMINI_BROWSER_FAILED',tab_id:prior.tabId};
 let tabId=link.tabId,created=false,recorded=false;
 const keepAlive=setInterval(()=>chrome.runtime.getPlatformInfo(()=>{}),20000);
 try{
  const paired=await chrome.tabs.get(link.tabId);const url=new URL(paired.url);
  if(url.origin!=='https://gemini.google.com')return {ok:false,accepted:false,code:'GEMINI_BROWSER_OFFLINE'};
  if(job.request.operation==='generate'){
   const currentPath=url.pathname.match(/^\/u\/\d+/)?.[0]||'';
   if(link.accountPath!==undefined&&currentPath!==link.accountPath)return {ok:false,accepted:false,code:'GEMINI_BROWSER_OFFLINE'};
   const accountPath=link.accountPath??currentPath;
   const tab=await chrome.tabs.create({url:'https://gemini.google.com'+accountPath+'/app',active:false,windowId:paired.windowId});tabId=tab.id;created=true;
   const end=Date.now()+25000;while(Date.now()<end){const t=await chrome.tabs.get(tabId);if(t.status==='complete')break;await new Promise(r=>setTimeout(r,250));}
  }
  if(job.request.operation==='receive'){
   const original=(await chrome.storage.local.get('geminiJob:'+job.request.target_job))['geminiJob:'+job.request.target_job];
   if(!original?.tabId)return {ok:false,accepted:null,code:'GEMINI_BROWSER_FAILED'};tabId=original.tabId;
  }
  await chrome.storage.local.set({[key]:{started:true,tabId,linkId:link.id,operation:job.request.operation}});recorded=true;
  const [execution]=await chrome.scripting.executeScript({target:{tabId},func:sceneForgeGeminiTab,args:[{...job.request,request_id:job.id}]});let result=execution?.result||{ok:false,accepted:null,code:'GEMINI_BROWSER_FAILED'};
  if(result.imageUrl){
   try{
    const url=new URL(result.imageUrl);if(url.protocol!=='https:'||!url.hostname.endsWith('.googleusercontent.com'))throw Error();
    const r=await fetch(url.href,{credentials:'include',redirect:'error',signal:AbortSignal.timeout(20000)});const mime=r.headers.get('content-type')?.split(';')[0];if(!r.ok||!['image/png','image/jpeg','image/webp'].includes(mime))throw Error();
    const reader=r.body.getReader(),chunks=[];let size=0;
    try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>24*1024*1024)throw Error();chunks.push(value);}}finally{await reader.cancel().catch(()=>{});}
    const binary=chunks.flatMap(a=>{const out=[];for(let i=0;i<a.length;i+=8192)out.push(String.fromCharCode(...a.subarray(i,i+8192)));return out;}).join('');result={ok:true,image:btoa(binary),mime};
   }catch{result={ok:false,accepted:true,code:'GEMINI_BROWSER_TRANSFER_FAILED'};}
  }
  delete result.imageUrl;result.tab_id=tabId;
  await chrome.storage.local.set({[key]:{started:true,tabId,linkId:link.id,operation:job.request.operation,pending:true,result}});return result;
 }catch{return {ok:false,accepted:recorded?null:false,code:recorded?'GEMINI_BROWSER_FAILED':'GEMINI_BROWSER_OFFLINE',tab_id:tabId};}
 finally{clearInterval(keepAlive);}
}
async function geminiDeliver(link,job,result){
 while(((await chrome.storage.local.get('geminiLinks')).geminiLinks||{})[link.id]){
  try{await geminiWire(link,'result',{job_id:job.id,result});break;}catch(e){if(e.message==='revoked')return;await new Promise(r=>setTimeout(r,2000));}
 }
 const key='geminiJob:'+job.id;
 await chrome.storage.local.set({[key]:{started:true,tabId:result.tab_id,linkId:link.id,operation:job.request.operation,pending:false,...(!result.ok?{result}:{}),received:!!result.ok}});
 if(result.ok&&job.request.operation!=='identity')await chrome.tabs.remove(result.tab_id).catch(()=>{});
}
async function geminiLoop(link){
 if(geminiLoops.has(link.id))return;geminiLoops.add(link.id);
 try{
  const stored=await chrome.storage.local.get(null);
  for(const [key,row]of Object.entries(stored)){if(key.startsWith('geminiJob:')&&row.linkId===link.id&&row.pending&&row.result)await geminiDeliver(link,{id:key.slice(10),request:{operation:row.operation}},row.result);}
  while(((await chrome.storage.local.get('geminiLinks')).geminiLinks||{})[link.id]){
   try{
    const packet=await geminiWire(link,'poll');if(!packet.job)continue;const job=packet.job;
    const result=await (geminiTurn=geminiTurn.catch(()=>{}).then(()=>geminiTabJob(link,job)));
    await geminiDeliver(link,job,result);
   }catch(e){if(e.message==='revoked')return;await new Promise(r=>setTimeout(r,2500));}
  }
 }finally{geminiLoops.delete(link.id);}
}
async function geminiConnectLink(link){
 const tab=await chrome.tabs.get(link.tabId);const url=new URL(tab.url);if(url.origin!=='https://gemini.google.com')throw Error('tab');
 link.accountPath=url.pathname.match(/^\/u\/\d+/)?.[0]||'';
 await geminiWire(link,'poll',{hello:true});const all=(await chrome.storage.local.get('geminiLinks')).geminiLinks||{};all[link.id]=link;await chrome.storage.local.set({geminiLinks:all});geminiLoop(link);return {ok:true};
}
chrome.runtime.onMessage.addListener((message,sender,respond)=>{
 if(message?.type!=='pairGemini'||sender.id!==chrome.runtime.id||!sender.url?.startsWith('chrome-extension://'+chrome.runtime.id+'/'))return;
 const link=message.link;let u;try{u=new URL(link.base);}catch{respond({ok:false});return;}
 if(u.protocol!=='http:'||u.hostname!=='127.0.0.1'||!Number.isInteger(link.tabId)){respond({ok:false});return;}
 geminiConnectLink(link).then(respond,()=>respond({ok:false}));return true;
});
async function resumeGemini(){const all=(await chrome.storage.local.get('geminiLinks')).geminiLinks||{};for(const link of Object.values(all))geminiLoop(link);}
chrome.alarms.create('gemini-browser-resume',{periodInMinutes:.5});chrome.alarms.onAlarm.addListener(a=>{if(a.name==='gemini-browser-resume')resumeGemini();});resumeGemini();
