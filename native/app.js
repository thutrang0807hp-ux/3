(()=>{
'use strict';
if(window.parent!==window)document.body.classList.add('embedded');
const pause=()=>document.querySelectorAll('video').forEach(video=>video.pause());
window.addEventListener('message',event=>{if(event.origin!==location.origin||event.source!==window.parent)return;if(event.data?.type==='sceneforge:pause-preview')pause();});
document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});
window.addEventListener('pagehide',pause);
document.querySelector('#workspaceFullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.querySelector('#viewer').requestFullscreen();}catch{document.querySelector('#announcement').textContent='Không mở được toàn màn hình trên trình duyệt này.';}};
})();
