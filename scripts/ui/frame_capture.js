/* Validate actual frame bytes; use local FFmpeg only if browser capture fails. */
(()=>{
 const pending=new Map(),active=new Set();
 async function source(s){
  const room=project.id,asset=project.source?.asset,file=asset&&assets.get(asset),at=(s.start+s.end)/2;
  if(!(file instanceof Blob)||!file.size)throw Error('Thiếu video gốc của dự án; cần nhập lại video nguồn. Chưa gửi AI.');
  const stamp=JSON.stringify([asset,s.start,s.end,file.size]);
  if(s.sourceFrame?.captureStamp===stamp&&assets.has(s.sourceFrame.asset))return s.sourceFrame;
  const key=room+':'+s.id+':'+stamp;if(pending.has(key))return pending.get(key);
  let stopped=false,nativeController=null,rejectStop;const stopWait=new Promise((_,reject)=>{rejectStop=reject;});const cancel=()=>{stopped=true;nativeController?.abort();rejectStop(Error('Đã dừng trích khung; chưa gửi thêm AI.'));};active.add(cancel);
  const task=Promise.race([(async()=>{
   let blob,engine='browser';const url=URL.createObjectURL(file);
   try{blob=await useVideo(url,async v=>{await seekFrame(v,at);if(!v.videoWidth||!v.videoHeight)throw Error('Video chưa có kích thước khung.');const c=document.createElement('canvas'),scale=Math.min(1,1920/Math.max(v.videoWidth,v.videoHeight));c.width=Math.max(1,Math.round(v.videoWidth*scale));c.height=Math.max(1,Math.round(v.videoHeight*scale));try{c.getContext('2d').drawImage(v,0,0,c.width,c.height);let b=await new Promise(r=>c.toBlob(r,'image/png'));if(!b||b.size>5*1024**2)b=await new Promise(r=>c.toBlob(r,'image/jpeg',.95));if(!b?.size)throw Error('Trình duyệt trả khung rỗng.');return b;}finally{c.width=c.height=0;}});}catch(error){
    if(stopped)throw Error('Đã dừng trích khung.');
    if(!['localhost','127.0.0.1'].includes(location.hostname))throw Error('Không trích được khung bằng trình duyệt: '+error.message+'. Bản cục bộ có thể dùng FFmpeg dự phòng.');
    if(project.id!==room||project.source?.asset!==asset)throw Error('Nguồn đã đổi; chưa gửi thêm.');
    const controller=nativeController=new AbortController(),timer=setTimeout(()=>controller.abort(),90000);
    try{const response=await fetch('/local-api/analysis/frame-capture',{method:'POST',headers:{'X-SceneForge-Local':'1','X-Frame-Time':String(at),'Content-Type':file.type||'application/octet-stream'},body:file,signal:controller.signal});if(!response.ok){const data=await response.json().catch(()=>({}));throw Error(data.detail||'Không trích được khung trên máy.');}blob=await response.blob();engine='ffmpeg';}finally{clearTimeout(timer);}
   }finally{URL.revokeObjectURL(url);}
   if(stopped)throw Error('Đã dừng trích khung.');
   const bitmap=await createImageBitmap(blob);const width=bitmap.width,height=bitmap.height;bitmap.close();if(!width||!height)throw Error('Khung rỗng; chưa gửi AI.');
   if(stopped||project.id!==room||project.source?.asset!==asset||assets.get(asset)!==file||!project.scenes.includes(s))throw Error('Nguồn đã đổi; bỏ khung của lượt cũ.');
   const sha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',await blob.arrayBuffer()))].map(x=>x.toString(16).padStart(2,'0')).join('');
   s.sourceFrame={id:'source',asset:putAsset(blob),mime:blob.type,name:blob.type==='image/png'?'khung-goc.png':'khung-goc.jpg',sha256,width,height,captureStamp:stamp,captureEngine:engine};save();return s.sourceFrame;
  })(),stopWait]);pending.set(key,task);try{return await task;}finally{pending.delete(key);active.delete(cancel);}
 }
 frameV3Source=async function(s){if(s.frames.length&&s.frameSelectionId!=='source')return frameV3(s);return source(s);};
 const cancelAll=()=>{for(const cancel of active)cancel();};const pause=SFPromptPipeline.pause;SFPromptPipeline.pause=(...a)=>{cancelAll();return pause(...a);};const restart=SFPromptPipeline.restartImagesAll;if(restart)SFPromptPipeline.restartImagesAll=(...a)=>{cancelAll();return restart(...a);};
 window.SFFrameCapture={source,cancel:cancelAll,stamp:s=>{const file=assets.get(project.source?.asset);return JSON.stringify([project.source?.asset,s.start,s.end,file?.size]);}};
})();
