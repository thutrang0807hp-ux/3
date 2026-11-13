/* Shared rules used by both Veo nodes. Backend remains the single Flow dispatcher. */
(()=>{
 const pending=['prepared','preparing','submitted','queued','running','downloading'];
 function valid(c){return !!c&&c.kind==='video'&&['ingredients','frames'].includes(c.mode)&&['9:16','16:9'].includes(c.ratio)&&['lite','fast','quality','omni-1.2-flash'].includes(c.model)&&c.outputs===1&&!(c.mode==='ingredients'&&c.model==='quality');}
 function model(c){if(!valid(c))throw Error('Cấu hình video chưa hợp lệ. Quality cần chế độ Khung hình; mỗi lượt nhận một video.');return (c.model==='omni-1.2-flash'?c.model:'veo-3.1-'+c.model)+'-i2v-8s-'+(c.ratio==='9:16'?'portrait':'landscape');}
 function ownership(job,record,room,scene,part){if(record.request_id!==job.id||record.result?.room_id!==room||record.result?.scene_id!==scene||record.result?.part!==part)throw Error('Kết quả không khớp phòng, cảnh hoặc phần clip; chưa nhập.');if(job.store_id&&record.store_id!==job.store_id)throw Error('Kết quả thuộc kho dữ liệu khác; chưa nhập.');}
 function unresolved(j){return !!j&&(pending.includes(j.state)||['unknown','missing','invalid','done'].includes(j.state));}
 const yieldUI=()=>new Promise(resolve=>{let done=false;const finish=()=>{if(done)return;done=true;clearTimeout(timer);resolve();},timer=setTimeout(finish,100);requestAnimationFrame(()=>setTimeout(finish,0));});
 async function readVideo(file,c,stopTime=null){
  const video=document.createElement('video'),url=URL.createObjectURL(file);video.muted=true;video.preload='auto';
  try{await new Promise((ok,no)=>{const timer=setTimeout(()=>no(Error('Không đọc được video.')),15000);video.onloadeddata=()=>{clearTimeout(timer);ok();};video.onerror=()=>{clearTimeout(timer);no(Error('Không giải mã được video.'));};video.src=url;});
   const ratio=c.ratio==='9:16'?9/16:16/9;if(!Number.isFinite(video.duration)||video.duration<7.5||video.duration>8.5||Math.abs(video.videoWidth/video.videoHeight-ratio)>.03)throw Error('Video chưa khớp thời lượng hoặc tỉ lệ đã chọn.');
   const canvas=document.createElement('canvas'),scale=Math.min(1,768/video.videoWidth);canvas.width=Math.round(video.videoWidth*scale);canvas.height=Math.round(video.videoHeight*scale);const draw=()=>{canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);return canvas.toDataURL('image/jpeg',.9);};const poster=draw(),time=Math.max(0,Math.min(video.duration,stopTime||video.duration)-.06);
   if(Math.abs(video.currentTime-time)>.001)await new Promise((ok,no)=>{const timer=setTimeout(()=>no(Error('Không đọc được khung cuối.')),10000);video.onseeked=()=>{clearTimeout(timer);ok();};video.onerror=()=>{clearTimeout(timer);no(Error('Không giải mã được khung cuối.'));};video.currentTime=time;});
   return {duration:video.duration,width:video.videoWidth,height:video.videoHeight,poster,tail:draw()};
  }finally{video.removeAttribute('src');video.load();URL.revokeObjectURL(url);}
 }
 window.SFVeoLifecycle={pending,valid,model,ownership,unresolved,yieldUI,readVideo};
})();
