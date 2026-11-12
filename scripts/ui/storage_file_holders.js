// .122: show actual file holders; allow retiring backup-only media explicitly.
function storageHolderText(reason){
 if(reason.type==='recipe_library')return 'Kho kịch bản · '+[...new Set((reason.references||[]).map(ref=>ref.name))].join('; ');
 const label={project:'Dự án',library_reference:'Thư viện',pin:'Bản ghim',upload_lease:'Tệp tải lên chờ lưu',job:'Tác vụ',backup:'Sao lưu',other_operation:'Lượt dọn khác'}[reason.type]||reason.type;
 if(reason.type==='upload_lease')return label+' · bảo vệ đến '+new Date(reason.expires*1000).toLocaleString('vi-VN');
 if(reason.type==='backup')return label+' · '+reason.folder+'/'+reason.name+(reason.pinned?' · có ghim trong bản sao lưu':'')+' · dự án '+(reason.room_ids||[]).join(', ');
 if(reason.type==='job')return label+' · '+reason.request_id+' · '+reason.state+' · '+(reason.name||reason.room_id||'chưa gán dự án');
 return label+' · '+(reason.name||reason.note||reason.op_id||reason.key||'không có ghi chú');
}
async function storageInspectOperation(opId){
 try{
  const report=await SceneForgeStorage.api('lifecycle/detail/'+encodeURIComponent(opId));
  modal('Tệp còn lại và nơi đang giữ', '<p>Mỗi tệp dưới đây có đường dẫn và lý do thực tế đang giữ nó. Xóa ngay không tự bỏ tài nguyên của dự án khác.</p>'+report.files.map((file,i)=>'<section style="border-top:1px solid #35404a;padding:12px 0"><b>'+esc(archiveFormat(file.bytes))+' · '+esc(file.mime)+'</b><p style="overflow-wrap:anywhere;user-select:text">'+esc(file.path)+'</p><ul>'+file.reasons.map(reason=>'<li>'+esc(storageHolderText(reason))+'</li>').join('')+'</ul>'+(!file.reasons.length?'<p>Không còn nơi giữ; có thể thử xóa lại.</p>':'')+(file.can_detach_recipe?'<p>Gỡ ảnh này khỏi các mục Kho kịch bản đã liệt kê; giữ nguyên lời, nhịp cảnh và nội dung khác.</p><button data-storage-detach-recipe="'+i+'" class="homeDanger">Gỡ ảnh khỏi kịch bản và xóa nếu không còn nơi dùng…</button>':'')+(file.can_release_backup?'<p>Tệp này chỉ còn phục vụ khôi phục từ sao lưu. Xóa sẽ làm các bản sao lưu liệt kê ở trên không khôi phục được tệp này.</p><button data-storage-release-backup="'+i+'" class="homeDanger">Xóa tệp chỉ còn trong sao lưu…</button>':'')+(file.reasons.some(reason=>reason.type==='pin')?'<button data-storage-unpin-file="'+i+'">Bỏ ghim tệp này…</button>':'')+file.reasons.filter(reason=>reason.type==='project'&&roomFor(reason.room_id)).map(reason=>'<button data-storage-open-owner="'+esc(reason.room_id)+'">Mở dự án '+esc(reason.name)+'</button>').join('')+'</section>').join('')+(report.truncated?'<p>Báo cáo giới hạn 200 mục đầu.</p>':'')+(!report.files.length?'<p>Không còn tệp trong kho thuộc lượt dọn này.</p>':''),'<button id="storageDownloadHolders">Tải báo cáo tệp còn lại</button><button id="storageRetryHolders">Thử xóa lại</button><button id="storageCloseHolders">Đóng</button>');
  $('#storageCloseHolders').onclick=()=>$('#shellDialog').close();
  $('#storageDownloadHolders').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='SceneForge-tep-con-lai-'+opId+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  $('#storageRetryHolders').onclick=async()=>{if(!confirm('Xóa ngay các tệp đủ điều kiện của lượt này?'))return;try{const result=await SceneForgeStorage.api('lifecycle/expedite',{op_id:opId,confirm:true});await hubMeasure(true);toast(storageDeleteResultText(result));await storageInspectOperation(opId);}catch(e){toast(e.message);}};
  $$('[data-storage-detach-recipe]').forEach(button=>button.onclick=async()=>{
   const file=report.files[Number(button.dataset.storageDetachRecipe)];
   const names=file.reasons.filter(reason=>reason.type==='recipe_library').flatMap(reason=>reason.references.map(ref=>ref.name));
   if(!confirm('Gỡ ảnh khỏi '+[...new Set(names)].join(', ')+'? Giữ nguyên nội dung kịch bản. Xóa tệp nếu không còn nơi khác dùng; sao lưu cũ cũng không khôi phục ảnh đã gỡ.'))return;
   if(storageMutationBusy)return toast('Đợi thao tác kho hiện tại.');
   storageMutationBusy=true;const wasInert=document.body.inert;document.body.inert=true;let sent=false,complete=false;
   try{
    await SceneForgeStorage.flush();
    if(SceneForgeStorage.state.revision!==report.revision){toast('Kho đã có thay đổi; xem lại danh sách trước khi gỡ ảnh.');await storageInspectOperation(opId);return;}
    const result=await SceneForgeStorage.edit(async()=>{const id=crypto.randomUUID();await SceneForgeStorage.markMutation(id,'checkpoint');sent=true;return SceneForgeStorage.api('lifecycle/detach-recipe-image',{op_id:opId,hash:file.hash,token:report.token,mutation_id:id,confirm:true});});
    SceneForgeStorage.pause();await SceneForgeStorage.hydrate(result.snapshot);recipeCache=null;recipeLoading=null;SceneForgeStorage.clearMediaCache();
    sessionStorage.setItem('sceneforge-last-cleanup',JSON.stringify(result));complete=true;location.reload();
   }catch(error){if(sent){SceneForgeStorage.pause();error.message+=' Mở lại app để nạp trạng thái kho, tránh lưu đè dữ liệu cũ.';}toast(error.message);}
   finally{storageMutationBusy=false;if(!complete)document.body.inert=wasInert;}
  });
  $$('[data-storage-release-backup]').forEach(button=>button.onclick=async()=>{
   const file=report.files[Number(button.dataset.storageReleaseBackup)];
   if(!confirm('Xóa hẳn tệp '+file.path+'? Tệp chỉ còn trong sao lưu. Sau khi xóa, các bản sao lưu đã liệt kê không khôi phục được tệp này.'))return;
   button.disabled=true;try{const result=await SceneForgeStorage.api('lifecycle/release-backup-file',{op_id:opId,hash:file.hash,token:report.token,confirm:true});await hubMeasure(true);toast(storageDeleteResultText(result));await storageInspectOperation(opId);}catch(e){toast(e.message);await storageInspectOperation(opId);}finally{button.disabled=false;}
  });
  $$('[data-storage-unpin-file]').forEach(button=>button.onclick=async()=>{const file=report.files[Number(button.dataset.storageUnpinFile)];if(!confirm('Bỏ ghim tệp '+file.path+'? Chỉ bỏ ghim; chưa xóa tệp ở bước này.'))return;try{await SceneForgeStorage.api('pin',{hash:file.hash,pinned:false});await storageInspectOperation(opId);}catch(e){toast(e.message);}});
  $$('[data-storage-open-owner]').forEach(button=>button.onclick=()=>{$('#shellDialog').close();hubClose();openRoom(button.dataset.storageOpenOwner);});
 }catch(error){toast(error.message);}
}
