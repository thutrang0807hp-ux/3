/* Gemini's browser transport is discovered automatically; this panel only shows status/help. */
(()=>{
 let signature='',reading=false;
 const q=s=>document.querySelector(s);
 async function open(){
  let setup;try{setup=await engineRequest('browser-bridge/setup');}catch(e){toast(e.message);return;}
  modal('Gemini Chat · tự kết nối','<section id="geminiAutoConnect"><p>Cài tiện ích SceneForge, mở Chrome/Edge đã đăng nhập Gemini và mở app. Tiện ích tự kết nối; không nhập mã.</p><p id="geminiAutoStatus" role="status">Đang nhận trạng thái tiện ích…</p><p><a href="'+esc(setup.download)+'" download="SceneForge-Browser-Connect.zip">Tải tiện ích Chrome/Edge</a> · <a href="https://gemini.google.com/app" target="_blank" rel="noopener">Đăng nhập Gemini trong trình duyệt</a></p><details><summary>Cài tiện ích lần đầu</summary><p>Giải nén ZIP. Mở chrome://extensions hoặc edge://extensions → Chế độ nhà phát triển → Tải tiện ích đã giải nén. Nếu đã cài, thay file trong thư mục cũ rồi bấm Tải lại ⟳.</p></details><p>Khi tiện ích nhận được app và đọc được ô chat Gemini, tài khoản xuất hiện tại đây. Node, prompt và ảnh tham khảo giữ nguyên.</p></section>','<button id="geminiAutoBack">Về tài khoản</button>');
  const host=q('#geminiAutoConnect');q('#geminiAutoBack').onclick=()=>accountScreen('gemini_chat');
  async function poll(){
   if(!host.isConnected||!q('#shellDialog')?.open)return;
   try{const data=await engineRequest('gemini-chat/browser-status');if(!host.isConnected)return;q('#geminiAutoStatus').textContent=data.message+(data.extension_version?' · tiện ích '+data.extension_version:'');if(data.ready){await accountScreen('gemini_chat');return;}}
   catch(e){if(host.isConnected)q('#geminiAutoStatus').textContent=e.message;}
   setTimeout(poll,1500);
  }
  poll();
 }
 async function watch(){
  if(reading||!q('#shellDialog')?.open||!q('#settingsAccounts')||typeof accountDashboard==='undefined'||accountDashboard?.service!=='gemini_chat')return;
  reading=true;try{const data=await engineRequest('gemini-chat/browser-status'),next=JSON.stringify([data.ready,data.account_ids,data.extension_version]);if(signature!==next){signature=next;if(data.ready)await accountScreen('gemini_chat',false);}}catch{}finally{reading=false;}
 }
 setInterval(watch,2000);window.SFGeminiAuto={open};
})();
