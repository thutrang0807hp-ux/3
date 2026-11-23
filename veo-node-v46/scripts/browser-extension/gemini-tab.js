/* Browser transport adapted from the user's test-gemoni-chat 0.2.2 DOM mechanism.
   SceneForge retains scene/prompt/reference ownership; this function performs one turn only. */
async function sceneForgeGeminiTab(request){
 const wait=ms=>new Promise(r=>setTimeout(r,ms)),visible=e=>e.getClientRects().length>0;
 const editor=()=>[...document.querySelectorAll('rich-textarea [contenteditable="true"],.ql-editor[contenteditable="true"],[contenteditable="true"][role="textbox"]')].find(visible);
 const queries=()=>[...document.querySelectorAll('user-query,.user-query')].filter(e=>!e.parentElement?.closest('user-query,.user-query'));
 const responses=()=>[...document.querySelectorAll('model-response,.model-response-text')].filter(e=>!e.parentElement?.closest('model-response,.model-response-text'));
 const button=re=>[...document.querySelectorAll('button')].find(e=>visible(e)&&!e.disabled&&e.getAttribute('aria-disabled')!=='true'&&re.test(e.getAttribute('aria-label')||e.title||e.textContent||''));
 const until=async(fn,ms)=>{const end=Date.now()+ms;do{const r=fn();if(r)return r;await wait(250);}while(Date.now()<end);};
 let sent=false;
 try{
  const input=await until(editor,20000);if(!input)return {ok:false,accepted:false,code:'GEMINI_BROWSER_OFFLINE'};
  if(request.operation==='identity')return {ok:true};
  const images=node=>{
  const candidates=[...(node?.querySelectorAll('img')||[])].filter(i=>i.closest('generated-image,single-image,image-generation,generated-image-container')||/^blob:|^data:image\//.test(i.currentSrc||i.src)||/^https:\/\/[^/]+\.googleusercontent\.com\//.test(i.currentSrc||i.src));
  for(const i of candidates){if(!i.complete||i.naturalWidth<256){i.loading='eager';i.scrollIntoView({block:'center',behavior:'instant'});}}
  return candidates.filter(i=>i.complete&&i.naturalWidth>=256&&i.naturalHeight>=256);
 };
  let latest;
  if(request.operation==='receive'){
   sent=true;latest=()=>{
    const marked=request.target_job&&document.querySelector('[data-sf-gemini-turn="'+CSS.escape(request.target_job)+'"]');
    if(marked?.isConnected&&images(marked).length)return marked;
    const responsesNow=responses().filter(visible);
    if(document.documentElement.getAttribute('data-sf-gemini-owner')!==request.target_job)return request.owned_single_turn&&responsesNow.length===1?responsesNow[0]:null;
    const index=Number(document.documentElement.getAttribute('data-sf-gemini-response-index'));
    const candidates=responses().filter(visible);
    // A replacement is safe only for the same dedicated turn; never pick a later unrelated reply.
    return candidates.length===index+1?candidates[index]:marked;
   };
  }else{
   if(request.operation!=='generate'||typeof request.prompt!=='string'||!request.prompt.trim())return {ok:false,accepted:false,code:'GEMINI_BROWSER_FAILED'};
   const previous=new Set(responses());const previousCount=responses().length,queryIndex=queries().length;const refs=request.references||[];
   if(refs.length){
    let fileInput=document.querySelector('input[type=file]');
    if(!fileInput){const upload=button(/upload|add files|attach|tải lên|thêm tệp|đính kèm/i);if(upload)upload.click();fileInput=await until(()=>document.querySelector('input[type=file]'),5000);}
    if(!fileInput)return {ok:false,accepted:false,code:'GEMINI_BROWSER_ATTACH_FAILED'};
    const dt=new DataTransfer();
    for(let i=0;i<refs.length;i++){
     const r=refs[i];if(!['image/png','image/jpeg','image/webp','video/mp4','video/webm','video/quicktime'].includes(r.mime_type))return {ok:false,accepted:false,code:'GEMINI_BROWSER_ATTACH_FAILED'};
     const bytes=Uint8Array.from(atob(r.data),c=>c.charCodeAt(0));
     dt.items.add(new File([bytes],'SceneForge-reference-'+(i+1)+'.'+({'image/png':'png','image/jpeg':'jpg','image/webp':'webp','video/mp4':'mp4','video/webm':'webm','video/quicktime':'mov'}[r.mime_type]),{type:r.mime_type}));
    }
    fileInput.files=dt.files;fileInput.dispatchEvent(new Event('change',{bubbles:true}));
    const attached=await until(()=>{
     const previews=[...document.querySelectorAll('file-preview,uploader-file-preview,[class*="file-preview"],[class*="attachment"],[data-test-id*="file-preview"],img[src^="blob:"]')].filter(visible);
     const named=refs.every((_,i)=>document.body.innerText.includes('SceneForge-reference-'+(i+1))||[...document.querySelectorAll('[title],[aria-label],img[alt]')].some(e=>[e.title,e.getAttribute('aria-label'),e.getAttribute('alt')].some(t=>t?.includes('SceneForge-reference-'+(i+1)))));
     return named||previews.length>=refs.length;
    },30000);
    if(!attached)return {ok:false,accepted:false,code:'GEMINI_BROWSER_ATTACH_FAILED'};
    await wait(1500);
   }
   input.focus();const range=document.createRange();range.selectNodeContents(input);const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);
   const text=request.kind==='image'?'Generate one image using the attached source and reference images and follow this prompt exactly. Return the generated image.\n\n'+request.prompt:request.prompt;
   if(!document.execCommand('insertText',false,text)){input.textContent=text;input.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:text}));}
   const send=await until(()=>{const explicit=[...document.querySelectorAll('button.send-button')].find(e=>visible(e)&&!e.disabled&&e.getAttribute('aria-disabled')!=='true');return explicit||button(/^(send( message| prompt)?|gửi( tin nhắn| lời nhắc)?)$/i);},15000);
   if(!send)return {ok:false,accepted:false,code:'GEMINI_BROWSER_SEND_CONTROL_MISSING'};
   sent=true;send.click();latest=()=>{
    // Gemini can replace its streaming placeholder. Never retain a detached DOM node.
    const marked=request.request_id&&document.querySelector('[data-sf-gemini-turn="'+CSS.escape(request.request_id)+'"]');
    let candidates=responses().filter(e=>!previous.has(e)&&visible(e));
    const turns=queries(),query=turns[queryIndex],next=turns[queryIndex+1];
    if(query)candidates=candidates.filter(e=>(query.compareDocumentPosition(e)&Node.DOCUMENT_POSITION_FOLLOWING)&&(!next||(e.compareDocumentPosition(next)&Node.DOCUMENT_POSITION_FOLLOWING)));
    const current=marked?.isConnected&&images(marked).length?marked:candidates.at(-1);
    if(current&&request.request_id){
     if(marked&&marked!==current)marked.removeAttribute('data-sf-gemini-turn');
     current.setAttribute('data-sf-gemini-turn',request.request_id);
     document.documentElement.setAttribute('data-sf-gemini-owner',request.request_id);
     document.documentElement.setAttribute('data-sf-gemini-response-index',String(previousCount));
    }
    return current;
   };
  }
  if(request.kind==='text'){
   let old='',changed=Date.now();const text=await until(()=>{const node=latest(),s=(node?.querySelector('message-content,.markdown')?.innerText||node?.innerText||'').trim();if(s!==old){old=s;changed=Date.now();}return s&&!button(/^(stop|dừng|ngừng)(\b|\s)/i)&&Date.now()-changed>2500?s:null;},180000);
   return text?{ok:true,text}:{ok:false,accepted:null,code:'GEMINI_BROWSER_TEXT_TIMEOUT'};
  }
  const output=await until(()=>images(latest()).at(-1),180000);
  if(!output)return {ok:false,accepted:null,code:'GEMINI_BROWSER_IMAGE_TIMEOUT'};
  try{
   let file;try{const r=await fetch(output.currentSrc,{credentials:'include',signal:AbortSignal.timeout(15000)});if(r.ok)file=await r.blob();}catch{}
   if(!file||!['image/png','image/jpeg','image/webp'].includes(file.type)){const c=document.createElement('canvas');c.width=output.naturalWidth;c.height=output.naturalHeight;c.getContext('2d').drawImage(output,0,0);file=await new Promise(r=>c.toBlob(r,'image/png'));}
   if(!file||file.size>24*1024*1024)throw Error();
   return await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve({ok:true,image:r.result.split(',')[1],mime:file.type});r.onerror=reject;r.readAsDataURL(file);});
  }catch{
   const u=new URL(output.currentSrc);if(u.protocol==='https:'&&u.hostname.endsWith('.googleusercontent.com'))return {ok:false,accepted:true,code:'GEMINI_BROWSER_TRANSFER_FAILED',imageUrl:u.href};
   return {ok:false,accepted:true,code:'GEMINI_BROWSER_TRANSFER_FAILED'};
  }
 }catch{return {ok:false,accepted:sent?null:false,code:'GEMINI_BROWSER_FAILED'};}
}
