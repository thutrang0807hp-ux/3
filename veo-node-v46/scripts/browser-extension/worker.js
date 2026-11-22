function flowTabUrl(url){try{const u=new URL(url);return u.protocol==='https:'&&(u.hostname==='flow.google.com'||u.hostname==='labs.google'&&u.pathname.startsWith('/fx/'));}catch{return false;}}
'use strict';
importScripts('native-flow.js','dom-flow.js');
const running=new Set();
async function wire(link,path,extra={}){
 const response=await fetch(link.base+'/local-api/browser-bridge/flow-'+path,{method:'POST',headers:{'Content-Type':'application/json','X-SceneForge-Bridge':'1'},credentials:'omit',cache:'no-store',redirect:'error',body:JSON.stringify({id:link.id,key:link.browser_key,...extra}),signal:AbortSignal.timeout(path==='poll'?20000:30000)});
 if(response.status===403){await remove(link.id);throw Error('revoked');}
 if(!response.ok)throw Error('bridge');return response.json();
}
async function links(){return (await chrome.storage.session.get('flowLinks')).flowLinks||{};}
async function save(link){const all=await links();all[link.id]=link;await chrome.storage.session.set({flowLinks:all});}
async function remove(id){const all=await links();delete all[id];await chrome.storage.session.set({flowLinks:all});}
async function loop(link){
 if(running.has(link.id))return;running.add(link.id);
 try{
  while((await links())[link.id]){
   let packet;
   try{packet=await wire(link,'poll');}catch{
    if(!(await links())[link.id])break;
    await new Promise(resolve=>setTimeout(resolve,3000));continue;
   }
   if(!packet.job)continue;
   const job=packet.job;let result;
   try{
    const tab=await chrome.tabs.get(link.tabId);
    if(!flowTabUrl(tab.url))throw Error('tab');
    let results;
    if(link.ui){
     if(job.request.kind!=='ui')throw Error('UI route refuses native RPC');
     const identity=(await chrome.scripting.executeScript({target:{tabId:link.tabId},world:'MAIN',func:sceneForgeFlowIdentity}))[0]?.result;
     if(!identity?.account_hash||identity.account_hash!==link.account_hash){result={status:409,code:'FLOW_BROWSER_ACCOUNT_CHANGED'};}
     else if(job.request.action==='identity')result={status:200,...identity};
     else{
      const workspace=sceneForgeFlowWorkspace(link,identity,job.request);
      if(!workspace.ok){
       await chrome.scripting.executeScript({target:{tabId:link.tabId},world:'ISOLATED',func:sceneForgeFlowWorkspaceFailure});
       result={status:422,code:'FLOW_UI_CHANGED',uncertain:workspace.uncertain};
      }else{
       if(workspace.pin){link.project_hash=workspace.pin;await save(link);}
       results=await chrome.scripting.executeScript({target:{tabId:link.tabId},world:'ISOLATED',func:sceneForgeDomFlow,args:[job.request]});
      }
     }
    }else results=await chrome.scripting.executeScript({target:{tabId:link.tabId},world:'MAIN',func:sceneForgeNativeFlow,args:[job.request,link.account_hash||'',job.timeout]});
    result=result||results?.[0]?.result||{status:503,code:'FLOW_BROWSER_UNAVAILABLE'};
    if(result.account_hash){
     if(link.account_hash&&link.account_hash!==result.account_hash)result={status:409,code:'FLOW_BROWSER_ACCOUNT_CHANGED'};
     else if(!link.account_hash){link.account_hash=result.account_hash;await save(link);}
    }
   }catch{result={status:503,code:'FLOW_BROWSER_UNAVAILABLE',uncertain:true};}
   try{await wire(link,'result',{job_id:job.id,result});}catch{break;}
   if([409,503].includes(result.status)){try{await wire(link,'disconnect');}catch{}await remove(link.id);break;}
  }
 }finally{running.delete(link.id);}
}
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
 if(sender.id!==chrome.runtime.id||message?.type!=='pairFlow')return;
 (async()=>{
  const link=message.link,base=new URL(link.base);
  if(base.protocol!=='http:'||base.hostname!=='127.0.0.1'||!Number.isInteger(link.tabId)||!/^[-_A-Za-z0-9]{20,80}$/.test(link.id)||!/^[-_A-Za-z0-9]{32,100}$/.test(link.browser_key))throw Error('invalid');
  // Pin identity now, before any engine work or later account change.
  const tab=await chrome.tabs.get(link.tabId);if(!flowTabUrl(tab.url))throw Error('tab');
  const result=await chrome.scripting.executeScript({target:{tabId:link.tabId},world:'MAIN',func:link.ui?sceneForgeFlowIdentity:sceneForgeNativeFlow,args:link.ui?[]:[{kind:'bootstrap'},'',30]});
  const meta=result[0]?.result;if(meta?.status!==200||!meta.account_hash)throw Error('Flow tab not signed in');
  link.account_hash=meta.account_hash;
  if(link.ui){link.project_hash=meta.project_hash||null;link.page_kind=meta.page_kind;}
  await save(link);
  await wire(link,'poll',{hello:true});
  void loop(link);return {ok:true};
 })().then(reply,()=>reply({ok:false}));return true;
});
chrome.alarms.onAlarm.addListener(async alarm=>{if(alarm.name==='flowRelay')for(const link of Object.values(await links())){try{await wire(link,'poll',{hello:true});}catch{}void loop(link);}});
chrome.alarms.create('flowRelay',{periodInMinutes:0.5});
chrome.runtime.onStartup.addListener(()=>chrome.storage.session.remove('flowLinks'));
