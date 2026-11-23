/* Automatic local-app discovery. No pairing code, Google cookies or SDK login. */
let geminiDiscoverBusy=false,geminiAutoMessage='Đang tìm SceneForge trên máy…';
async function geminiAutoConnect(extraBase){
 if(geminiDiscoverBusy)return;geminiDiscoverBusy=true;
 try{
  const saved=await chrome.storage.local.get('geminiAuto');const cfg=saved.geminiAuto||{installation_id:crypto.randomUUID(),bases:[]};
  if(extraBase){const u=new URL(extraBase);if(u.protocol==='http:'&&['127.0.0.1','localhost'].includes(u.hostname)&&Number(u.port)>=1024)cfg.bases=[...new Set([...cfg.bases,'http://127.0.0.1:'+u.port])].slice(-5);}
  await chrome.storage.local.set({geminiAuto:cfg});
  const bases=[...new Set(['http://127.0.0.1:8840',...cfg.bases])];
  let found=false;
  for(const base of bases){
   try{
    const r=await fetch(base+'/local-api/browser-bridge/gemini-discover',{method:'POST',credentials:'omit',redirect:'error',headers:{'Content-Type':'application/json','X-SceneForge-Bridge':'1'},body:JSON.stringify({installation_id:cfg.installation_id,version:chrome.runtime.getManifest().version}),signal:AbortSignal.timeout(1500)});
    if(!r.ok)continue;const reply=await r.json();if(reply.service!=='sceneforge-gemini-browser'||!reply.relay)continue;found=true;geminiAutoMessage=reply.ready?'Đã tự kết nối với SceneForge.':'Đã nhận app, đang kiểm tra tab Gemini…';
    const links=(await chrome.storage.local.get('geminiLinks')).geminiLinks||{};let link=links[reply.relay.id];let tab;
    if(link){try{tab=await chrome.tabs.get(link.tabId);if(!tab.url?.startsWith('https://gemini.google.com/'))tab=null;}catch{}}
    if(!tab&&cfg.pendingTabId){try{const candidate=await chrome.tabs.get(cfg.pendingTabId);if(candidate.url?.startsWith('https://gemini.google.com/'))tab=candidate;else{geminiAutoMessage='Đăng nhập Gemini trong tab trình duyệt đã mở.';continue;}}catch{delete cfg.pendingTabId;}}
    if(!tab){const tabs=await chrome.tabs.query({url:'https://gemini.google.com/*'});tab=tabs.find(t=>t.active)||tabs[0];if(!tab){tab=await chrome.tabs.create({url:'https://gemini.google.com/app',active:false});cfg.pendingTabId=tab.id;await chrome.storage.local.set({geminiAuto:cfg});}}
    if(!tab.url?.startsWith('https://gemini.google.com/'))continue;
    link={...reply.relay,base,tabId:tab.id};
    await geminiConnectLink(link);
   }catch{}
  }
  if(!found)geminiAutoMessage='Chưa thấy SceneForge. Mở app để tiện ích tự nhận.';
 }finally{geminiDiscoverBusy=false;}
}
chrome.runtime.onMessage.addListener((message,sender,respond)=>{
 if(message?.type==='sceneforge-auto-now'&&sender.id===chrome.runtime.id&&sender.url?.startsWith('chrome-extension://'+chrome.runtime.id+'/')){geminiAutoConnect().then(()=>respond({ok:true,message:geminiAutoMessage}));return true;}
 if(message?.type!=='sceneforge-auto-discover'||sender.id!==chrome.runtime.id||sender.frameId!==0)return;
 try{const u=new URL(sender.url);if(u.protocol!=='http:'||!['127.0.0.1','localhost'].includes(u.hostname))return;geminiAutoConnect(u.origin).then(()=>respond({ok:true}),()=>respond({ok:false}));return true;}catch{}
});
chrome.alarms.create('gemini-auto-discover',{periodInMinutes:.5});
chrome.alarms.onAlarm.addListener(a=>{if(a.name==='gemini-auto-discover')geminiAutoConnect();});
chrome.tabs.onUpdated.addListener((id,info,tab)=>{if(info.status==='complete'&&tab.url?.startsWith('https://gemini.google.com/'))geminiAutoConnect();});
chrome.runtime.onStartup.addListener(()=>geminiAutoConnect());
geminiAutoConnect();
// Fast discovery while this worker is active; Chrome's alarm resumes it after suspension.
setInterval(()=>geminiAutoConnect(),5000);
