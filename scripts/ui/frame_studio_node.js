/* Rebuilt frame node: one editor, one queue, one result owner. Existing prompt/account APIs stay. */
(()=>{
 const q=s=>document.querySelector(s);let selected=null,error='',refreshing=false;
 const busy=()=>SFFrameImages.isRunning();
 const names={prepared:'Đang chuẩn bị',submitted:'Đang tạo',queued:'Đang chờ',running:'Đang tạo',downloading:'Đang nhận ảnh',done:'Có ảnh · đang nhập',imported:'Có ảnh',unknown:'Chưa nhận xong',failed:'Chưa tạo được',stale:'Đầu vào đã đổi',not_submitted:'Chưa gửi'};
 function label(s){const j=SFFrameImages.job(s);return j?names[j.state]||j.state:s.frames.length?'Có ảnh · chờ duyệt':'Chưa tạo';}
 function renderNode(n){
  n.classList.add('sfFrameStudio');n.style.width='430px';
  const run=SFFrameImages.runState(),active=busy(),missing=project.scenes.filter(s=>!s.frames.length);
  n.innerHTML=port('in')+port('out','▣')+'<header><strong>Ảnh khung</strong><span>'+project.scenes.filter(s=>s.frames.length).length+'/'+project.scenes.length+' cảnh</span></header><div class="nodeBody"><p class="sfStudioPhase" role="status">'+esc(active?(run?.phase||'Đang xử lý'):error||'Chọn cảnh để xem prompt và tạo ảnh')+'</p><div class="sfStudioGrid">'+project.scenes.map(s=>'<button class="sfStudioCard" data-studio="open" data-scene="'+esc(s.id)+'"><img src="'+esc(s.frames.at(-1)?.image||s.thumbs?.[0]||project.source?.poster||'')+'" alt="Cảnh '+(s.index+1)+'"><b>Cảnh '+(s.index+1)+'</b><small>'+esc(s.approvedFrame?'Đã duyệt':label(s))+'</small></button>').join('')+'</div><div class="sfStudioActions"><button data-studio="create-missing" class="primary" '+(!missing.length||active?'disabled':'')+'>Tạo '+missing.length+' ảnh còn thiếu</button>'+(active?'<button data-studio="pause">Tạm dừng</button>':'')+'</div></div>';
 }
 async function savePrompt(s){const field=q('#studioEnglish');if(!field||field.disabled)return;const text=field.value.trim();if(!text||text===SFFrameImages.prompt(s))return;s.framePromptOverride=SFPromptContract.sceneText(text);s.frameManualInput=SFPromptPipeline.snapshot(s,'image');invalidateFrame(s);await storeProject();}
 function draw(s){
  const j=SFFrameImages.job(s),active=busy(),image=s.frames.find(f=>f.id===s.frameSelectionId)||s.frames.at(-1),source=s.thumbs?.[0]||project.source?.poster;
  modal('Ảnh khung · Cảnh '+(s.index+1),'<section id="frameStudioEditor"><div class="sfStudioPreview"><figure><img src="'+esc(source||'')+'" alt="Ảnh nguồn"><figcaption>Ảnh nguồn</figcaption></figure><figure>'+(image?'<img src="'+esc(image.image)+'" alt="Ảnh kết quả">':'<div class="sfStudioEmpty">Ảnh sẽ hiện tại đây</div>')+'<figcaption>'+esc(image?'Bản '+image.version:'Chưa có ảnh')+'</figcaption></figure></div><p id="studioSceneStatus" role="status">'+esc(error||j?.error||label(s))+'</p><details><summary>Prompt · giữ khung hiện tại</summary><textarea id="studioEnglish" rows="10" '+(active?'disabled':'')+'>'+esc(SFFrameImages.prompt(s))+'</textarea><div class="sfStudioActions"><button data-studio="save-prompt" '+(active?'disabled':'')+'>Lưu prompt</button><button data-studio="optimize" '+(active?'disabled':'')+'>AI tối ưu · tùy chọn</button></div></details><details><summary>Ảnh tham khảo của cảnh</summary><div class="sfStudioRefs">'+refsFor(s).flatMap(role=>sceneReference(s,role).images.map(i=>'<figure><img src="'+esc(i.image||i)+'" alt="'+esc(refNames[role])+'"><figcaption>'+esc(refNames[role])+'</figcaption></figure>')).join('')+'</div></details>'+(s.frames.length?'<details><summary>Các bản ảnh · '+s.frames.length+'</summary><div class="sfStudioRefs">'+s.frames.map(f=>'<button data-studio="version" data-version="'+esc(f.id)+'"><img src="'+esc(f.image)+'" alt="Bản '+f.version+'">Bản '+f.version+'</button>').join('')+'</div></details>':'')+'</section>',(active?'<button data-studio="pause">Tạm dừng</button>':'<button data-studio="create" class="primary">'+(image?'Tạo lại ảnh':'Tạo ảnh')+'</button>')+(j&&!['imported','not_submitted'].includes(j.state)?'<button data-studio="receive" '+(active?'disabled':'')+'>Nhận ảnh của lượt này</button>':'')+(image?'<button data-studio="approve" '+(active?'disabled':'')+'>Duyệt ảnh</button>':'')+(j&&['unknown','failed','stale'].includes(j.state)?'<button data-studio="fresh" '+(active?'disabled':'')+'>Tạo lượt mới…</button>':''));
  q('#modal').classList.remove('mniInspector');q('#modal').classList.add('sfStudioDialog');
 }
 async function open(id){const s=sceneBy(id);if(!s)return;selected=id;error='';if(!busy()&&(!SFFrameImages.job(s)||['imported','failed','not_submitted'].includes(SFFrameImages.job(s).state))){try{await SFFrameImages.prepare(s);}catch(e){error=e.message;}}draw(s);}
 function refresh(){if(q('#modal')?.open&&q('#frameStudioEditor')){const s=sceneBy(selected);if(s)draw(s);}}
 async function action(a,b){
  const s=sceneBy(b.dataset.scene||selected);error='';
  if(a==='open')return open(s.id);
  if(a==='pause'){SFFrameImages.pause();return refresh();}
  if(busy())return;
  if(a==='create-missing')return SFFrameImages.create(project.scenes.filter(s=>!s.frames.length));
  if(!s)return;
  if(a==='save-prompt'){await savePrompt(s);return refresh();}
  if(a==='version'){const f=s.frames.find(f=>f.id===b.dataset.version);if(f){s.frameSelectionId=f.id;await storeProject();}return refresh();}
  if(a==='approve'){s.frameSelectionId??=s.frames.at(-1)?.id;closeModal();return approvalApprove('frame',[{s,part:null}],true);}
  if(a==='receive')return SFFrameImages.receive(s);
  if(a==='optimize'){await savePrompt(s);await SFFrameImages.optimize(s);return refresh();}
  if(a==='fresh')return SFFrameImages.retry(s);
  if(a==='create'){await savePrompt(s);return SFFrameImages.create([s],{regenerate:!!s.frames.length});}
 }
 document.addEventListener('click',e=>{const b=e.target.closest('[data-studio]');if(!b)return;e.preventDefault();e.stopImmediatePropagation();Promise.resolve(action(b.dataset.studio,b)).catch(e=>{error=e.message;toast(error);}).finally(()=>{render();refresh();});},true);
 window.SFFrameStudio={renderNode,open,refresh};
 const oldOpen=SFMediaNodes.open;SFMediaNodes.open=(kind,id,...rest)=>kind==='frame'?open(id):oldOpen(kind,id,...rest);
 const oldGallery=g6Open;g6Open=(kind,id,...rest)=>kind==='frame'?open(id):oldGallery(kind,id,...rest);
 // After reopening, this owner alone may import its own completed jobs. No automatic resend.
 setInterval(async()=>{if(refreshing||busy()||!project?.scenes||q('#studioEnglish')===document.activeElement)return;const s=project.scenes.find(s=>{const j=SFFrameImages.job(s);return j&&['submitted','queued','running','downloading','done'].includes(j.state);});if(!s)return;refreshing=true;try{await SFFrameImages.receive(s,{readOnly:true});}catch{}finally{refreshing=false;}},2500);
 setInterval(()=>{if(!q('#frameStudioEditor')||!q('#modal')?.open)return;const s=sceneBy(selected);if(!s)return;const j=SFFrameImages.job(s),active=busy(),activity=SFPromptPipeline.activity();const message=error||j?.error||(active?(activity?.stage==='writing'?'Đang tối ưu prompt…':activity?.stage==='frame-preparing'?'Đang chuẩn bị khung nguồn…':SFFrameImages.runState()?.phase||'Đang nhận ảnh…'):label(s));q('#studioSceneStatus').textContent=message;for(const b of q('#modalFooter').querySelectorAll('[data-studio]')){if(active&&b.dataset.studio!=='pause')b.disabled=true;}if(active&&!q('#modalFooter [data-studio=pause]'))q('#modalFooter').insertAdjacentHTML('afterbegin','<button data-studio="pause">Tạm dừng</button>');},500);
 const style=document.createElement('style');style.textContent='.sfStudioGrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.sfStudioCard{display:flex;flex-direction:column;align-items:stretch;gap:4px;padding:5px;min-width:0;text-align:left}.sfStudioCard img{width:100%;aspect-ratio:9/16;object-fit:cover;border-radius:7px}.sfStudioCard small{font-size:10px;color:#aab5bc}.sfStudioActions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.sfStudioPreview{display:grid;grid-template-columns:1fr 1fr;gap:18px}.sfStudioPreview figure{margin:0;min-width:0}.sfStudioPreview img,.sfStudioEmpty{width:100%;height:390px;object-fit:contain;background:#101315;border-radius:12px}.sfStudioEmpty{display:grid;place-items:center;color:#93a0ae}.sfStudioRefs{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}.sfStudioRefs figure{margin:0;width:90px}.sfStudioRefs img{width:80px;height:110px;object-fit:contain}.sfStudioPhase{font-size:12px;overflow-wrap:anywhere}.sfStudioDialog details{margin:12px 0}.sfStudioDialog textarea{width:100%;margin-top:10px}';document.head.append(style);
 render();
})();
