'use strict';
// Executed in the user's Flow tab, only after an explicit popup button click.
// Return fixed diagnostics, never cookies, tokens, HTML, email or response text.
async function sceneForgeFlowProbe(){
 const result={probe_version:1,generated_content:false,origin_is_flow:location.origin==='https://flow.google.com'};
 const done=(code,more={})=>({...result,code,...more});
 if(!result.origin_is_flow)return done('FLOW_BROWSER_WRONG_TAB');
 try{
  const wiz=window.WIZ_global_data||{},html=document.documentElement.innerHTML;
  const read=(key)=>{
   const val=wiz[key];if(typeof val==='string'||typeof val==='number')return String(val);
   const match=html.match(new RegExp('"'+key+'"\\s*:\\s*("(?:[^"\\\\]|\\\\.)*"|-?[0-9]+)'));
   if(!match)return '';try{return String(JSON.parse(match[1]));}catch{return '';}
  };
  const build=html.match(/boq_labs-ai-sandbox-frontend_[A-Za-z0-9_.-]+/)?.[0]||(/^[A-Za-z0-9_.-]+$/.test(read('cfb2h'))?read('cfb2h'):'');
  const sid=read('FdrFJe'),xsrf=read('SNlM0e');
  Object.assign(result,{has_build:!!build,has_session_id:/^-?\d+$/.test(sid),has_xsrf:!!xsrf,signed_in_hint:!!read('oPEP7c')});
  if(!result.has_build||!result.has_session_id||!result.has_xsrf)return done('FLOW_BROWSER_METADATA_MISSING');
  const url=new URL('/_/AiSandboxAngularFrontend/data/batchexecute',location.origin);
  for(const [k,v]of Object.entries({rpcids:'nzlxg','source-path':location.pathname,bl:build,'f.sid':sid,hl:'en',_reqid:'12345',rt:'c'}))url.searchParams.set(k,v);
  const index=new URL(location.href).searchParams.get('authuser');
  if(index&&/^\d{1,3}$/.test(index))url.searchParams.set('authuser',index);
  const body=new URLSearchParams({'f.req':JSON.stringify([[['nzlxg','[]',null,'generic']]]),at:xsrf});
  const response=await fetch(url.href,{method:'POST',credentials:'include',redirect:'error',cache:'no-store',headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8','x-same-domain':'1'},body:body.toString(),signal:AbortSignal.timeout(20000)});
  result.http_status=response.status;
  if(!response.ok)return done('FLOW_BROWSER_HTTP_REJECTED');
  const text=await response.text();if(text.length>1024*1024)return done('FLOW_BROWSER_RESPONSE_TOO_LARGE');
  const frames=[];
  // Google batchexecute uses XSSI + length-prefixed JSON lines.
  for(const line of text.split('\n')){if(!line.trim().startsWith('['))continue;try{const frame=JSON.parse(line);if(Array.isArray(frame))frames.push(frame);}catch{}}
  let payloadPresent=false;
  for(const frame of frames){
   for(const item of frame){
    if(!Array.isArray(item))continue;
    if(item[0]==='er'&&Number.isInteger(item[5]))result.rpc_error=item[5];
    if(item[0]==='wrb.fr'&&item[1]==='nzlxg'&&typeof item[2]==='string'){
     try{const payload=JSON.parse(item[2]);payloadPresent=Array.isArray(payload)&&payload.some(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0);}catch{}
    }
   }
  }
  if(result.rpc_error===401)return done('FLOW_BROWSER_RPC_AUTH_REJECTED');
  if(result.rpc_error)return done('FLOW_BROWSER_RPC_REJECTED');
  return done(payloadPresent?'FLOW_BROWSER_CREDIT_OK':'FLOW_BROWSER_RESPONSE_UNRECOGNIZED');
 }catch{return done('FLOW_BROWSER_REQUEST_FAILED');}
}
