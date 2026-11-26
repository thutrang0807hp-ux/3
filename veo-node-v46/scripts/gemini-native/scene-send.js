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
    async function sendMessage(message) {
      const input = await until(editor, 20000);
      if (!input) throw new Error("Không thấy ô chat Gemini. Hãy kiểm tra bạn đã đăng nhập Gemini Chat trên Chrome.");
      const previousMessages = new Set(assistantMessages());
      input.focus();
      if (!document.execCommand("insertText", false, message)) {
        input.textContent = message;
        input.dispatchEvent(new InputEvent("input", {bubbles: true, inputType: "insertText", data: message}));
      }
      const send = await until(() => findButton(
        "button.send-button, button[aria-label], button[title]", /^(send( message| prompt)?|gửi( tin nhắn| lời nhắc)?)$/i
      ), 8000);
      if (!send) throw new Error("Gemini đã đổi giao diện hoặc chưa cho phép gửi prompt.");
      send.click();
      return () => assistantMessages().filter(node => !previousMessages.has(node)).at(-1);
    }

 const message=request.kind==='image'?'Hãy tạo một ảnh theo đúng prompt này. Tỷ lệ ảnh: '+(request.ratio||'9:16')+'\n\n'+request.prompt:request.prompt;
 const prior=request.request_id;
 for(const node of assistantMessages())node.setAttribute('data-sceneforge-prior',prior);
 const latest=await sendMessage(message);
 const answer=await until(latest,90000);
 if(!answer)throw new Error('Đã gửi nhưng chưa thấy phản hồi mới của lượt này.');
 const selector=':is(model-response,.model-response-text):not(:is(model-response,.model-response-text) :is(model-response,.model-response-text)):not([data-sceneforge-prior="'+prior+'"] )';
 return {selector};
}
