/* Settings-local cleanup navigation and committed-snapshot reconciliation. */
(()=>{
 let context=null,painting=false,leaving=false;
 const locked=()=>storageMutationBusy||SceneForgeStorage.state.mutating;
 async function back(force=false){if(!force&&locked())return;if(!context)return g5OpenSettings('storage');context.detail=false;await restoreRoom();await g5OpenSettings('storage');const n=document.querySelector('.g5SettingsScroll');if(n)n.scrollTop=context.scroll;}
 async function restoreRoom(){if(!context)return;const r=roomFor(context.room);if(!currentRoom&&r&&!r.deleted)await openRoom(r.id,context.view);}
 const baseModal=modal;modal=function(title,body,actions=''){
  if(context&&!painting&&/^(Dọn|Xác nhận|Công việc của dự án)/.test(title)){
   context.detail=true;painting=true;try{baseModal('Cài đặt','<div class="g5Settings">'+context.nav+'<section class="g5SettingMain"><header class="g5SettingsTitle"><button id="smReturnSettings">← Dữ liệu & dung lượng</button><h2>'+esc(title)+'</h2></header><div class="g5SettingsScroll">'+body+'<div class="smInlineActions">'+actions+'</div></div></section></div>','');$('#shellDialog').classList.add('wideDialog','g5SettingsDialog');$('#smReturnSettings').onclick=()=>back().catch(fail);$$('[data-g5-tab]').forEach(b=>b.onclick=async()=>{if(locked())return;await restoreRoom();context=null;g5OpenSettings(b.dataset.g5Tab);});}finally{painting=false;}return;
  }
  return baseModal(title,body,actions);
 };
 const settingsOpen=g5OpenSettings;g5OpenSettings=async function(...a){if(context){context.detail=false;await restoreRoom();}const result=await settingsOpen(...a);if((a[0]||'overview')==='storage'&&!context?.detail)await settingsMeasure();return result;};
 const settingsPaint=g5PaintSettings;g5PaintSettings=function(...a){if(context?.detail)return;return settingsPaint(...a);};
 function capture(){if(!context&&$('#dialogBody .g5Settings')&&g5SettingsTab==='storage')context={nav:$('.g5Settings>nav').outerHTML,scroll:$('.g5SettingsScroll').scrollTop,room:currentRoom?.id,view:currentView};}
 const cleanup=storageCleanupDialog;storageCleanupDialog=async function(...args){capture();return cleanup(...args);};
 const bulk=storageBulk.onclick;storageBulk.onclick=async function(...a){capture();return bulk.apply(this,a);};
 window.storagePrepareRoom=async id=>{if(activeWorkers.has(id))throw Error('Dự án còn đang phân tích.');if(typeof batchState!=='undefined'&&batchState?.jobs?.some(j=>j.status==='running'))throw Error('Đợi lượt hàng loạt xong trước khi dọn.');await SceneForgeStorage.flush();};
 const close=storageCloseRoom;storageCloseRoom=async function(id){if(!context)return close(id);await storagePrepareRoom(id);await flushFrames();$('#roomFrames').replaceChildren();currentRoom=null;frameRoom=null;await SceneForgeStorage.flush();};
 async function adopt(result){
   await SceneForgeStorage.adoptCommittedSnapshot(result.snapshot);
   [products,rooms,jobs,notifications]=await Promise.all(['products','rooms','jobs','notifications'].map(s=>io(s,'readonly')));
   prefs={...prefs,...await io('prefs','readonly','main')};if(!roomFor(prefs.lastRoom))prefs.lastRoom=null;const order=prefs.productOrder||[];products.sort((a,b)=>(order.indexOf(a.id)<0?9999:order.indexOf(a.id))-(order.indexOf(b.id)<0?9999:order.indexOf(b.id)));notifications.sort((a,b)=>b.at-a.at);
   SceneForgeStorage.clearMediaCache();recipeCache=null;recipeLoading=null;settingsStorageData=null;for(const id of storageManagerSelected)if(!roomFor(id))storageManagerSelected.delete(id);for(const id of archiveSelection)if(!roomFor(id))archiveSelection.delete(id);
   render();await back(true);toast(storageDeleteResultText(result));
 }
 window.SFStorageManageFlow={active:()=>!!context,adopt};
 const apply=storageApplyPlan;storageApplyPlan=async function(plan){
  if(!context)return apply(plan);
  if(storageMutationBusy)throw Error('Đợi thao tác dọn hiện tại hoàn tất.');storageMutationBusy=true;let sent=false;
  try{
   if(SceneForgeStorage.state.dirty||SceneForgeStorage.state.busy||SceneForgeStorage.state.revision!==plan.revision)throw Error('Kho đã đổi; quay lại xem phạm vi trước khi xóa.');
   await SceneForgeStorage.markMutation(plan.token);sent=true;
   const result=await SceneForgeStorage.edit(()=>SceneForgeStorage.api('lifecycle/execute',{mutation_id:plan.token,room_id:plan.room_id,mode:plan.mode,days:plan.days,published:plan.published,revision:plan.revision,token:plan.token,confirm:true}));
   await adopt(result);return result;
  }catch(e){if(sent)SceneForgeStorage.pause();throw e;}finally{storageMutationBusy=false;}
 };
 const measure=settingsMeasure;settingsMeasure=async function(...a){if(SceneForgeStorage.state.active&&!storageMutationBusy)await SceneForgeStorage.flush();return measure(...a);};
 const list=storageManagerList;storageManagerList=function(...a){const template=document.createElement('template');template.innerHTML=list(...a).replace(/0 file · 0 ảnh · 0 video/g,'Không còn media · vẫn còn dữ liệu dự án');for(const row of storageManagerRows()){if(row.usage?.files!==0)continue;const original=[...template.content.querySelectorAll('[data-sm-room]')].find(b=>b.dataset.smRoom===row.room.id);if(original){const button=document.createElement('button');button.dataset.smRemoveEmpty=row.room.id;button.className='smDanger';button.textContent='Xóa dự án…';button.disabled=original.disabled;original.after(button);}}return '<p class="settingsMuted">Xóa tệp ngoài app không xóa bản sao đã nhập. Dự án không còn media vẫn có thể còn kịch bản/cài đặt; chọn Xóa dự án nếu không cần giữ.</p>'+template.innerHTML;};
 const bind=storageManagerBindList;storageManagerBindList=function(...a){bind(...a);$$('[data-sm-remove-empty]').forEach(b=>b.onclick=()=>storageCleanupDialog(b.dataset.smRemoveEmpty,'delete'));};
 const rows=storageManagerRows;storageManagerRows=function(){const measured=settingsStorageData,canonical=Number.isInteger(measured?.revision)&&measured.revision===SceneForgeStorage.state.revision?new Set(measured.room_usage.map(x=>x.id)):null;return rows().filter(({room})=>!room.deleted&&(!canonical||canonical.has(room.id)));};
 $('#shellDialog').addEventListener('cancel',e=>{if(context&&locked())e.preventDefault();});
 $('#shellDialog').addEventListener('close',()=>{setTimeout(async()=>{if(!context||$('#shellDialog').open||leaving||locked())return;leaving=true;try{await restoreRoom();if(!currentRoom&&currentView!=='overview')await showView('overview');}catch(e){fail(e);}finally{context=null;leaving=false;}},0);});
})();
