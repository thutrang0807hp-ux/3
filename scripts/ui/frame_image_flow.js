/* Frame Studio: one image owner. Prompt recipe/reference packing are deliberately unchanged. */
function studioJob(s){return (project.cloudJobs||[]).filter(j=>j.frameStudioVersion===164&&j.sceneId===s.id&&j.kind==='image'&&j.state!=='abandoned').at(-1);}
function detachStudioJobForEdit(s){
 if(!project.scenes.includes(s))throw Error('Cảnh đã đổi.');
 for(const job of project.cloudJobs||[]){
  if(job.frameStudioVersion!==164||job.sceneId!==s.id||job.kind!=='image'||['imported','failed','not_submitted','abandoned','stale'].includes(job.state))continue;
  job.previousState=job.state;job.state='abandoned';job.archivedBy='reference-change';job.archivedAt=Date.now();
 }
}
async function studioImport(s,job,record){
 if(job.archivedBy==='reference-change')return;
 ensure(s);if(s.frames.some(f=>f.requestId===job.id)){jobReadRecord(job,{state:'imported'});return;}
 if(record.state!=='done')return;
 if(record.result?.scene_id!==s.id||record.result?.room_id!==project.id)throw Error('Kết quả không thuộc cảnh này.');
 if(job.signature!==await directSignature(s,'','image')){job.state='stale';throw Error('Cảnh hoặc prompt đã đổi. Giữ ảnh trong lượt cũ để rà lại.');}
 const response=await fetch('/local-api/gemini-chat/files/'+encodeURIComponent(job.id));if(!response.ok)throw Error('Ảnh đã tạo nhưng chưa tải về máy. Bấm Nhận ảnh để đọc lại lượt này.');
 const file=new File([await response.blob()],job.id+'.png',{type:record.result.mime_type});ensure(s);const count=s.frames.length;
 await addFrame(file,s.id);ensure(s);if(s.frames.length===count)throw Error('Tệp trả về chưa nhập được vào cảnh.');
 Object.assign(s.frames.at(-1),{requestId:job.id,generationSignature:job.signature,prompt:job.prompt,origin:'gemini-chat',downloadVariant:record.result.download_variant,accountId:record.result.account_id,requestedOutput:job.requestedOutput,referenceManifest:job.referenceManifest});
 s.frameSelectionId=s.frames.at(-1).id;jobReadRecord(job,{state:'imported'});delete s.frameActionError;await storeProject();
}
async function receiveFrameJob(s,job,{requestReceive=false,readOnly=false}={}){
 ensure(s);if(job.archivedBy==='reference-change')return {sceneId:s.id,archived:true};if(job.state==='imported')return {sceneId:s.id,received:true,skipped:true};
 currentActivity={sceneId:s.id,stage:'image',startedAt:Date.now()};
 if(requestReceive&&job.state!=='done')await pipelineRequest('gemini-chat/jobs/'+job.id+'/receive',{});
 const started=Date.now();
 do{
  const record=await pipelineRequest('gemini-chat/jobs/'+job.id);ensure(s);if(job.archivedBy==='reference-change')return {sceneId:s.id,archived:true};jobReadRecord(job,record);if(state().run?.state==='running')state().run.phase=(record.state==='downloading'?'Đang nhận ảnh':record.state==='done'?'Đang nhập ảnh':record.state==='queued'?'Đang chờ Gemini':'Đang tạo / chờ Gemini')+' · cảnh '+(s.index+1);await storeProject();
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
 if([170,174].includes(s.framePromptVersion))SFUniversalFrame.validateForSend(s,imageFramePrompt(s));
 const signature=await directSignature(s,'','image');if(!regenerate&&s.frames.some(f=>f.generationSignature===signature))return {sceneId:s.id,skipped:true};
 const output=SFFrameSettings.output(s),prompt=imageFramePrompt(s),references=await generationRefs(s,null,true),status=chat||await statusFor('gemini-chat');ensure(s);
 if(signature!==await directSignature(s,'','image'))throw Error('Cảnh đã đổi trước khi gửi.');
 const referenceManifest=SFUniversalFrame.assigned(s);
 if(referenceManifest.length!==references.length)throw Error('Số ảnh gửi không khớp REFERENCE_BINDINGS; chưa gửi Gemini.');
 if([170,174].includes(s.framePromptVersion))SFUniversalFrame.validateForSend(s,prompt);
 job={id:'gchat-'+uid(),provider:'gemini-chat',kind:'image',frameStudioVersion:164,sceneId:s.id,part:'',signature,prompt,referenceManifest,requestedOutput:output,state:'prepared',at:Date.now()};
 project.cloudJobs??=[];project.cloudJobs.push(job);await SFProviderReceipts.persistIntent(job,storeProject,parent.SceneForgeStorage);ensure(s);
 currentActivity={sceneId:s.id,stage:'image',startedAt:Date.now()};state().run.phase='Đang tạo ảnh · cảnh '+(s.index+1);render();
 try{const record=await pipelineRequest('gemini-chat/jobs',{request_id:job.id,kind:'image',role:'image',image_engine:'studio-v1',ratio:output.ratio,prompt,references,room_id:project.id,scene_id:s.id,confirm_send:true,selection_token:status.selection.token});jobReadRecord(job,record);await storeProject();}
 catch(error){jobPostFailure(job,error);await storeProject();throw error;}
 return receiveFrameJob(s,job);
}

async function approveStudioImage(s){
 if(running||preparing||approvalBusy)throw Error('Đợi thao tác hiện tại trước khi duyệt ảnh.');
 const owner=project,f=s.frames.find(frame=>frame.id===s.frameSelectionId)||s.frames.at(-1),file=f?.asset&&assets.get(f.asset);
 if(!f||!file)throw Error('Thiếu file ảnh kết quả gốc. Nhập lại ảnh trước khi duyệt để tạo video; không dùng ảnh xem trước.');
 if(!['image/png','image/jpeg','image/webp'].includes(file.type||f.mime))throw Error('Ảnh đầu video cần PNG, JPEG hoặc WebP.');
 preparing=true;
 try{
  const bitmap=await createImageBitmap(file);const width=bitmap.width,height=bitmap.height;bitmap.close();
  if(!width||!height)throw Error('Không đọc được ảnh đầu video.');
  const sha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',await file.arrayBuffer()))].map(value=>value.toString(16).padStart(2,'0')).join('');
  if(project!==owner||!project.scenes.includes(s)||!s.frames.includes(f)||assets.get(f.asset)!==file||(s.frameSelectionId&&s.frameSelectionId!==f.id))throw Error('Ảnh hoặc cảnh đã đổi; chưa duyệt lựa chọn cũ.');
  if(f.sha256&&f.sha256!==sha256)throw Error('File ảnh đã đổi; nhập lại ảnh gốc trước khi duyệt.');
  if(s.approvedFrame&&s.approvedFrame!==f.id)s.chosen={};
  project.approvalCleanupPending=(project.approvalCleanupPending||[]).filter(item=>item.sceneId!==s.id||item.kind!=='frame');
  Object.assign(f,{width,height,sha256,status:'approved'});s.frameSelectionId=f.id;
  s.manualFrameApproval={frameId:f.id,asset:f.asset,sha256,at:Date.now()};
  s.manualFrameApproval.stamp=SFMediaNodes.frameStamp(s);
  s.localReviewedKey=s.localReviewKey;delete s.framePromptChanged;delete s.frameInputsChanged;delete s.frameCheckIssue;delete s.frameActionError;
  s.approvedFrame=f.id;
  if(!frameApproved(s))throw Error('Chưa ghi nhận được ảnh đã duyệt; lựa chọn được giữ để rà lại.');
  await storeProject();return {sceneId:s.id,frameId:f.id,approved:true};
 }finally{preparing=false;render();}
}
