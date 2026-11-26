async function sendSceneForgeFrame(request){
 const wait=ms=>new Promise(r=>setTimeout(r,ms)),visible=e=>e.getClientRects().length>0;
 const button=re=>[...document.querySelectorAll('button')].find(e=>visible(e)&&!e.disabled&&re.test(e.getAttribute('aria-label')||e.title||e.textContent||''));
 const until=async(fn,ms)=>{const end=Date.now()+ms;do{const r=fn();if(r)return r;await wait(250);}while(Date.now()<end);};
  const editor = () => Array.from(document.querySelectorAll(
    'rich-textarea [contenteditable="true"], .ql-editor[contenteditable="true"], [contenteditable="true"][role="textbox"]'
  )).find(visible);
  const findButton = (selector, label) => Array.from(document.querySelectorAll(selector))
    .find(button => visible(button) && !button.disabled && button.getAttribute("aria-disabled") !== "true" &&
      ((selector.includes("button.send-button") && button.classList.contains("send-button")) ||
       label.test(button.getAttribute("aria-label") || button.title || "")));
  const responseSelector = "model-response, .model-response-text";
  const assistantMessages = () => Array.from(document.querySelectorAll(responseSelector))
    .filter(node => !node.parentElement?.closest(responseSelector));
 const refs=request.references||[];
 try{
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

 }catch{return {ok:false,accepted:false,code:'GEMINI_BROWSER_ATTACH_FAILED'};}
 const prior=request.request_id;
 for(const node of assistantMessages())node.setAttribute('data-sceneforge-prior',prior);
 const selector=':is(model-response,.model-response-text):not(:is(model-response,.model-response-text) :is(model-response,.model-response-text)):not([data-sceneforge-prior="'+prior+'"] )';
 return {selector,userQueries:document.querySelectorAll('user-query,.user-query,[data-message-role="user"]').length};
}
