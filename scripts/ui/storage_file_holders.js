// .121: show actual file holders; allow retiring backup-only media explicitly.
function storageHolderText(reason){
 const label={project:'Dự án',library_reference:'Thư viện',pin:'Bản ghim',upload_lease:'Tệp tải lên chờ lưu',job:'Tác vụ',backup:'Sao lưu',other_operation:'Lượt dọn khác'}[reason.type]||reason.type;
 if(reason.type==='upload_lease')return label+' · bảo vệ đến '+new Date(reason.expires*1000).toLocaleString('vi-VN');
 if(reason.type==='backup')return label+' · '+reason.folder+'/'+reason.name+(reason.pinned?' · có ghim trong bản sao lưu':'')+' · dự án '+(reason.room_ids||[]).join(', ');
 if(reason.type==='job')return label+' · '+reason.request_id+' · '+reason.state+' · '+(reason.name||reason.room_id||'chưa gán dự án');
 return label+' · '+(reason.name||reason.note||reason.op_id||reason.key||'không có ghi chú');
}
async function storageInspectOperation(opId){
 try{
  const report=await SceneForgeStorage.api('lifecycle/detail/'+encodeURIComponent(opId));
  modal('Tệp còn lại và nơi đang giữ', '<p>Mỗi tệp dưới đây có đường dẫn và lý do thực tế đang giữ nó. Xóa ngay không tự bỏ tài nguyên của dự án khác.</p>'+report.files.map((file,i)=>'<section style="border-top:1px solid #35404a;padding:12px 0"><b>'+esc(archiveFormat(file.bytes))+' · '+esc(file.mime)+'</b><p style="overflow-wrap:anywhere;user-select:text">'+esc(file.path)+'</p><ul>'+file.reasons.map(reason=>'<li>'+esc(storageHolderText(reason))+'</li>').join('')+'</ul>'+(!file.reasons.length?'<p>Không còn nơi giữ; có thể thử xóa lại.</p>':'')+(file.can_release_backup?'<p>Tệp này chỉ còn phục vụ khôi phục từ sao lưu. Xóa sẽ làm các bản sao lưu liệt kê ở trên không khôi phục được tệp này.</p><button data-storage-release-backup="'+i+'" class="homeDanger">Xóa tệp chỉ còn trong sao lưu…</button>':'')+(file.reasons.some(reason=>reason.type==='pin')?'<button data-storage-unpin-file="'+i+'">Bỏ ghim tệp này…</button>':'')+file.reasons.filter(reason=>reason.type==='project'&&roomFor(reason.room_id)).map(reason=>'<button data-storage-open-owner="'+esc(reason.room_id)+'">Mở dự án '+esc(reason.name)+'</button>').join('')+'</section>').join('')+(report.truncated?'<p>Báo cáo giới hạn 200 mục đầu.</p>':'')+(!report.files.length?'<p>Không còn tệp trong kho thuộc lượt dọn này.</p>':''),'<button id="storageDownloadHolders">Tải báo cáo tệp còn lại</button><button id="storageRetryHolders">Thử xóa lại</button><button id="storageCloseHolders">Đóng</button>');
  $('#storageCloseHolders').onclick=()=>$('#shellDialog').close();
  $('#storageDownloadHolders').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='SceneForge-tep-con-lai-'+opId+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  $('#storageRetryHolders').onclick=async()=>{if(!confirm('Xóa ngay các tệp đủ điều kiện của lượt này?'))return;try{const result=await SceneForgeStorage.api('lifecycle/expedite',{op_id:opId,confirm:true});await hubMeasure(true);toast(storageDeleteResultText(result));await storageInspectOperation(opId);}catch(e){toast(e.message);}};
  $$('[data-storage-release-backup]').forEach(button=>button.onclick=async()=>{
   const file=report.files[Number(button.dataset.storageReleaseBackup)];
   if(!confirm('Xóa hẳn tệp '+file.path+'? Tệp chỉ còn trong sao lưu. Sau khi xóa, các bản sao lưu đã liệt kê không khôi phục được tệp này.'))return;
   button.disabled=true;try{const result=await SceneForgeStorage.api('lifecycle/release-backup-file',{op_id:opId,hash:file.hash,token:report.token,confirm:true});await hubMeasure(true);toast(storageDeleteResultText(result));await storageInspectOperation(opId);}catch(e){toast(e.message);await storageInspectOperation(opId);}finally{button.disabled=false;}
  });
  $$('[data-storage-unpin-file]').forEach(button=>button.onclick=async()=>{const file=report.files[Number(button.dataset.storageUnpinFile)];if(!confirm('Bỏ ghim tệp '+file.path+'? Chỉ bỏ ghim; chưa xóa tệp ở bước này.'))return;try{await SceneForgeStorage.api('pin',{hash:file.hash,pinned:false});await storageInspectOperation(opId);}catch(e){toast(e.message);}});
  $$('[data-storage-open-owner]').forEach(button=>button.onclick=()=>{$('#shellDialog').close();hubClose();openRoom(button.dataset.storageOpenOwner);});
 }catch(error){toast(error.message);}
}
