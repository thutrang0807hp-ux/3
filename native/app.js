(()=>{
'use strict';
if(new URLSearchParams(location.search).get('embedded')==='1'&&window.parent!==window){
 document.body.classList.add('embedded');
}
window.addEventListener('message',event=>{
 if(event.origin!==location.origin||event.source!==window.parent)return;
 if(event.data?.type==='sceneforge:pause-preview')document.querySelectorAll('video').forEach(video=>video.pause());
});
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
const select=document.querySelector('#screen'),img=document.querySelector('#screenImage'),spots=document.querySelector('#hotspots'),viewer=document.querySelector('#viewer'),notice=document.querySelector('#announcement');
let current='media',mode='explore';
for(const [id,title] of screens){const option=document.createElement('option');option.value=id;option.textContent=title;select.append(option);}
const common=[['media',18,42,45,48],['text',65,42,35,48],['stickers',104,42,50,48],['transitions',156,42,69,48],['effects',228,42,49,48],['filters',280,42,42,48],['templates',327,42,65,48],['export',1217,3,78,27],['video-inspector',198,923,79,72],['text-inspector',198,879,79,40],['audio-inspector',198,799,239,72]];
function hotspot(id,left,top,width,height,fn){const button=document.createElement('button');button.className='hotspot';const label=screens.find(s=>s[0]===id)?.[1]||id;button.setAttribute('aria-label',id==='export'&&current==='export'?'Xem MP4 mẫu đã xuất':('Xem '+label));button.dataset.label=label;button.style.cssText=`left:${left/14.4}%;top:${top/10}%;width:${width/14.4}%;height:${height/10}%`;button.onclick=fn||(()=>showScreen(id));spots.append(button);}
function showScreen(id,writeUrl=true){const item=screens.find(s=>s[0]===id)||screens[0];current=item[0];select.value=current;img.src=`./assets/${current}.webp`;img.alt=`Cửa sổ Concat gốc — ${item[1]}`;document.querySelector('#screenTitle').textContent=item[1];document.querySelector('#screenDescription').textContent=item[2];notice.textContent='Đang xem '+item[1];spots.replaceChildren();if(current==='export'){hotspot('media',1397,8,35,35);hotspot('export',989,949,324,38,()=>showMode('output'));}else{common.forEach(s=>hotspot(...s));}if(writeUrl)history.replaceState(null,'',`#${current}`);}
function showMode(next){mode=next;document.querySelectorAll('[data-mode]').forEach(b=>{b.setAttribute('aria-selected',String(b.dataset.mode===mode));b.tabIndex=b.dataset.mode===mode?0:-1;});for(const id of ['explore','recording','output'])document.getElementById(id).hidden=id!==mode;for(const video of document.querySelectorAll('video'))video.pause();notice.textContent=mode==='explore'?'Khám phá các bảng giao diện':mode==='recording'?'Video thao tác thật':'MP4 mẫu đã xuất';}
select.onchange=()=>showScreen(select.value);
document.querySelector('#nextScreen').onclick=()=>{const index=screens.findIndex(s=>s[0]===current);showScreen(screens[(index+1)%screens.length][0]);};
document.querySelector('#guides').onchange=e=>viewer.classList.toggle('guided',e.target.checked);
document.querySelector('#fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else if(viewer.requestFullscreen)await viewer.requestFullscreen();else notice.textContent='Dùng chức năng phóng to của trình duyệt để xem rõ hơn.';}catch{notice.textContent='Không mở được toàn màn hình; dùng chức năng phóng to của trình duyệt.';}};
for(const button of document.querySelectorAll('[data-mode]')){button.onclick=()=>showMode(button.dataset.mode);button.onkeydown=e=>{if(!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();const list=[...document.querySelectorAll('[data-mode]')];const i=list.indexOf(button);const next=list[(i+(e.key==='ArrowRight'?1:list.length-1))%list.length];next.click();next.focus();};}
window.addEventListener('hashchange',()=>showScreen(location.hash.slice(1),false));
showScreen(location.hash.slice(1)||'media',false);
showMode('explore');
})();
