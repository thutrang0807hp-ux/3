/* Frame Studio adapter. Sending, waiting and image conversion use the vendored repo implementation. */
window.SFStudioBridge={async run(request){
 const wait=ms=>new Promise(r=>setTimeout(r,ms)),visible=e=>e.getClientRects().length>0;
 const button=re=>[...document.querySelectorAll('button')].find(e=>visible(e)&&!e.disabled&&re.test(e.getAttribute('aria-label')||e.title||e.textContent||''));
 const until=async(fn,ms)=>{const end=Date.now()+ms;do{const r=fn();if(r)return r;await wait(250);}while(Date.now()<end);};
  async function readImage(image) {
    let file;
    try {
      const response = await fetch(image.currentSrc, {signal: AbortSignal.timeout(15000)});
      if (response.ok) file = await response.blob();
    } catch {
      // Some Gemini image hosts allow rendering but restrict direct fetches.
    }
    if (!file?.type.startsWith("image/")) {
      const canvas = document.createElement("canvas");
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      canvas.getContext("2d").drawImage(image, 0, 0);
      file = await new Promise(resolve => canvas.toBlob(resolve, "image/png"));
    }
    if (!file || !["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 8_000_000) {
      throw new Error("Không thể chuyển ảnh này về Studio.");
    }
    return await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve({image: reader.result.split(",")[1], mime: file.type});
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

 if(request.operation==='receive'){
  const saved=window.SFStudioTurn;if(!saved||saved.id!==request.target_job)return {ok:false,accepted:null,code:'GEMINI_BROWSER_FAILED'};
  if(saved.result?.image||saved.result?.imageUrl)return {ok:!!saved.result.image,...saved.result};
  const messages=[...document.querySelectorAll('model-response,.model-response-text')].filter(n=>!n.parentElement?.closest('model-response,.model-response-text'));
  if(messages.length!==1)return {ok:false,accepted:null,code:'GEMINI_BROWSER_FAILED'};
  const image=[...messages[0].querySelectorAll('img')].filter(i=>i.complete&&i.naturalWidth>=256&&i.naturalHeight>=256).at(-1);
  if(!image)return {ok:false,accepted:null,code:'GEMINI_BROWSER_IMAGE_TIMEOUT'};
  try{return {ok:true,...await readImage(image)};}catch{const u=new URL(image.currentSrc);if(u.protocol==='https:'&&u.hostname.endsWith('.googleusercontent.com'))return {ok:false,accepted:true,imageUrl:u.href,code:'GEMINI_BROWSER_TRANSFER_FAILED'};return {ok:false,accepted:true,code:'GEMINI_BROWSER_TRANSFER_FAILED'};}
 }
 if(request.operation!=='generate')return {ok:false,accepted:false,code:'GEMINI_BROWSER_FAILED'};
 if(window.SFStudioTurn?.id===request.request_id)return {ok:false,accepted:null,code:'GEMINI_BROWSER_FAILED'};
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
 window.SFStudioTurn={id:request.request_id};
 const result=await generateInGemini(request.prompt,request.ratio||'9:16',false);
 window.SFStudioTurn.result=result;
 if(result.image)return {ok:true,...result};
 if(result.imageUrl)return {ok:false,accepted:true,code:'GEMINI_BROWSER_TRANSFER_FAILED',...result};
 if(result.error?.startsWith('Không thấy ô chat Gemini.'))return {ok:false,accepted:false,code:'GEMINI_BROWSER_OFFLINE'};
 if(result.error==='Gemini đã đổi giao diện hoặc chưa cho phép gửi prompt.')return {ok:false,accepted:false,code:'GEMINI_BROWSER_SEND_CONTROL_MISSING'};
 if(result.error?.startsWith('Gemini chưa trả ảnh sau khoảng'))return {ok:false,accepted:null,code:'GEMINI_BROWSER_IMAGE_TIMEOUT'};
 return {ok:false,accepted:null,code:'GEMINI_BROWSER_FAILED'};
}};
