'use strict';
// Identity is read only in the explicitly paired Google tab. No cookies/tokens.
async function sceneForgeFlowIdentity(){
 const email=String(window.WIZ_global_data?.oPEP7c||'').trim().toLowerCase();
 if(!email.includes('@'))return {status:401,code:'FLOW_UI_IDENTITY'};
 const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(email));
 const project=location.pathname.match(location.hostname==='labs.google'?/^\/fx\/(?:[a-z]{2}(?:-[a-z]{2})?\/)?tools\/flow\/project\/([a-zA-Z0-9_-]+)\/?$/i:/^\/project\/([a-zA-Z0-9_-]+)\/?$/);
 const scope=project?await crypto.subtle.digest('SHA-256',new TextEncoder().encode(location.origin+'/project/'+project[1])):null;
 return {status:200,page_kind:project?'project':'home',project_hash:scope?Array.from(new Uint8Array(scope),x=>x.toString(16).padStart(2,'0')).join(''):null,email,account_hash:Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,'0')).join('')};
}
// Pure local workspace check; does not navigate, submit or change browser identity.
function sceneForgeFlowWorkspace(link,identity,request){
 if(['identity','release'].includes(request.action))return {ok:true};
 if(identity.page_kind!=='project'||!/^([a-f0-9]{64})$/.test(identity.project_hash||''))return {ok:false,uncertain:request.action!=='prepare'};
 if(link.project_hash&&link.project_hash!==identity.project_hash)return {ok:false,uncertain:request.action!=='prepare'};
 if(!link.project_hash&&request.action!=='prepare')return {ok:false,uncertain:true};
 return {ok:true,pin:link.project_hash?null:identity.project_hash};
}
function sceneForgeFlowWorkspaceFailure(){
 globalThis.__sceneForgeDomDiagnostic={adapter:'1.6.9',stage:'workspace_project',code:'FLOW_UI_CHANGED'};
 return {status:422,code:'FLOW_UI_CHANGED'};
}
// Executed in extension ISOLATED world: page JS cannot access request state/bytes.
async function sceneForgeDomFlow(req){
 let stage='start';
 const fail=(code,uncertain=false)=>{globalThis.__sceneForgeDomDiagnostic={adapter:'1.6.9',stage,code};return {status:422,code,uncertain};};
 const visible=e=>!!e&&e.getClientRects().length>0&&getComputedStyle(e).visibility!=='hidden';
 const label=e=>{
  const copy=e.cloneNode(true);copy.querySelectorAll('i,.material-symbols-outlined,.material-icons').forEach(n=>n.remove());
  const text=(copy.textContent||'').trim(),aria=(e.getAttribute('aria-label')||'').trim();
  // Model triggers can have generic accessible labels while their visible text
  // identifies the selected model. Match the same text as the UI diagnostic.
  return /^(Veo|Omni)\s*\d/i.test(text.normalize('NFKC'))||/^(Agent|Tác nhân|Video|Videos|Frames to Video|Frames|Khung hình|9\s*:\s*16|16\s*:\s*9|x\s*[1-4]|[468]\s*(?:s|giây)|10\s*(?:s|giây))$/i.test(text)?text:aria||text;
 };
 const textOnly=e=>{const copy=e.cloneNode(true);copy.querySelectorAll('i,.material-icons,.material-symbols-outlined').forEach(n=>n.remove());return(copy.textContent||'').normalize('NFKC').replace(/\s+/g,' ').trim();};
 const isSelected=e=>!!e&&(e.getAttribute('aria-selected')==='true'||e.getAttribute('aria-pressed')==='true'||e.getAttribute('aria-checked')==='true'||['active','checked','on'].includes(e.getAttribute('data-state')));
 const buttons=()=>Array.from(document.querySelectorAll('button,[role="button"],[role="menuitem"],[role="menuitemradio"],[role="menuitemcheckbox"],[role="option"]')).filter(visible);
 const unique=(items)=>items.length===1?items[0]:null;
 const match=re=>unique(buttons().filter(e=>re.test(label(e))));
 // Flow exposes fixed duration in a composer summary, not necessarily an 8s tab.
 const summary=()=>{
  const candidates=buttons().map(e=>({element:e,text:textOnly(e)})).filter(v=>/^Video\b/i.test(v.text)&&/\b\d{3,4}p\b/i.test(v.text)&&/\b\d+\s*(?:giây|seconds?|s\b)/i.test(v.text));
  if(candidates.length!==1)return null;
  const row=candidates[0],duration=row.text.match(/\b(\d+)\s*(?:giây|seconds?|s\b)/i),quantity=row.text.match(/\bx\s*([1-4])\b/i);
  return {...row,duration:duration?Number(duration[1]):null,quantity:quantity?Number(quantity[1]):null};
 };
 const sleep=ms=>new Promise(r=>setTimeout(r,ms));
 const until=async fn=>{for(let n=0;n<40;n++){const value=fn();if(value)return value;await sleep(250);}return null;};
 const verification=()=>Array.from(document.querySelectorAll('[role="alert"],[role="alertdialog"]')).filter(visible).some(e=>/unusual activity|hoạt động bất thường|PUBLIC_ERROR_UNUSUAL_ACTIVITY|verify you are human/i.test(e.textContent))||Array.from(document.querySelectorAll('iframe[src*="recaptcha"][src*="bframe"]')).some(visible);
 // Flow can report denial inside a result card without role=alert.
 // Require a failure heading + known activity message in a small visible card;
 // exclude editors so prompt text cannot be mistaken for a provider error.
 const activityCard=()=>{
  for(const heading of document.querySelectorAll('h1,h2,h3,h4,p,span,div')){
   if(!visible(heading)||heading.closest('textarea,input,[contenteditable],[role="textbox"]'))continue;
   if(!/^(Không thành công|Unsuccessful|Failed|Generation failed)$/i.test((heading.innerText||'').trim()))continue;
   let card=heading;
   for(let depth=0;card&&depth<6&&card!==document.body&&card!==document.documentElement;depth++,card=card.parentElement){
    if(card.querySelector('textarea,input,[contenteditable],[role="textbox"]'))break;
    const text=(card.innerText||'').normalize('NFC').replace(/\s+/g,' ').trim();
    if(text.length>2000)break;
    if(/hoạt động bất thường|unusual activity|unusual traffic|PUBLIC_ERROR_UNUSUAL_ACTIVITY/i.test(text)&&card.querySelector('button,[role="button"]'))return true;
   }
  }
  return false;
 };
 const videos=()=>Array.from(document.querySelectorAll('video')).filter(visible);
 const mediaKey=e=>e.currentSrc||e.src||'';
 const signature=()=>location.href;
 const store=globalThis.__sceneForgeDomJobs||(globalThis.__sceneForgeDomJobs=new Map());
 const rid=req.request_id;
 if(typeof rid!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(rid))return fail('FLOW_UI_REQUEST');
 let job=store.get(rid);
 if(req.action==='release'){store.delete(rid);return {status:200};}
 if(verification()||activityCard()){stage='flow_activity_denial';return fail('FLOW_UI_VERIFY',!!job?.sent);}
 if(req.action==='prepare'){
  if(job)return job.prepared?{status:200}:fail('FLOW_UI_CHANGED',!!job.sent);
  if(store.size>=4)return fail('FLOW_UI_BUSY');
  job={page:signature(),sent:false,prepared:false};store.set(rid,job);
  try{

   // ===== AGENT UI FLOW (rewritten) =====
   const sleepA = ms => new Promise(r => setTimeout(r, ms));
   const vis = e => !!(e && (e.offsetParent || e.getClientRects().length));
   const allBtns = () => Array.from(document.querySelectorAll('button,[role="button"],[role="menuitem"]')).filter(vis);
   const txt = e => ((e.innerText || e.textContent || e.getAttribute('aria-label') || '') + '').replace(/\s+/g, ' ').trim();
   const findBtn = re => allBtns().find(e => re.test(txt(e)));
   try {
     // 1. Close Agent settings panel if open
     if (/Agent settings/i.test(document.body.innerText || '')) {
       const closer = findBtn(/^(Close|Đóng|×|✕)$/i) || allBtns().find(e => /close/i.test(e.getAttribute('aria-label') || ''));
       if (closer) closer.click();
       await sleepA(600);
     }
     // 2. Click 9:16 if visible
     const b916 = findBtn(/^9\s*:\s*16$/);
     if (b916 && b916.getAttribute('aria-pressed') !== 'true') b916.click();
     await sleepA(300);
     // 3. Try image context menu → Animate
     const imgs = Array.from(document.querySelectorAll('img')).filter(e => vis(e) && (e.naturalWidth || 0) > 40);
     if (imgs.length) {
       const card = imgs[0].closest('button,[role="button"],div') || imgs[0];
       card.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, view: window }));
       await sleepA(500);
       const anim = findBtn(/^Animate$/i);
       if (anim) { anim.click(); await sleepA(800); }
     }
     // 4. If Agent chat box exists, ensure prompt will be sent as video request
     const box = document.querySelector('textarea,[contenteditable="true"]');
     if (box && req.prompt && !/create a video/i.test(box.value || box.innerText || '')) {
       const line = 'Create a video from this image. ' + req.prompt;
       if ('value' in box) { box.value = line; box.dispatchEvent(new Event('input', { bubbles: true })); }
     }
   } catch (e) { /* continue to legacy path */ }
   // ===== END AGENT UI FLOW =====

   // Agent UI is a separate composer.
   try{
    const headings=Array.from(document.querySelectorAll('h1,h2,h3,[role="heading"]'));
    const agentHead=headings.find(e=>/Agent settings/i.test((e.textContent||'').trim()));
    if(agentHead){
     const box=agentHead.closest('div,section,aside')||agentHead.parentElement;
     const closer=box&&Array.from(box.querySelectorAll('button')).find(b=>/close|đóng|×/i.test(b.getAttribute('aria-label')||b.textContent||''));
     if(closer)closer.click();
     else {const xs=box&&box.querySelector('button'); if(xs)xs.click();}
     await new Promise(r=>setTimeout(r,500));
    }
    const imgs=Array.from(document.querySelectorAll('img')).filter(e=>e.offsetParent&&(e.naturalWidth||0)>40);
    if(imgs.length){
     const card=imgs[0].closest('button,[role="button"],div')||imgs[0];
     card.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,view:window}));
     await new Promise(r=>setTimeout(r,500));
     const anim=Array.from(document.querySelectorAll('button,[role="menuitem"]')).find(e=>/^Animate$/i.test((e.textContent||'').trim()));
     if(anim){anim.click();await new Promise(r=>setTimeout(r,800));}
    }
   }catch(e){}
   // Agent UI is a separate composer. Toggle only when explicit pressed state says ON.
   const editorNodes=()=>Array.from(document.querySelectorAll('textarea,[contenteditable="true"],[contenteditable="plaintext-only"]')).filter(visible);
   const agentOff=async()=>{
    const agent=match(/^(Agent|Tác nhân)$/i);if(!agent)return true;
    const pressed=agent.getAttribute('aria-pressed');
    if(pressed==='false')return true;
    if(pressed!=='true')return false;
    agent.click();return !!await until(()=>match(/^(Agent|Tác nhân)$/i)?.getAttribute('aria-pressed')==='false');
   };
   const defaultsPanel=()=>Array.from(document.querySelectorAll('h1,h2,h3,h4,[role="heading"],label,p,span')).filter(visible).some(e=>/^(Agent settings|Cài đặt tác nhân|Video generation default|Thiết lập mặc định tạo video)$/i.test(e.textContent.trim()));
   stage='agent';
   if(defaultsPanel()){
    // In Agent settings: pick 9:16 for video then Save
    const v916=buttons().find(e=>/^9\s*:\s*16$/.test(label(e).replace(/\s/g,''))||label(e)==='9:16');
    if(v916){v916.click();await sleep(300);}
    const save=match(/^(Save|Lưu)$/i);
    if(save&&!save.disabled){save.click();await sleep(600);}
   }
   if(!defaultsPanel()&&!await agentOff())return fail('FLOW_UI_AGENT');
   // Prefer image menu → Animate (user-requested path)
   stage='animate_menu';
   const tryAnimate=async()=>{
    const imgs=Array.from(document.querySelectorAll('img')).filter(visible).filter(e=>e.naturalWidth>50);
    if(!imgs.length)return false;
    const card=imgs[0].closest('button,[role="button"],[role="listitem"],div')||imgs[0];
    card.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,view:window}));
    await sleep(400);
    let anim=match(/^Animate$/i)||buttons().find(e=>/Animate/i.test(label(e)));
    if(!anim){
     const dots=buttons().find(e=>/more|menu|⋮|options/i.test(label(e))||e.querySelector('i,.material-symbols-outlined'));
     if(dots){dots.click();await sleep(400);anim=match(/^Animate$/i)||buttons().find(e=>/^Animate$/i.test(textOnly(e)));}
    }
    if(anim){anim.click();await sleep(800);return true;}
    return false;
   };
   await tryAnimate();
   // Prefer image-animation / 9:16 over Agent defaults
   const click916=()=>{
    const b=buttons().find(e=>/^9\s*:\s*16$/.test(label(e).replace(/\s/g,''))||label(e)==='9:16');
    if(b&&b.getAttribute('aria-pressed')!=='true'&&b.getAttribute('aria-selected')!=='true'){b.click();return true;}
    return false;
   };
   click916();await sleep(400);
   const findSettings=()=>{
    const isSettings=e=>/^(Settings|Generation settings|Cài đặt|Cài đặt tạo|tune)$/i.test(label(e));
    const icon=e=>Array.from(e.querySelectorAll('i,.material-symbols-outlined,.material-icons')).some(i=>/^crop_|^tune$/.test(i.textContent.trim()));
    const candidates=buttons().filter(e=>isSettings(e)||icon(e)||e===summary()?.element),editors=editorNodes();
    if(editors.length===1){let node=editors[0].parentElement;
     for(let depth=0;node&&depth<7&&node!==document.body&&node!==document.documentElement;depth++,node=node.parentElement){const scoped=candidates.filter(e=>node.contains(e));if(scoped.length)return unique(scoped);}
    }
    return unique(candidates.filter(icon));
   };
   stage='settings_scope';const settings=findSettings();
   const hasVisibleModel=()=>buttons().some(e=>/^(Veo|Omni)\s*\d/i.test(label(e)));
   if(!settings&&!hasVisibleModel())return fail('FLOW_UI_SETTINGS');
   const paneAlreadyOpen=hasVisibleModel()&&Array.from(document.querySelectorAll('[role="dialog"],[role="menu"],[role="listbox"]')).some(visible);
   if(settings&&settings.getAttribute('aria-expanded')!=='true'&&!paneAlreadyOpen){
    stage='settings_open';settings.click();
    await until(()=>hasVisibleModel()||Array.from(document.querySelectorAll('[role="menu"],[role="dialog"],[role="listbox"]')).some(visible));
   }
   // Select Video before model; tolerate Frames-to-Video already selected.
   const mode=match(/^(Video|Videos|Video generation|Tạo video)$/i);
   if(mode&&mode.getAttribute('aria-selected')!=='true'&&mode.getAttribute('aria-pressed')!=='true'){mode.click();await sleep(300);}
   // The picker may render ordinary buttons instead of role=option.
   // Normalize only presentation characters, never substitute Fast/Quality for Lite.
   stage='model_scan';
   const modelLabel=e=>label(e).normalize('NFKC').replace(/[\u2010-\u2015\u2212\u00b7-]/g,' ').replace(/\b(?:expand_more|arrow_drop_down|keyboard_arrow_down|check)\b/g,' ').replace(/\s+/g,' ').trim();
   const isModel=e=>/^(Veo|Omni)\s*\d/i.test(modelLabel(e));
   const isLite=e=>/^Veo\s*3\.1\s*[-–—·]?\s*Lite(?:\s|$)/i.test(modelLabel(e));
   const optionRole=e=>!e.hasAttribute('aria-haspopup')&&(['option','menuitem','menuitemradio','menuitemcheckbox'].includes(e.getAttribute('role'))||!!e.closest('[role="menu"],[role="listbox"]'));
   const modelControls=()=>buttons().filter(isModel);
   const triggers=()=>modelControls().filter(e=>!optionRole(e));
   const selectedLite=()=>{const all=triggers();return all.length===1&&isLite(all[0]);};
   let picker=unique(triggers().filter(e=>e.hasAttribute('aria-haspopup')))||unique(triggers());
   const openOptions=()=>buttons().filter(e=>isLite(e)&&optionRole(e));
   if(!selectedLite()||openOptions().length){
    let choice=unique(openOptions());
    // A menu already opened by the user can contain plain <button> options.
    if(!choice&&modelControls().length>1)choice=unique(modelControls().filter(isLite));
    if(!choice&&picker){stage='model_open';picker.click();choice=await until(()=>unique(openOptions())||unique(modelControls().filter(e=>isLite(e)&&e!==picker)));}
    if(!choice){
    if(/Veo\s*3\.1\s*[-–—·]?\s*Lite/i.test(document.body.innerText||'')){/* accept */}
    else return fail('FLOW_UI_MODEL');
   }
    stage='model_select';choice.click();
    // React replaces dropdown nodes. Verify the selected trigger, not a stale option.
    if(!await until(selectedLite))return fail('FLOW_UI_MODEL');
   }
   if(!selectedLite()){
    const body=(document.body.innerText||'');
    if(!/Veo\s*3\.1\s*[-–—·]?\s*Lite/i.test(body))return fail('FLOW_UI_MODEL');
   }
   // Agent defaults are not the generation controls. Save the selected model,
   // return to the composer, then inspect actual duration/aspect/quantity.
   if(defaultsPanel()){
    stage='defaults_save';const save=match(/^(Save|Lưu)$/i);
    if(!save||save.disabled)return fail('FLOW_UI_SETTINGS');
    save.click();
    if(!await until(()=>!defaultsPanel()&&editorNodes().length===1))return fail('FLOW_UI_SETTINGS');
    stage='agent_after_defaults';if(!await agentOff())return fail('FLOW_UI_AGENT');
    const ready=()=>!!(match(/^8\s*(s|sec|seconds|giây)$/i)||summary()?.duration===8)&&[/^9\s*:\s*16$/,/^(x\s*1|1x|1)$/i].every(re=>match(re));
    if(!ready()){
     stage='generation_settings_open';const generationSettings=findSettings();
     if(!generationSettings)return fail('FLOW_UI_SETTINGS');
     generationSettings.click();await until(()=>ready()||defaultsPanel());
     // No loop back into defaults or assumption that defaults imply duration.
     if(defaultsPanel()||!ready())return fail('FLOW_UI_SETTINGS');
    }
    if(!selectedLite()){
    const body=(document.body.innerText||'');
    if(!/Veo\s*3\.1\s*[-–—·]?\s*Lite/i.test(body))return fail('FLOW_UI_MODEL');
   }
   }
   stage='video_settings';
   const frameMode=unique(Array.from(document.querySelectorAll('button[id$="-trigger-VIDEO_FRAMES"],button[role="tab"][aria-controls*="VIDEO_FRAMES"]')).filter(visible))||match(/^(Frames to Video|Frames|Khung hình thành video|Khung hình)$/i);
   if(frameMode&&!isSelected(frameMode)){frameMode.click();if(!await until(()=>{const node=match(/^(Frames to Video|Frames|Khung hình thành video|Khung hình)$/i);return isSelected(node);}))return fail('FLOW_UI_SETTINGS');}
   const durationTab=match(/^8\s*(s|sec|seconds|giây)$/i);
   if(durationTab){if(!isSelected(durationTab)){durationTab.click();if(!await until(()=>isSelected(match(/^8\s*(s|sec|seconds|giây)$/i))))return fail('FLOW_UI_SETTINGS');}}
   else {
    const s=summary();
    if(!s||s.duration!==8){
     const b=match(/^8\s*(s|sec|seconds|giây)$/i);if(b)b.click();
     const p=match(/^9\s*:\s*16$/);if(p)p.click();
     await sleep(400);
     if(summary()?.duration!==8)return fail('FLOW_UI_SETTINGS');
    }
   }
   // Ratio and quantity must still be selected explicitly in the VIDEO panel.
   for(const re of [/^9\s*:\s*16$/,/^(x\s*1|1x|1)$/i]){
    const option=match(re);if(!option)return fail('FLOW_UI_SETTINGS');
    if(!isSelected(option)){option.click();if(!await until(()=>isSelected(match(re))))return fail('FLOW_UI_SETTINGS');}
   }
   if(summary()&&!await until(()=>{const value=summary();return value?.duration===8&&value?.quantity===1;}))return fail('FLOW_UI_SETTINGS');
   // Close settings using Escape, then re-query nodes after React remounts.
   document.activeElement?.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',code:'Escape',bubbles:true}));
   const frames=unique(Array.from(document.querySelectorAll('button[id$="-trigger-VIDEO_FRAMES"],button[role="tab"][aria-controls*="VIDEO_FRAMES"]')).filter(visible))||match(/^(Frames to Video|Frames|Khung hình thành video|Khung hình)$/i);
   if(frames&&!isSelected(frames)){frames.click();await sleep(300);}
   const image=req.image;
   if(!image||!['image/png','image/jpeg','image/webp'].includes(image.mime_type)||typeof image.data!=='string'||image.data.length>9*1024*1024)return fail('FLOW_UI_IMAGE');
   let field=unique(Array.from(document.querySelectorAll('input[type="file"]')).filter(e=>/image|\.png|\.jpg|\.webp/i.test(e.accept)));
   if(!field){const upload=match(/^(Upload image|Upload media|Tải ảnh|Tải nội dung nghe nhìn|Add image|Thêm ảnh)$/i);if(upload){upload.click();await sleep(300);field=unique(Array.from(document.querySelectorAll('input[type="file"]')).filter(e=>/image|\.png|\.jpg|\.webp/i.test(e.accept)));}}
   if(!field)return fail('FLOW_UI_IMAGE');
   const bytes=Uint8Array.from(atob(image.data),c=>c.charCodeAt(0));
   const dt=new DataTransfer();dt.items.add(new File([bytes],'sceneforge-start.'+({'image/png':'png','image/jpeg':'jpg','image/webp':'webp'}[image.mime_type]),{type:image.mime_type}));
   field.files=dt.files;field.dispatchEvent(new Event('change',{bubbles:true}));
   const editor=await until(()=>unique(Array.from(document.querySelectorAll('textarea,[contenteditable="true"],[contenteditable="plaintext-only"]')).filter(visible)));
   if(!editor||typeof req.prompt!=='string'||!req.prompt.trim())return fail('FLOW_UI_EDITOR');
   editor.focus();
   if(editor.tagName==='TEXTAREA'){
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(editor,req.prompt);editor.dispatchEvent(new Event('input',{bubbles:true}));
   }else{
    const range=document.createRange();range.selectNodeContents(editor);const sel=getSelection();sel.removeAllRanges();sel.addRange(range);
    if(!document.execCommand('insertText',false,req.prompt))return fail('FLOW_UI_EDITOR');
   }
   await sleep(500);
   if((editor.value??editor.innerText).trim()!==req.prompt.trim())return fail('FLOW_UI_EDITOR');
   // Need an uploaded image preview in the same composer, not an unrelated library image.
   const container=editor.closest('form')||editor.closest('[data-testid*="composer"]')||editor.parentElement?.parentElement;
   if(!container||!await until(()=>Array.from(container.querySelectorAll('img')).filter(e=>visible(e)&&e.complete&&e.naturalWidth>0).length===1))return fail('FLOW_UI_IMAGE');
   const submit=unique(Array.from(container.querySelectorAll('button,[role="button"]')).filter(e=>visible(e)&&/^(Generate|Create|Create video|Tạo|Tạo video|Send|Gửi|arrow_forward)$/i.test(label(e))&&!e.disabled));
   if(!submit)return fail('FLOW_UI_SUBMIT');
   job.editor=editor;job.submit=submit;job.prompt=req.prompt;job.baseline=new Set(videos().map(mediaKey));job.prepared=true;
   return {status:200};
  }finally{if(!job.prepared)store.delete(rid);}
 }
 if(!job||job.page!==signature())return fail('FLOW_UI_CHANGED',true);
 if(req.action==='submit'){
  if(job.sent)return fail('FLOW_UI_CHANGED',true);
  if(!job.prepared||!job.submit.isConnected||job.submit.disabled||!job.editor.isConnected||(job.editor.value??job.editor.innerText).trim()!==job.prompt.trim())return fail('FLOW_UI_CHANGED');
  job.sent=true;job.submit.click();return {status:200};
 }
 if(req.action==='status'){
  if(!job.sent)return fail('FLOW_UI_CHANGED');
  if(job.bytes)return {status:200,ready:true,bytes:job.bytes.length,sha256:job.sha256};
  const fresh=videos().filter(e=>mediaKey(e)&&!job.baseline.has(mediaKey(e)));
  if(fresh.length>1)return fail('FLOW_UI_RESULTS',true);
  if(!fresh.length)return {status:200,ready:false};
  const url=new URL(mediaKey(fresh[0]),location.href);
  const allowed=url.protocol==='blob:'&&url.origin===location.origin||url.protocol==='https:'&&(url.origin===location.origin||/^(?:storage\.googleapis\.com|(?:[a-z0-9-]+\.)*googleusercontent\.com|(?:[a-z0-9-]+\.)*googlevideo\.com|flow-content\.google)$/.test(url.hostname));
  if(!allowed)return fail('FLOW_UI_DOWNLOAD',true);
  try{
   const response=await fetch(url.href,{credentials:'same-origin',redirect:'error',signal:AbortSignal.timeout(60000)});
   if(!response.ok||!response.body)return fail('FLOW_UI_DOWNLOAD',true);
   const reader=response.body.getReader(),chunks=[];let size=0;
   while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>100*1024*1024){await reader.cancel();return fail('FLOW_UI_DOWNLOAD',true);}chunks.push(value);}
   if(!size)return fail('FLOW_UI_DOWNLOAD',true);
   job.bytes=new Uint8Array(size);let offset=0;for(const part of chunks){job.bytes.set(part,offset);offset+=part.length;}
   job.sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',job.bytes)),v=>v.toString(16).padStart(2,'0')).join('');
   return {status:200,ready:true,bytes:size,sha256:job.sha256};
  }catch{return fail('FLOW_UI_DOWNLOAD',true);}
 }
 if(req.action==='chunk'){
  if(!job.bytes||!Number.isInteger(req.offset)||req.offset<0||req.offset>=job.bytes.length)return fail('FLOW_UI_DOWNLOAD',true);
  const part=job.bytes.subarray(req.offset,req.offset+1024*1024);let text='';for(let i=0;i<part.length;i+=8192)text+=String.fromCharCode(...part.subarray(i,i+8192));
  return {status:200,data:btoa(text)};
 }
 return fail('FLOW_UI_REQUEST');
}
