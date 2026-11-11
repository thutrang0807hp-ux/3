/* Batch only reads the shared Settings account selection; it has no login/session store. */
(()=>{
 let serial=0;
 const chatSources=new Set(['gemini_chat','chatgpt','grok','meta','flow']);
 const current=()=>$('#batchEngine')?.value;
 async function refresh(){
  const source=current(),node=$('#batchAccountNow'),button=$('#batchConnectSource'),ticket=++serial;
  if(!node||!source)return;
  node.dataset.accountState='loading';node.dataset.source=source;if(button)button.onclick=()=>{const selected=current();if(chatSources.has(selected))return accountScreen(selected);};
  if(source==='simulation'){node.textContent='Mô phỏng · không dùng tài khoản';node.dataset.accountState='simulation';return;}
  if(source==='gemini'){node.textContent='Gemini API dùng key riêng trong Cài đặt → Phân tích (AI).';node.dataset.accountState='api';return;}
  if(!chatSources.has(source))return;
  node.textContent='Đang đọc tài khoản trong Cài đặt…';
  try{
   if(!batchIsLocal())throw Error('Mở bản local để dùng tài khoản đã lưu.');
   const status=await engineRequest(batchStatusPath(source));
   if(ticket!==serial||current()!==source||!node.isConnected)return;
   const selection=status.selection||{},ready=status.installed!==false&&status.configured===true&&selection.available===true&&!!selection.token;
   node.dataset.accountState=ready?'ready':'attention';
   if(status.installed===false)node.textContent='Thiếu bộ chạy '+batchSources[source]+'. Xem hướng dẫn trong Cài đặt → Tài khoản.';
   else if(ready){node.textContent=(selection.mode==='balanced'?'Chia việc theo tài khoản đã bật':selection.mode==='failover'?'Dự phòng theo thứ tự đã chọn':'Đang dùng: '+(selection.account_name||'Tài khoản đã chọn'))+' · từ Cài đặt';}
   else node.textContent='Chưa có tài khoản sẵn sàng. Chọn tài khoản đã lưu hoặc đăng nhập trên web trong Cài đặt.';
   if(button){button.hidden=false;button.textContent=ready?'Đổi tài khoản trong Cài đặt':'Chọn / đăng nhập tài khoản';button.onclick=()=>accountScreen(current());}
   node.title='Dùng lại phiên tài khoản trong Cài đặt. Không yêu cầu mã kết nối SceneForge cho mỗi lượt; dịch vụ vẫn có thể yêu cầu đăng nhập/xác minh khi hết phiên.';
  }catch(error){if(ticket===serial&&current()===source){node.textContent='Chưa đọc được tài khoản: '+error.message;node.dataset.accountState='attention';}}
 }
 batchAccountNow=refresh;
 batchPage.addEventListener('change',event=>{if(event.target.id==='batchEngine')refresh();},true);
 const mount=batchMount;batchMount=function(){mount();const node=$('#batchAccountNow');if(node){node.setAttribute('role','status');node.setAttribute('aria-live','polite');node.classList.add('batchSharedAccount');const caption=document.createElement('small');caption.className='batchSharedAccountHint';caption.textContent='Dùng chung tài khoản trong Cài đặt · không kết nối lại theo từng lượt';node.after(caption);const refreshButton=document.createElement('button');refreshButton.id='batchRefreshSharedAccount';refreshButton.type='button';refreshButton.textContent='↻ Làm mới tài khoản';refreshButton.onclick=()=>refresh();caption.after(refreshButton);}refresh();};

 // Account changes are applied on return, without opening a login window.
 $('#shellDialog').addEventListener('close',()=>{if(batchOpen)refresh();});
 window.addEventListener('focus',()=>{if(batchOpen)refresh();});
 window.addEventListener('sceneforge:google-accounts',()=>{if(batchOpen)refresh();});
 window.SFBatchAccounts={refresh};
})();
