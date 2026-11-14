/* Motion Studio rooms reuse the reference-workflow bridge, never change another room's mode. */
(()=>{
 function mount(){const choices=document.querySelector('#workflowModes .workflowModeChoices');if(!choices||choices.querySelector('[data-workflow-mode="motion"]'))return;const b=document.createElement('button');b.dataset.workflowMode='motion';b.innerHTML='<span><strong>Motion Studio</strong><small>Chỉnh clip mẫu</small></span>';b.title='Mở nhánh Motion Studio riêng';choices.append(b);}
 const payload=roomPayload;roomPayload=async r=>({...await payload(r),workflowVariant:r.workflowVariant||null});
 const paint=renderWorkflowModes;renderWorkflowModes=function(...args){paint(...args);mount();if(currentRoom?.workflowVariant==='motion')for(const b of workflowModes.querySelectorAll('[data-workflow-mode]')){const active=b.dataset.workflowMode==='motion';b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active));b.setAttribute('aria-current',active?'page':'false');}};
 async function open(product=null,{fresh=false}={}){
  if(changingWorkflow)return;changingWorkflow=true;renderWorkflowModes();
  try{
   await flushFrames();product??=productFor(currentRoom?.productId)||productFor(prefs.product)||products[0];if(!product)throw Error('Tạo sản phẩm trước.');
   let target=!fresh&&rooms.filter(r=>r.productId===product.id&&r.workflowVariant==='motion'&&!archivedRoom(r)).sort((a,b)=>(b.updatedAt||b.createdAt)-(a.updatedAt||a.createdAt))[0];
   if(!target){target=await createWorkflowRoom('reference',product);target.workflowVariant='motion';target.name='Motion Studio · '+product.name;target.slug=uniqueSlug(target.name,rooms.filter(r=>r.id!==target.id&&r.productId===product.id));await persistRoom(target);}
   await openRoom(target.id,'analysis');
  }catch(e){fail(e);}finally{changingWorkflow=false;renderWorkflowModes();}
 }
 workflowModes.addEventListener('click',e=>{const b=e.target.closest('[data-workflow-mode="motion"]');if(!b)return;e.preventDefault();e.stopImmediatePropagation();open();},true);
 const create=$('#newVideo').onclick;$('#newVideo').onclick=function(...args){const value=create.apply(this,args);const body=$('#shellDialog');if(body?.open&&!$('#newMotionStudio')){const b=document.createElement('button');b.id='newMotionStudio';b.className='choice';b.innerHTML='<b>Motion Studio</b><small>Clip mẫu + nhân vật, trang phục và sản phẩm tham khảo</small>';$('#createPhotos')?.after(b);b.onclick=()=>{body.close();open(null,{fresh:true});};}return value;};
 const switchBefore=switchWorkflow;switchWorkflow=function(mode){return mode==='motion'?open():switchBefore(mode);};window.SceneForgeApp.switchWorkflow=switchWorkflow;
 window.SceneForgeApp.openMotionFlow=async()=>{const status=await engineRequest('flow/simple/status');if(status.active_request)throw Error('Đợi lượt Flow hiện tại xong trước.');const id=status.selection?.account_id;if(!status.selection?.available||!id)return accountScreen('flow');return openAccountWebLogin('flow',{account_id:id});};
 window.SceneForgeApp.openMotionStudio=(productId,options={})=>open(productFor(productId),options);
 mount();
})();
