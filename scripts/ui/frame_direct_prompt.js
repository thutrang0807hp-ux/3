/* Local image-edit recipe: no text-generation request and no video-prompt changes. */
async function prepareFrameDirect(s){
 ensure(s);currentActivity={sceneId:s.id,stage:'frame-preparing',startedAt:Date.now()};SFFrameRefs.validate(s);
 const prior=record(s,'image'),inFlight=(project.cloudJobs||[]).some(j=>j.frameStudioVersion===164&&j.sceneId===s.id&&j.kind==='image'&&!['imported','failed','not_submitted','abandoned','stale','invalid'].includes(j.state));
 if(inFlight&&current(s,'image'))return;
 if(!inFlight&&s.framePromptVersion!==174){if(SFUniversalFrame.isLegacyManaged(s.framePromptOverride)){s.framePromptBackups??=[];s.framePromptBackups.push({text:s.framePromptOverride,at:Date.now()});s.framePromptBackups=s.framePromptBackups.slice(-5);state().history??=[];state().history.push({...clone(prior||{}),manualPrompt:s.framePromptOverride,archivedAt:Date.now(),action:'replace-managed-template-v60'});delete s.framePromptOverride;delete s.frameManualInput;if(s.promptOwners)delete s.promptOwners.image;if(prior)delete prior.manualInput;}const originalInput=snapshot(s,'image'),manualInput=prior?.manualInput||s.frameManualInput;if(owners(s,'image')&&manualInput&&manualInput!==originalInput){manualDecision(s,'image',null,originalInput);throw Error('Rà prompt đã sửa tay trước khi cập nhật.');}s.framePromptVersion=174;if(owners(s,'image')){const updated=snapshot(s,'image');s.frameManualInput=updated;if(prior){prior.manualInput=updated;prior.input=updated;}}}
 if(!inFlight&&s.frameProductFactsVersion!==168){const oldInput=snapshot(s,'image'),manualInput=prior?.manualInput||s.frameManualInput;if(owners(s,'image')&&manualInput&&manualInput!==oldInput){manualDecision(s,'image',null,oldInput);throw Error('Rà prompt sửa tay trước khi cập nhật thông số sản phẩm.');}s.frameProductFactsVersion=168;if(owners(s,'image')){const updated=snapshot(s,'image');s.frameManualInput=updated;if(prior){prior.manualInput=updated;prior.input=updated;}}}
 if(!inFlight&&!s.frameEditPolicy){const oldManual=prior?.manualInput||s.frameManualInput;if(owners(s,'image')&&oldManual&&oldManual!==snapshot(s,'image')){manualDecision(s,'image',null,snapshot(s,'image'));throw Error('Rà prompt sửa tay trước khi cập nhật yêu cầu ảnh.');}s.frameEditPolicy=166;if(owners(s,'image')){const updated=snapshot(s,'image');s.frameManualInput=updated;if(prior){prior.manualInput=updated;prior.input=updated;}}}
 if(current(s,'image')&&(prior?.framePromptVersion===174||(!prior?.localRecipe&&prior?.job?.state==='applied')))return;
 const slot=key(s,'image'),previous=record(s,'image'),input=snapshot(s,'image');
 const pending=(project.cloudJobs||[]).find(j=>j.frameStudioVersion===164&&j.sceneId===s.id&&j.kind==='image'&&!['imported','failed','not_submitted','abandoned','stale','invalid'].includes(j.state));
 if(pending)throw Error('Lượt ảnh cũ chưa rõ kết quả. Kiểm tra lượt hiện tại trước; chưa gửi ảnh mới.');
 if(owners(s,'image')&&previous?.manualInput&&previous.manualInput!==input){manualDecision(s,'image',null,input);throw Error('Giữ bản sửa tay; rà tham khảo mới trước khi tạo ảnh.');}
 const context=productFrameContext(s);
 if(context?.visible_in_scene&&!sceneReference(s,'product').images.length)throw Error('Thêm ảnh sản phẩm ở node Ảnh tham chiếu trước khi tạo khung.');
 const bindings=imageBindings(s);
 if(bindings.length>8)throw Error('Tối đa 8 ảnh nguồn / tham chiếu mỗi lượt.');
 const capture=project.source?.asset&&assets.has(project.source.asset)?await SFFrameCapture.source(s):null;
 ensure(s);if(input!==snapshot(s,'image'))throw Error('Tham khảo hoặc cảnh đã đổi; chưa gửi ảnh.');
 const en=SFUniversalFrame.render(s),vi=SFFrameSettings.compact(s,'vi');
 const next={framePromptVersion:174,frameProductFactsVersion:168,frameEditPolicy:166,input,template:SFPromptContract.version,applied:true,localRecipe:true,namePolicy:'reference-only-v1',manual:owners(s,'image'),manualInput:owners(s,'image')?input:undefined,bindings,result:{promptFrame:{en,vi},used_refs:bindings.map(b=>b.code),warnings:[]},sourceCapture:capture?{asset:capture.asset,stamp:capture.captureStamp,sha256:capture.sha256}:null};
 if(previous){state().history??=[];state().history.push({...clone(previous),archivedAt:Date.now(),action:'direct-frame-without-writer'});}
 state().records[slot]=next;delete s.frameActionError;await storeProject();
}
