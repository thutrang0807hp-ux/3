/* Frame image flow: one create/receive owner; no writer is mandatory for creation. */
async function receiveFrameJob(s,job,{requestReceive=false,allowLegacyImage=false}={}){
 ensure(s);if(job.state==='imported')return {sceneId:s.id,requestId:job.id,received:true,skipped:true};currentActivity={sceneId:s.id,stage:'image',startedAt:Date.now()};
 const attempt=job.receiveAttempt={startedAt:Date.now(),state:'running'};await storeProject();
 try{
 if(requestReceive&&job.state!=='done'){
  const reply=await pipelineRequest('gemini-chat/jobs/'+job.id+'/receive',{conversation_scope:job.conversationScope||s.imageConversationScope});
  ensure(s);jobReadRecord(job,reply);await storeProject();
 }
 await poll(job,job.provider||'gemini-chat',!requestReceive);
 ensure(s);await directRecover({sceneId:s.id,silent:true,allowLegacyImage});
 if(job.state!=='imported')throw Error(job.error||'Kết quả chưa nhận được vào cảnh. Giữ lượt cũ, chưa tạo thêm.');
 attempt.state='done';attempt.finishedAt=Date.now();delete s.frameActionError;await storeProject();
 return {sceneId:s.id,requestId:job.id,received:true};
 }catch(error){attempt.state='failed';attempt.finishedAt=Date.now();attempt.error=error.message||String(error);await storeProject();throw error;}
}
async function processFrameImage(s,chat,{regenerate=false,receiveOnly=false,allowLegacyImage=false}={}){
 ensure(s);
 const old=(project.cloudJobs||[]).filter(j=>j.sceneId===s.id&&j.kind==='image'&&j.state!=='abandoned').at(-1);
 if(receiveOnly){if(!old)throw Error('Không có lượt ảnh cũ để nhận.');return receiveFrameJob(s,old,{requestReceive:true,allowLegacyImage});}
 if(old&&(old.canReceiveImage||old.errorCode==='GEMINI_IMAGE_DOWNLOAD_ERROR'||!['imported','failed','not_submitted'].includes(old.state)))return receiveFrameJob(s,old,{requestReceive:old.canReceiveImage||old.errorCode==='GEMINI_IMAGE_DOWNLOAD_ERROR',allowLegacyImage});
 await prepareFrameDirect(s);ensure(s);
 if(!regenerate&&latestVersion(s,'frame')?.generationSignature===await directSignature(s,'','image'))return {sceneId:s.id,skipped:true};
 await phase('Đang tạo / nhận ảnh · cảnh '+(s.index+1));
 const selected=chat||await statusFor('gemini-chat');
 await generate(s,null,'image',selected);ensure(s);
 return {sceneId:s.id,requestId:(project.cloudJobs||[]).filter(j=>j.sceneId===s.id&&j.kind==='image').at(-1)?.id,received:true};
}
