/* .125: product facts plus reference-video structure; originals remain immutable. */
(()=>{
 let running=false,statusTimer=null;
 const labels={name:'Tên sản phẩm',facts:'Thông tin có căn cứ',audience:'Khách hàng',offer:'Giá / ưu đãi',avoid:'Điều không được nói',url:'Link sản phẩm'};
 function state(){return project.productScript??={brief:null,currentProduct:null,request:null,history:[]};}
 function defaults(p={}){return {name:p.name||'',facts:p.refs?.product?.description||'',audience:'',offer:'',avoid:'',url:'',originProductId:p.id||null,edited:false};}
 function brief(){const s=state();return s.brief??=defaults(s.currentProduct||{name:'',refs:project.refs});}
 function setProduct(p){if(!p||project.mode==='photos')return;const s=state();s.currentProduct={id:p.id||null,name:p.name||'',refs:{product:{description:p.refs?.product?.description||''}}};if(!s.brief||!s.brief.edited)s.brief=defaults(s.currentProduct);}
 function mismatch(){const s=state();return s.currentProduct?.id&&brief().originProductId!==s.currentProduct.id;}
 function input(){return {adaptation_version:2,action:'adapt_product',room_id:project.id,product:Object.fromEntries(Object.keys(labels).map(k=>[k,String(brief()[k]||'')])),reference_lines:project.script.filter(l=>l.original?.trim()||l.translation?.trim()).map(l=>({id:l.id,start:l.start,end:l.end,original:l.original||'',translation:l.translation||'',current_text:l.newText||''})),reference_scenes:project.scenes.slice(0,100).map(s=>({start:s.start,end:s.end,description:String(s.description||'').slice(0,500)}))};}
 const signature=()=>{const value=input();delete value.adaptation_version;return JSON.stringify({input:value,source:project.source?.asset||null,productId:state().currentProduct?.id||null});};
 function panel(){if(project.mode==='photos')return '';const b=brief();return '<section class="productScriptBrief" style="border:1px solid #465044;border-radius:8px;padding:10px;margin-bottom:12px"><b>Thông tin sản phẩm của tôi</b><p>'+esc(b.name||'Chưa có tên sản phẩm')+'</p><small>'+esc((b.facts||b.offer||'Thêm dữ kiện để không dùng nhầm thông tin sản phẩm mẫu.').slice(0,140))+'</small>'+(mismatch()?'<p class="warning">Sản phẩm đang chọn đã đổi. Nạp lại thông tin trước khi viết.</p>':'')+'<div class="scriptToolbar"><button data-product-script="brief">Nhập / sửa thông tin</button><button class="primary" data-product-script="write">AI viết lời theo sản phẩm</button>'+(state().request?'<button data-product-script="review">Xem lượt viết</button>':'')+'</div></section>';}
 function form(){const b=brief(),s=state();modal('Sản phẩm dùng cho kịch bản','<p>Video mẫu chỉ cung cấp nhịp và cách kể. Lời mới lấy dữ kiện từ sản phẩm của bạn.</p>'+(s.currentProduct?'<p>Sản phẩm đang chọn: <b>'+esc(s.currentProduct.name)+'</b></p><button id="productScriptLoad">Nạp tên và mô tả đã lưu của sản phẩm này</button>':'')+(mismatch()?'<p class="warning">Thông tin nhập trước thuộc sản phẩm khác. Nạp lại để tránh dùng nhầm.</p>':'')+Object.entries(labels).map(([k,label])=>'<label class="promptField" style="display:block;margin-top:12px">'+label+(k==='url'?' · chỉ lưu để tham khảo, chưa tự đọc trang':'')+(k==='name'||k==='url'?'<input style="width:100%;box-sizing:border-box" data-product-script-field="'+k+'" maxlength="'+(k==='name'?300:2000)+'" value="'+esc(b[k]||'')+'">':'<textarea style="width:100%;box-sizing:border-box;min-height:75px" data-product-script-field="'+k+'" maxlength="'+({facts:6000,audience:1000,offer:2000,avoid:2000}[k])+'" placeholder="'+(k==='facts'?'Dán mô tả, thông số, chất liệu hoặc công dụng đã được xác nhận.':'Không có thì để trống.')+'">'+esc(b[k]||'')+'</textarea>')+'</label>').join('')+'<p>Thông tin tự lưu theo phòng. Ảnh sản phẩm tiếp tục dùng ở bộ tham chiếu; không tự suy ra công dụng từ ảnh. Chỉ gửi chữ tới nguồn AI đang chọn khi bấm viết.</p>','<button data-action="close-modal">Đóng</button><button class="primary" data-product-script="write">AI viết lời theo sản phẩm</button>');
  $('#productScriptLoad')?.addEventListener('click',async()=>{if(running)return toast('Đợi lượt viết đang chạy.');s.history.push({brief:structuredClone(b),at:Date.now()});s.history=s.history.slice(-10);s.brief=defaults(s.currentProduct);await storeProject();render();form();});
 }
 async function request(recovery=false){
  if(running)return;
  const s=state(),b=brief();
  if(mismatch())return form();
  if(!recovery&&(!b.name.trim()||!(b.facts.trim()||b.offer.trim()))){form();return toast('Cần tên sản phẩm và dữ kiện thật hoặc giá/ưu đãi.');}
  if(!recovery&&!input().reference_lines.length)return toast('Cần lời mẫu: chép lời CPU hoặc nhập SRT trước. Không tự đoán lời từ ảnh.');
  if(!recovery&&['submitted','unknown'].includes(s.request?.state)){await inspect();return review();}
  const room=project.id;running=true;toast(recovery?'Đang đọc lại kết quả đã gửi…':'Đang viết lời theo thông tin sản phẩm…');
  try{
   if(!recovery){const status=await workflowLocalRequest('ai/script-library/status');if(project.id!==room)throw Error('Phòng đã đổi.');if(s.request)s.history.push(structuredClone(s.request));s.history=s.history.slice(-10);s.request={body:{...input(),request_id:crypto.randomUUID(),ai_source:status.ai_source},storeId:status.store_id,signature:signature(),state:'submitted',at:Date.now()};await storeProject();review();}
   const req=s.request;if(!req)throw Error('Chưa có lượt để nhận lại.');
   const result=await workflowLocalRequest('ai/script-library',{...structuredClone(req.body),expected_store_id:req.storeId,recovery});
   if(project.id!==room)throw Error('Phòng đã đổi; kết quả không áp sang phòng khác.');
   req.result=result;req.state='received';await storeProject();review();
  }catch(error){if(project.id===room&&['submitted','unknown'].includes(s.request?.state)){const receipt=error.detail,request=s.request;const notSent=receipt?.submitted===false&&receipt.store_id===request.storeId&&[request.body.request_id,'gchat-'+request.body.request_id].includes(receipt.request_id);request.state=!recovery&&(notSent||[400,413,422].includes(error.status))?'rejected':'unknown';request.error=error.message;if(notSent)request.negativeReceipt=structuredClone(receipt);await storeProject();}toast(error.message);if(project.id===room)review();}
  finally{running=false;}
 }
 async function inspect(){
  const req=state().request,room=project.id;if(!req)return;
  req.checking=true;review();
  try{const status=await workflowLocalRequest('ai/script-library/request-status',{...structuredClone(req.body),expected_store_id:req.storeId});if(project.id!==room||state().request!==req)return;req.remote=status;req.checkedAt=Date.now();}
  catch(e){req.remote={state:'unavailable',message:e.message};}
  finally{req.checking=false;if(project.id===room&&state().request===req){await storeProject();review();}}
 }
 async function restart(){
  if(running)return toast('Lượt đang gửi; chưa gửi thêm.');
  const req=state().request;if(!req)return request();await inspect();
  if(['queued','running','submitted','downloading'].includes(req.remote?.state))return toast('Động cơ vẫn đang xử lý lượt cũ; chưa gửi thêm.');
  if(req.remote?.state==='done')return request(true);
  if(!confirm('Bỏ chờ lượt cũ và viết lượt mới bằng thông tin hiện tại? Lượt chưa rõ có thể đã dùng hạn mức. Bản ghi cũ sẽ được giữ trong lịch sử.'))return;
  req.state='abandoned';await storeProject();return request();
 }
 function review(){const req=state().request;if(!req)return form();const result=req.result,stale=req.signature!==signature();let html='<p>Giữ nguyên lời gốc, bản dịch và mốc giây. Lời mới chỉ được áp dụng sau khi bạn rà.</p>'+(stale?'<p class="warning">Thông tin sản phẩm, lời hoặc cấu trúc mẫu đã thay đổi. Chưa được áp dụng bản này.</p>':'');
  html+='<details><summary>Thông tin đã dùng · '+esc(req.body.product.name)+'</summary>'+Object.entries(labels).filter(([k])=>req.body.product[k]).map(([k,label])=>'<p style="white-space:pre-wrap;overflow-wrap:anywhere"><b>'+label+':</b> '+esc(req.body.product[k])+'</p>').join('')+'</details>';
  if(!result)html+='<p><b>'+esc(req.state==='rejected'?'Chưa gửi AI · chưa viết lại':req.state==='submitted'?'Đang chờ kết quả AI':'Chưa xác định được kết quả lượt trước')+'</b></p><p>'+esc(req.error||'Lượt đã gửi, chưa có kết quả. Nhận lại không tự gửi lượt mới.')+'</p>';
  else if(result.needs_info)html+='<b>Cần bổ sung trước khi viết</b><ul>'+result.questions.map(q=>'<li>'+esc(q)+'</li>').join('')+'</ul>';
  else html+='<section class="productScriptContinuous"><label><b>Đọc liền mạch</b><textarea id="productScriptContinuous" readonly rows="6" style="display:block;width:100%;box-sizing:border-box">'+esc(result.lines.map(row=>row.new_text.trim()).join(' '))+'</textarea></label><small>Đọc cả đoạn để rà mạch nói. Các ô bên dưới là nhịp thời gian của lời mẫu, không nhất thiết là câu độc lập.</small></section>'+result.lines.map((row,i)=>{const source=project.script.find(l=>l.id===row.id);return '<section style="margin:12px 0"><b>Nhịp '+(i+1)+' · '+stamp(source?.start)+'–'+stamp(source?.end)+'</b><p>Mẫu: '+esc(source?.original||source?.translation||'')+'</p><label>Lời cho '+esc(req.body.product.name)+'<textarea style="display:block;width:100%;box-sizing:border-box" maxlength="5000" data-product-script-draft="'+i+'">'+esc(row.new_text)+'</textarea></label><small>Dữ kiện dùng: '+esc(row.fact_ids.map(k=>labels[k]).join(', ')||'Câu dẫn / kêu gọi')+'</small></section>';}).join('')+(result.notes?.length?'<ul>'+result.notes.map(n=>'<li>'+esc(n)+'</li>').join('')+'</ul>':'')+'<p>AI có thể diễn giải sai; đối chiếu với thông tin sản phẩm trước khi áp dụng. Các clip cũ giữ phiên bản nhưng cần chọn/tạo lại nếu lời đổi.</p>';
  const names={queued:'Đang xếp hàng',running:'Động cơ đang xử lý',submitted:'Đã gửi · chờ kết quả',done:'AI đã hoàn tất · bấm Nhận kết quả',failed:'Lượt viết thất bại',missing:'Không có lượt đang chạy được ghi nhận',unknown:'Kết quả phía AI chưa rõ',unavailable:'Chưa đọc được trạng thái'};
  if(!result)html+='<div role="status"><b>'+esc(req.checking?'Đang kiểm tra trạng thái…':req.remote?names[req.remote.state]||req.remote.state:running?'Đang gửi yêu cầu viết…':'Chưa kiểm tra trạng thái động cơ')+'</b><p>'+esc(req.remote?.message||'')+'</p></div>';
  const pending=!result&&['submitted','unknown'].includes(req.state);
  modal('Lời mới theo sản phẩm',html,'<button data-product-script="brief">Sửa thông tin sản phẩm</button><button data-action="close-modal">Đóng</button>'+(pending?'<button data-product-script="inspect" '+(req.checking?'disabled':'')+'>Kiểm tra trạng thái</button><button data-product-script="recover">Nhận kết quả lượt cũ</button><button data-product-script="restart" '+(running?'disabled':'')+'>Viết theo thông tin hiện tại</button>':'')+(result&&!result.needs_info&&req.state!=='applied'?'<button id="productScriptApply" class="primary" '+(stale?'disabled':'')+'>Áp dụng vào cột Lời mới</button>':'')+(result||req.state==='rejected'?'<button data-product-script="write">Viết lượt mới</button>':''));
  clearTimeout(statusTimer);if(!result&&!req.checking&&(running||['queued','running','submitted'].includes(req.remote?.state))){const room=project.id;statusTimer=setTimeout(()=>{if(project.id===room&&document.querySelector('[data-product-script=inspect]'))inspect().catch(e=>toast(e.message));},2000);}
  $('#productScriptApply')?.addEventListener('click',()=>apply().catch(e=>toast(e.message)));
 }
 async function apply(){const s=state(),req=s.request;if(!req?.result||req.result.needs_info||req.state==='applied')throw Error('Chưa có bản nháp để áp dụng.');if(req.signature!==signature())throw Error('Dữ liệu đã đổi; chưa áp dụng lời cũ.');if(window.SFPromptPipeline?.isRunning()||(project.cloudJobs||[]).some(j=>['queued','running','submitted','unknown','downloading'].includes(j.state)))throw Error('Đợi các lượt tạo đang chạy hoặc đối soát xong trước khi thay lời.');
  const rows=req.result.lines,expected=input().reference_lines;if(rows.length!==expected.length||rows.some((r,i)=>r.id!==expected[i].id||typeof r.new_text!=='string'||!r.new_text.trim()||r.new_text.length>5000))throw Error('Bản nháp không còn khớp các câu nguồn.');
  s.history.push({at:Date.now(),before:project.script.map(l=>({id:l.id,newText:l.newText})),sceneSelections:project.scenes.map(scene=>({id:scene.id,chosen:structuredClone(scene.chosen||{}),dialogueParts:structuredClone(scene.dialogueParts||{})}))});s.history=s.history.slice(-10);
  const before=new Map(project.scenes.map(scene=>[scene.id,JSON.stringify(dialogueFor(scene).map(l=>l.newText))]));
  for(const row of rows)project.script.find(l=>l.id===row.id).newText=row.new_text;
  for(const scene of project.scenes)if(before.get(scene.id)!==JSON.stringify(dialogueFor(scene).map(l=>l.newText))){invalidateFrame(scene);scene.dialogueParts={};}
  req.state='applied';await storeProject();render();scriptDialog();toast('Đã cập nhật Lời mới; giữ nguyên lời gốc, mốc giây và phiên bản clip cũ.');
 }
 document.addEventListener('input',e=>{const el=e.target;if(el.dataset.productScriptField){brief()[el.dataset.productScriptField]=el.value;brief().edited=true;save();}if(el.dataset.productScriptDraft!==undefined){const row=state().request?.result?.lines?.[Number(el.dataset.productScriptDraft)];if(row){row.new_text=el.value;const full=$('#productScriptContinuous');if(full)full.value=state().request.result.lines.map(line=>line.new_text.trim()).join(' ');save();}}});
 document.addEventListener('click',e=>{const button=e.target.closest('[data-product-script]');if(!button)return;e.preventDefault();e.stopImmediatePropagation();const action=button.dataset.productScript;if(action==='inspect')inspect().catch(err=>toast(err.message));if(action==='restart')restart().catch(err=>toast(err.message));if(action==='brief')form();if(action==='review')review();if(action==='write')request().catch(err=>toast(err.message));if(action==='recover')request(true).catch(err=>toast(err.message));},true);
 const nodeBefore=scriptNode;scriptNode=function(){const html=nodeBefore();return project.mode==='photos'?html:html.replace('<div class="scriptSummary">',panel()+'<div class="scriptSummary">');};
 const dialogBefore=scriptDialog;scriptDialog=function(){dialogBefore();if(project.mode!=='photos'){$('#modalContent')?.insertAdjacentHTML('afterbegin',panel());const sourceAI=$('#modalContent [data-action=ai-help]');if(sourceAI)sourceAI.textContent='Phân tích / dịch lại video mẫu';}};
 window.SFProductScript={brief,setProduct,input,signature,form,request,review,apply,state};
})();
