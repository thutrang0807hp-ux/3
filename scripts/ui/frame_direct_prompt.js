/* Local image-edit recipe: no text-generation request and no video-prompt changes. */
async function prepareFrameDirect(s){
 ensure(s);SFFrameRefs.validate(s);
 if(current(s,'image'))return;
 const slot=key(s,'image'),previous=record(s,'image'),input=snapshot(s,'image');
 const pending=(project.cloudJobs||[]).find(j=>j.sceneId===s.id&&j.kind==='image'&&!['imported','failed','not_submitted','abandoned','stale','invalid'].includes(j.state));
 if(pending)throw Error('Lượt ảnh cũ chưa rõ kết quả. Kiểm tra lượt hiện tại trước; chưa gửi ảnh mới.');
 if(owners(s,'image')&&previous?.manualInput&&previous.manualInput!==input){manualDecision(s,'image',null,input);throw Error('Giữ bản sửa tay; rà tham khảo mới trước khi tạo ảnh.');}
 const context=productFrameContext(s);
 if(context?.visible_in_scene&&!sceneReference(s,'product').images.length)throw Error('Thêm ảnh sản phẩm ở node Ảnh tham chiếu trước khi tạo khung.');
 const bindings=imageBindings(s);
 if(bindings.length>8)throw Error('Tối đa 8 ảnh nguồn / tham chiếu mỗi lượt.');
 const capture=project.source?.asset&&assets.has(project.source.asset)?await SFFrameCapture.source(s):null;
 ensure(s);if(input!==snapshot(s,'image'))throw Error('Tham khảo hoặc cảnh đã đổi; chưa gửi ảnh.');
 const roles=bindings.filter(b=>b.replace).map(b=>b.code+' = '+b.role+' ('+b.purpose+')').join('; ');
 const notes=refsFor(s).map(role=>role+': '+(sceneReference(s,role).description||'')).join('\n');
 const replaceProduct=refsFor(s).includes('product')&&sceneReference(s,'product').images.length>0;
 const label=replaceProduct?(s.expectedLabel||''):'';
 const en=[
  'IMAGE EDIT — one unified still frame, not a video, collage or storyboard.',
  'R1 is the original scene: preserve its camera angle, framing, pose, hand placement, perspective, scene layout and lighting. Replace only the roles identified below; preserve all other content.',
  roles?'REFERENCE ROLES: '+roles:'No replacement references supplied; preserve original identities and objects.',
  'For each replacement role use only its corresponding attached images. Never mix faces or transfer clothes/background from a product reference. Multiple images of the same item are views of that item, not extra objects to insert.',
  (replaceProduct?'PRODUCT LOCK: copy the referenced product shape, proportions, colors, material, cap, package layout, logo and visible lettering faithfully. Fit its real shape into the original scene with plausible scale, hand contact, occlusion, shadows and reflections. Do not keep the old source product brand or invent missing letters, features or a redesigned package.':'No product replacement is selected: retain the original product and its real branding.'),
  label?'User product/name to preserve when present on its reference: '+label+'. Do not add this as a caption or invent a label missing from the reference.':'',
  'PERSON / OUTFIT LOCK: use the attached face only for identity and attached outfit only for clothing. Preserve natural anatomy, texture and scene lighting. Leave unselected roles unchanged.',
  'Remove source subtitles and promotional overlays; preserve authentic lettering on the referenced item. No added captions, watermark, grid or split screen. Produce a clear, natural photographic still with real texture; do not hallucinate detail from a blurred reference.',
  notes?'REFERENCE NOTES:\n'+notes:'',
  s.extraRequest?'USER REQUEST: '+s.extraRequest:'',
  s.promptRevision?.image?'USER FRAME EDIT: '+s.promptRevision.image:''
 ].filter(Boolean).join('\n\n');
 const vi=['Chỉnh một ảnh khung duy nhất. Giữ góc máy, bố cục, tư thế, vị trí tay và ánh sáng của R1; chỉ thay các vai trò có ảnh tham khảo.',roles?'Vai trò ảnh: '+roles:'Giữ người và đồ gốc vì chưa chọn ảnh thay thế.',replaceProduct?'Sao chép đúng hình dáng, tỉ lệ, màu, chất liệu, bao bì, logo và chữ nhìn thấy của sản phẩm tham khảo. Giữ tiếp xúc tay, che khuất, bóng và phản chiếu tự nhiên. Không trộn mặt, không đổi thiết kế đồ, không bịa chữ.':'Không chọn thay sản phẩm: giữ nguyên đồ và nhãn thật của cảnh nguồn.',label?'Tên/nhãn cần giữ theo ảnh: '+label:'','Bỏ phụ đề và chữ quảng cáo đè trên video mẫu; giữ chữ thật trên sản phẩm. Một ảnh liền mạch, không chia ô, không thêm chữ hay watermark.',notes,s.extraRequest||'',s.promptRevision?.image||''].filter(Boolean).join('\n\n');
 const next={input,template:SFPromptContract.version,applied:true,localRecipe:true,namePolicy:'reference-only-v1',manual:owners(s,'image'),manualInput:owners(s,'image')?input:undefined,bindings,result:{promptFrame:{en,vi},used_refs:bindings.map(b=>b.code),warnings:[]},sourceCapture:capture?{asset:capture.asset,stamp:capture.captureStamp,sha256:capture.sha256}:null};
 if(previous){state().history??=[];state().history.push({...clone(previous),archivedAt:Date.now(),action:'direct-frame-without-writer'});}
 state().records[slot]=next;delete s.frameActionError;await storeProject();
}
