'use strict';
const form=document.querySelector('#connect'),button=document.querySelector('#submit'),status=document.querySelector('#status');
function note(text,state=''){status.textContent=text;status.dataset.state=state;}
async function send(base,path,body){
 const response=await fetch(base+'/local-api/browser-bridge/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-SceneForge-Bridge':'1'},body:JSON.stringify(body),credentials:'omit',cache:'no-store',redirect:'error',signal:AbortSignal.timeout(20000)});
 let data;try{data=await response.json();}catch{throw Error('App chưa phản hồi đúng. Kiểm tra SceneForge đang mở và cổng kết nối.');}
 if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Chưa kết nối được với app.');
 return data;
}
form.addEventListener('submit',async event=>{
 event.preventDefault();const code=document.querySelector('#code').value.trim(),port=Number(document.querySelector('#port').value);
 if(!/^\d{8}$/.test(code)||!Number.isInteger(port)||port<1024||port>65535)return note('Nhập mã 8 chữ số và cổng do app cung cấp.','error');
 button.disabled=true;let cookies=null;
 try{
  const base='http://127.0.0.1:'+port;
  note('Đang đối chiếu mã với SceneForge…');
  const pair=await send(base,'claim',{code});
  const services=pair.services||[pair.service];if(!services.length||services.some(s=>!['gemini_chat','flow'].includes(s)))throw Error('Nguồn không được tiện ích hỗ trợ.');
  const targets=[...new Set(services.flatMap(s=>s==='gemini_chat'?['https://gemini.google.com/']:['https://google.com/','https://flow.google.com/','https://flow.google.com/projects','https://labs.google/fx/tools/flow']))];
  if(!targets)throw Error('Nguồn không được tiện ích hỗ trợ.');
  note('Đang chuyển phiên '+(services.length===2?'Gemini Chat + Flow':pair.service==='gemini_chat'?'Gemini Chat':'Flow')+' · '+pair.name+'…');
  const unique=new Map();
  let browser_context=null;
  if(services.includes('flow')){
   const tabs=await chrome.tabs.query({url:'https://flow.google.com/*',currentWindow:true});
   const active=tabs.find(t=>t.active)|| (tabs.length===1?tabs[0]:null);
   let authuser;
   if(active?.url){const u=new URL(active.url),index=u.searchParams.get('authuser');if(index&&/^\d{1,3}$/.test(index))authuser=index;}
   browser_context={user_agent:navigator.userAgent,...(authuser?{authuser}:{})};
  }
  const allowed=new Set(services.flatMap(s=>s==='gemini_chat'?['google.com','gemini.google.com']:['google.com','flow.google.com','labs.google']));
  const filters=targets.map(url=>({url}));
  // URL queries exclude cookies scoped to /_/ (the actual RPC path). Import
  // every Flow path while retaining original scope for the SDK cookie jar.
  if(services.includes('flow'))filters.push({domain:'flow.google.com'},{domain:'google.com'});
  for(const filter of filters){
   for(const c of await chrome.cookies.getAll(filter)){
    if(!allowed.has(c.domain.replace(/^\./,'')))continue;
    if(c.partitionKey||c.partitionKeyOpaque)continue;
    unique.set(c.domain+'|'+c.path+'|'+c.name,{name:c.name,value:c.value,domain:c.domain,path:c.path,secure:c.secure,httpOnly:c.httpOnly,hostOnly:c.hostOnly,sameSite:({no_restriction:'None',lax:'Lax',strict:'Strict'}[c.sameSite]),...(Number.isFinite(c.expirationDate)?{expires:c.expirationDate}:{})});
   }
  }
  cookies=[...unique.values()];
  if(services.length===1&&pair.service==='gemini_chat'&&!cookies.some(c=>c.name==='__Secure-1PSID'&&c.value))throw Error('Chưa thấy phiên Gemini trong trình duyệt này. Mở gemini.google.com và đăng nhập, rồi tạo mã mới trong SceneForge.');
  await send(base,'complete',{code,submission:pair.submission,cookies,protocol:2,...(browser_context?{browser_context}:{})});
  note('Đã chuyển phiên. Quay lại SceneForge để xem kết quả kiểm tra. Chưa thử tạo ảnh/video.','done');
  form.hidden=true;
 }catch(error){note(error instanceof TypeError?'Không liên lạc được với SceneForge. Mở app và kiểm tra cổng ở cạnh mã kết nối.':error.message,'error');}
 finally{cookies=null;button.disabled=false;}
});

const probeButton=document.querySelector('#probeFlow'),probeReport=document.querySelector('#probeReport'),copyProbe=document.querySelector('#copyProbe');
probeButton.addEventListener('click',async()=>{
 probeButton.disabled=true;probeReport.hidden=false;copyProbe.hidden=true;probeReport.value='Đang đọc hạn mức trong tab Flow…';
 let report;
 try{
  const tabs=await chrome.tabs.query({url:'https://flow.google.com/*',currentWindow:true});
  const tab=tabs.find(t=>t.active)||(tabs.length===1?tabs[0]:null);
  if(!tab)report={probe_version:1,code:'FLOW_BROWSER_SELECT_TAB',generated_content:false};
  else{
   const answers=await chrome.scripting.executeScript({target:{tabId:tab.id},world:'MAIN',func:sceneForgeFlowProbe});
   report=answers[0]?.result||{probe_version:1,code:'FLOW_BROWSER_NO_RESULT',generated_content:false};
  }
 }catch{report={probe_version:1,code:'FLOW_BROWSER_SCRIPT_PERMISSION_OR_TAB_ERROR',generated_content:false};}
 probeReport.value=JSON.stringify(report,null,2);copyProbe.hidden=false;probeButton.disabled=false;
});
copyProbe.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(probeReport.value);copyProbe.textContent='Đã chép báo cáo';}catch{probeReport.focus();probeReport.select();}});
