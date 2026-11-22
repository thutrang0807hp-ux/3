'use strict';
// This runs only in the explicitly paired Flow tab. No arbitrary target URLs.
async function sceneForgeNativeFlow(request,expectedHash,timeout){
 const fail=(status,code,uncertain=false)=>({status,code,uncertain});
 if(location.origin!=='https://flow.google.com')return fail(409,'FLOW_BROWSER_ACCOUNT_CHANGED');
 const wiz=window.WIZ_global_data||{},html=document.documentElement.innerHTML;
 const read=key=>{const value=wiz[key];if(typeof value==='string'||typeof value==='number')return String(value);const m=html.match(new RegExp('"'+key+'"\\s*:\\s*("(?:[^"\\\\]|\\\\.)*"|-?[0-9]+)'));if(!m)return '';try{return String(JSON.parse(m[1]));}catch{return '';}};
 const email=read('oPEP7c');
 if(!email.includes('@'))return fail(401,'FLOW_BROWSER_REQUEST_FAILED');
 const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(email.toLowerCase().trim()));
 const accountHash=Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('');
 if(expectedHash&&expectedHash!==accountHash)return fail(409,'FLOW_BROWSER_ACCOUNT_CHANGED');
 const build=html.match(/boq_labs-ai-sandbox-frontend_[A-Za-z0-9_.-]+/)?.[0]||read('cfb2h'),sid=read('FdrFJe'),xsrf=read('SNlM0e');
 if(!/^[A-Za-z0-9_.-]+$/.test(build)||!/^[-]?\d+$/.test(sid)||!xsrf)return fail(401,'FLOW_BROWSER_REQUEST_FAILED');
 if(request.kind==='bootstrap')return {status:200,email,account_hash:accountHash};
 if(request.kind==='captcha'){
  if(!['IMAGE_GENERATION','VIDEO_GENERATION','UPLOAD_IMAGE'].includes(request.action))return fail(400,'FLOW_BROWSER_REQUEST_FAILED');
  try{
   const existing=Array.from(document.scripts).map(s=>s.src).find(s=>s.includes('/recaptcha/enterprise.js'));
   const sitekey=existing?new URL(existing).searchParams.get('render'):'6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV';
   if(!sitekey||sitekey==='explicit')return fail(403,'FLOW_BROWSER_REQUEST_FAILED');
   if(!window.grecaptcha?.enterprise){
    await Promise.race([new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='https://www.google.com/recaptcha/enterprise.js?render='+encodeURIComponent(sitekey);s.onload=resolve;s.onerror=reject;document.head.append(s);}),new Promise((_,reject)=>setTimeout(reject,15000))]);
   }
   const token=await new Promise((resolve,reject)=>{window.grecaptcha.enterprise.ready(()=>window.grecaptcha.enterprise.execute(sitekey,{action:request.action}).then(resolve,reject));setTimeout(()=>reject(Error('timeout')),45000);});
   return typeof token==='string'&&token?{status:200,token,account_hash:accountHash}:fail(403,'FLOW_BROWSER_REQUEST_FAILED');
  }catch{return fail(403,'FLOW_BROWSER_REQUEST_FAILED');}
 }
 if(!['rpc','stream'].includes(request.kind))return fail(400,'FLOW_BROWSER_REQUEST_FAILED');
 if(request.kind==='rpc'&&(!/^[A-Za-z0-9]{1,16}$/.test(request.rpc_id)||!Array.isArray(request.argument)))return fail(400,'FLOW_BROWSER_REQUEST_FAILED');
 if(request.kind==='stream'&&typeof request.f_request!=='string')return fail(400,'FLOW_BROWSER_REQUEST_FAILED');
 const path=request.kind==='rpc'?'/_/AiSandboxAngularFrontend/data/batchexecute':'/_/AiSandboxAngularFrontend/data/google.internal.labs.aisandbox.proto.flow.agent.v1.FlowCreationAgentService/StreamChat';
 const url=new URL(path,location.origin),index=new URL(location.href).searchParams.get('authuser');
 for(const[k,v]of Object.entries({bl:build,'f.sid':sid,hl:'en',_reqid:String(Math.floor(Math.random()*80000)+10000),rt:'c'}))url.searchParams.set(k,v);
 if(index&&/^\d{1,3}$/.test(index))url.searchParams.set('authuser',index);
 if(request.kind==='rpc'){url.searchParams.set('rpcids',request.rpc_id);url.searchParams.set('source-path',location.pathname);}
 const body=new URLSearchParams({'f.req':request.kind==='rpc'?JSON.stringify([[[request.rpc_id,JSON.stringify(request.argument),null,'generic']]]):request.f_request,at:xsrf});
 try{
  const response=await fetch(url.href,{method:'POST',credentials:'include',redirect:'error',cache:'no-store',headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8','x-same-domain':'1'},body:body.toString(),signal:AbortSignal.timeout(Math.min(Math.max(timeout||90,5),250)*1000)});
  const text=await response.text();if(text.length>20*1024*1024)return fail(502,'FLOW_BROWSER_OUTCOME_UNKNOWN',true);
  return {status:response.status,text,account_hash:accountHash};
 }catch{return fail(504,'FLOW_BROWSER_OUTCOME_UNKNOWN',true);}
}
