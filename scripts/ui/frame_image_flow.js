/* Frame Studio: one image owner. Prompt recipe/reference packing are deliberately unchanged. */
function studioJob(s){return (project.cloudJobs||[]).filter(j=>j.frameStudioVersion===164&&j.sceneId===s.id&&j.kind==='image'&&j.state!=='abandoned').at(-1);}
async function studioImport(s,job,record){
 ensure(s);if(s.frames.some(f=>f.requestId===job.id)){jobReadRecord(job,{state:'imported'});return;}
 if(record.state!=='done')return;
 if(record.result?.scene_id!==s.id||record.result?.room_id!==project.id)throw Error('Kết quả không thuộc cảnh này.');
 if(job.signature!==await directSignature(s,'','image')){job.state='stale';throw Error('Cảnh hoặc prompt đã đổi. Giữ ảnh trong lượt cũ để rà lại.');}
 const response=await fetch('/local-api/gemini-chat/files/'+encodeURIComponent(job.id));if(!response.ok)throw Error('Ảnh đã tạo nhưng chưa tải về máy. Bấm Nhận ảnh để đọc lại lượt này.');
 const file=new File([await response.blob()],job.id+'.png',{type:record.result.mime_type});ensure(s);const count=s.frames.length;
 await addFrame(file,s.id);ensure(s);if(s.frames.length===count)throw Error('Tệp trả về chưa nhập được vào cảnh.');
 Object.assign(s.frames.at(-1),{requestId:job.id,generationSignature:job.signature,prompt:job.prompt,origin:'gemini-chat',downloadVariant:record.result.download_variant,accountId:record.result.account_id});
 s.frameSelectionId=s.frames.at(-1).id;jobReadRecord(job,{state:'imported'});delete s.frameActionError;await storeProject();
}
async function receiveFrameJob(s,job,{requestReceive=false,readOnly=false}={}){
 ensure(s);if(job.state==='imported')return {sceneId:s.id,received:true,skipped:true};
 currentActivity={sceneId:s.id,stage:'image',startedAt:Date.now()};
 if(requestReceive&&job.state!=='done')await pipelineRequest('gemini-chat/jobs/'+job.id+'/receive',{});
 const started=Date.now();
 do{
  const record=await pipelineRequest('gemini-chat/jobs/'+job.id);ensure(s);jobReadRecord(job,record);await storeProject();
  if(record.state==='done'){await studioImport(s,job,record);return {sceneId:s.id,requestId:job.id,received:true};}
  if(readOnly)return {sceneId:s.id,pending:true};
  if(!['prepared','preparing','submitted','queued','running','downloading'].includes(record.state))throw Error(record.message||'Chưa nhận được ảnh. Giữ lượt hiện tại; có thể bấm Nhận ảnh, chưa tạo thêm.');
  if(Date.now()-started>300000)throw Error('Đã dừng chờ trong app. Lượt cũ được giữ để nhận ảnh, chưa gửi lại.');
  await wait(1000);
 }while(true);
}
async function processFrameImage(s,chat,{regenerate=false,receiveOnly=false,readOnly=false}={}){
 ensure(s);let job=studioJob(s);
 if(receiveOnly){if(!job)throw Error('Node mới chưa có lượt ảnh của cảnh này.');return receiveFrameJob(s,job,{requestReceive:!readOnly,readOnly});}
 if(job&&!['imported','failed','not_submitted','abandoned'].includes(job.state))return receiveFrameJob(s,job);
 // Old node receipts remain in history. Only an explicit new-node send moves them aside locally.
 const old=(project.cloudJobs||[]).filter(j=>j.sceneId===s.id&&j.kind==='image'&&!j.frameStudioVersion&&!['imported','failed','not_submitted','abandoned'].includes(j.state));
 if(old.length){if(!confirm('Tạo bằng node mới cho cảnh này? Lượt node cũ vẫn được giữ trong lịch sử và có thể đã dùng hạn mức.'))return {sceneId:s.id,cancelled:true};for(const j of old){j.previousState=j.state;j.state='abandoned';j.archivedBy='frame-studio-164';}}
 await prepareFrameDirect(s);ensure(s);
 const signature=await directSignature(s,'','image');if(!regenerate&&s.frames.some(f=>f.generationSignature===signature))return {sceneId:s.id,skipped:true};
 const prompt=imageFramePrompt(s),references=await generationRefs(s,null,true),status=chat||await statusFor('gemini-chat');ensure(s);
 if(signature!==await directSignature(s,'','image'))throw Error('Cảnh đã đổi trước khi gửi.');
 job={id:'gchat-'+uid(),provider:'gemini-chat',kind:'image',frameStudioVersion:164,sceneId:s.id,part:'',signature,prompt,state:'prepared',at:Date.now()};
 project.cloudJobs??=[];project.cloudJobs.push(job);await SFProviderReceipts.persistIntent(job,storeProject,parent.SceneForgeStorage);ensure(s);
 currentActivity={sceneId:s.id,stage:'image',startedAt:Date.now()};state().run.phase='Đang tạo ảnh · cảnh '+(s.index+1);render();
 try{const record=await pipelineRequest('gemini-chat/jobs',{request_id:job.id,kind:'image',role:'image',image_engine:'studio-v1',prompt,references,room_id:project.id,scene_id:s.id,confirm_send:true,selection_token:status.selection.token});jobReadRecord(job,record);await storeProject();}
 catch(error){jobPostFailure(job,error);await storeProject();throw error;}
 return receiveFrameJob(s,job);
}
