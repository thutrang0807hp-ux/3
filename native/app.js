(()=>{
'use strict';
if(new URLSearchParams(location.search).get('embedded')==='1'&&window.parent!==window)document.body.classList.add('embedded');
const screens=[
 ['media','Tư liệu','Kho video và âm thanh, nhóm theo loại. Dự án mẫu có ba clip dọc và một bản nhạc.'],
 ['text','Văn bản','Bảng chữ của Concat gốc: kiểu chữ, mẫu tiêu đề và các công cụ liên quan.'],
 ['stickers','Nhãn dán','Kho nhãn dán và các danh mục trong giao diện native.'],
 ['transitions','Chuyển cảnh','Bảng chọn chuyển cảnh của ứng dụng gốc.'],
 ['effects','Hiệu ứng','Các nhóm hiệu ứng hình ảnh và âm thanh, với ảnh xem trước được Concat cung cấp.'],
 ['filters','Bộ lọc','Kho bộ lọc màu của Concat và các hình xem trước.'],
 ['templates','Mẫu dựng','Bảng mẫu dựng trong bản Concat đang chạy.'],
 ['video-inspector','Thuộc tính video','Chọn clip video để xem bảng tùy chỉnh tương ứng bên phải.'],
 ['text-inspector','Thuộc tính chữ','Chọn lớp chữ trên timeline để xem nội dung, kiểu chữ và thiết lập của clip.'],
 ['audio-inspector','Thuộc tính âm thanh','Chọn đoạn nhạc để xem bảng chỉnh âm thanh.'],
 ['export','Xuất video','Bảng xuất gốc: độ phân giải, tốc độ khung hình, codec và chất lượng. Nút xanh bên dưới chỉ mở MP4 mẫu đã xuất.']
];
const select=document.querySelector('#screen'),spots=document.querySelector('#hotspots'),viewer=document.querySelector('#viewer'),notice=document.querySelector('#announcement');
let img=document.querySelector('#screenImage');
const title=document.querySelector('#screenTitle'),description=document.querySelector('#screenDescription');
const tabs=[...document.querySelectorAll('[data-mode]')];
const videos=[...document.querySelectorAll('video')];
const status=document.querySelector('#screenStatus'),retry=document.querySelector('#retryScreen');
const loading=document.querySelector('#screenLoading');
const cache=new Map();
const cacheLimit=matchMedia('(max-width:600px)').matches?2:4;
const connection=navigator.connection;
let current=null,requested='media',mode=null,revision=0,idleTimer,loadingTimer,active=true;
for(const [id,label] of screens){const option=document.createElement('option');option.value=id;option.textContent=label;select.append(option);}
const common=[['media',18,42,45,48],['text',65,42,35,48],['stickers',104,42,50,48],['transitions',156,42,69,48],['effects',228,42,49,48],['filters',280,42,42,48],['templates',327,42,65,48],['export',1217,3,78,27],['video-inspector',198,923,79,72],['text-inspector',198,879,79,40],['audio-inspector',198,799,239,72]];
function pauseVideos(){videos.forEach(video=>video.pause());}
function pruneCache(){
 for(const key of cache.keys()){
  if(cache.size<=cacheLimit)break;
  if(key!==current&&key!==requested)cache.delete(key);
 }
}
function loadScreen(id){
 if(cache.has(id)){const entry=cache.get(id);cache.delete(id);cache.set(id,entry);return entry.ready;}
 const picture=img.src.endsWith('/'+id+'.webp')&&!(img.complete&&!img.naturalWidth)?img:new Image(1440,1000);
 picture.decoding='async';
 if(picture!==img)picture.src='./assets/'+id+'.webp';
 const entry={picture};
 entry.ready=(async()=>{
  try{
   await picture.decode();
   if(!picture.naturalWidth)throw Error('empty image');
   return picture;
  }catch(error){if(cache.get(id)===entry)cache.delete(id);throw error;}
 })();
 cache.set(id,entry);pruneCache();return entry.ready;
}
function warmNext(){
 clearTimeout(idleTimer);
 if(!active||document.hidden||mode!=='explore'||connection?.saveData||/2g/.test(connection?.effectiveType||''))return;
 idleTimer=setTimeout(()=>{
  if(!active||document.hidden||mode!=='explore')return;
  const next=screens[(screens.findIndex(s=>s[0]===current)+1)%screens.length][0];
  loadScreen(next).catch(()=>{});
 },600);
}
function hotspot(id,left,top,width,height,fn){
 const button=document.createElement('button');button.className='hotspot';
 const label=screens.find(s=>s[0]===id)?.[1]||id;
 button.setAttribute('aria-label',id==='export'&&current==='export'?'Xem MP4 mẫu đã xuất':'Xem '+label);
 button.dataset.label=label;
 button.style.cssText=`left:${left/14.4}%;top:${top/10}%;width:${width/14.4}%;height:${height/10}%`;
 button.onclick=fn||(()=>showScreen(id));return button;
}
async function showScreen(id,writeUrl=true){
 const item=screens.find(s=>s[0]===id)||screens[0];requested=item[0];select.value=requested;
 if(current===requested){++revision;clearTimeout(loadingTimer);viewer.setAttribute('aria-busy','false');loading.hidden=true;status.hidden=true;if(writeUrl&&location.hash!=='#'+current)history.replaceState(null,'','#'+current);return;}
 const ticket=++revision;
 clearTimeout(idleTimer);clearTimeout(loadingTimer);status.hidden=true;loading.hidden=true;
 viewer.setAttribute('aria-busy','true');
 loadingTimer=setTimeout(()=>{if(ticket===revision)loading.hidden=false;},150);
 try{
  const picture=await loadScreen(requested);
  if(ticket!==revision)return;
  current=item[0];picture.alt='Cửa sổ Concat gốc — '+item[1];
  if(img!==picture){img.replaceWith(picture);picture.id='screenImage';img.removeAttribute('id');img=picture;}
  title.textContent=item[1];description.textContent=item[2];notice.textContent='Đang xem '+item[1];
  const buttons=current==='export'?[hotspot('media',1397,8,35,35),hotspot('export',989,949,324,38,()=>showMode('output'))]:common.map(s=>hotspot(...s));
  spots.replaceChildren(...buttons);
  if(writeUrl&&location.hash!=='#'+current)history.replaceState(null,'','#'+current);
  pruneCache();warmNext();
 }catch{
  if(ticket!==revision)return;
  status.hidden=false;
  document.querySelector('#screenError').textContent='Chưa tải được bảng '+item[1]+'. Hình đang xem vẫn được giữ.';
  notice.textContent='Không tải được bảng. Bạn có thể thử lại.';
 }finally{
  if(ticket===revision){clearTimeout(loadingTimer);loading.hidden=true;viewer.setAttribute('aria-busy','false');}
 }
}
function showMode(next){
 if(!['explore','recording','output'].includes(next)||next===mode)return;
 mode=next;clearTimeout(idleTimer);pauseVideos();
 tabs.forEach(button=>{button.setAttribute('aria-selected',String(button.dataset.mode===mode));button.tabIndex=button.dataset.mode===mode?0:-1;});
 for(const id of ['explore','recording','output'])document.getElementById(id).hidden=id!==mode;
 if(mode!=='explore'){
  const video=document.querySelector(mode==='recording'?'#desktopVideo':'#resultVideo');
  if(!video.getAttribute('src')){video.src=video.dataset.src;video.preload='metadata';video.load();}
 }else warmNext();
 notice.textContent=mode==='explore'?'Khám phá các bảng giao diện':mode==='recording'?'Video thao tác thật':'MP4 mẫu đã xuất';
}
select.onchange=()=>showScreen(select.value);
retry.onclick=()=>showScreen(requested);
document.querySelector('#nextScreen').onclick=()=>{const index=screens.findIndex(s=>s[0]===requested);showScreen(screens[(index+1)%screens.length][0]);};
document.querySelector('#guides').onchange=e=>viewer.classList.toggle('guided',e.target.checked);
document.querySelector('#fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else if(viewer.requestFullscreen)await viewer.requestFullscreen();else notice.textContent='Dùng chức năng phóng to của trình duyệt để xem rõ hơn.';}catch{notice.textContent='Không mở được toàn màn hình; dùng chức năng phóng to của trình duyệt.';}};
for(const button of tabs){button.onclick=()=>showMode(button.dataset.mode);button.onkeydown=e=>{if(!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();const i=tabs.indexOf(button);const next=tabs[(i+(e.key==='ArrowRight'?1:tabs.length-1))%tabs.length];next.click();next.focus();};}
window.addEventListener('message',event=>{
 if(event.origin!==location.origin||event.source!==window.parent)return;
 if(event.data?.type==='sceneforge:pause-preview'){active=false;clearTimeout(idleTimer);pauseVideos();}
 if(event.data?.type==='sceneforge:resume-preview'){active=true;warmNext();}
});
document.addEventListener('visibilitychange',()=>{if(document.hidden){clearTimeout(idleTimer);pauseVideos();}else warmNext();});
window.addEventListener('pagehide',pauseVideos);
window.addEventListener('hashchange',()=>showScreen(location.hash.slice(1),false));
showMode('explore');showScreen(location.hash.slice(1)||'media',false);

})();
