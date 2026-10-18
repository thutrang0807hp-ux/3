(()=>{
'use strict';
const $=s=>document.querySelector(s),video=$('#captionVideo');
let filter='none';
const filters={none:'',warm:'sepia(.25) saturate(1.15)',cool:'hue-rotate(15deg) saturate(.85)',mono:'grayscale(1)'};
function apply(){video.style.filter=`${filters[filter]} brightness(${Number($('#effectBrightness').value)/100}) contrast(${Number($('#effectContrast').value)/100}) blur(${$('#effectBlur').value}px)`;}
for(const input of ['effectBrightness','effectContrast','effectBlur'])$('#'+input).oninput=apply;
$('#resetPreviewEffects').onclick=()=>{$('#effectBrightness').value=100;$('#effectContrast').value=100;$('#effectBlur').value=0;apply();};
for(const button of document.querySelectorAll('[data-preview-filter]'))button.onclick=()=>{filter=button.dataset.previewFilter;document.querySelectorAll('[data-preview-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));apply();};
for(const button of document.querySelectorAll('[data-sticker]'))button.onclick=()=>{$('#previewSticker').textContent=button.dataset.sticker;$('#previewSticker').hidden=!button.dataset.sticker;};
for(const [id,property] of [['stickerX','left'],['stickerY','top']])$('#'+id).oninput=e=>{$('#previewSticker').style[property]=e.target.value+'%';};
for(const button of document.querySelectorAll('[data-transition-demo]'))button.onclick=()=>{
 const kind=button.dataset.transitionDemo;
 const frames=kind==='fade'?[{opacity:0},{opacity:1}]:kind==='slide'?[{transform:'translateX(100%)',opacity:.2},{transform:'translateX(0)',opacity:1}]:[{transform:'scale(1.15)',opacity:0},{transform:'scale(1)',opacity:1}];
 video.getAnimations().forEach(animation=>animation.cancel());video.animate(frames,{duration:matchMedia('(prefers-reduced-motion:reduce)').matches?0:600,easing:'ease-out'});
 $('#captionFeedback').textContent='Đang xem mẫu chuyển cảnh; chưa áp dụng vào điểm ghép giữa nhiều clip.';
};
for(const button of document.querySelectorAll('[data-caption-template]'))button.onclick=()=>{document.querySelector(`[data-caption-preset="${button.dataset.captionTemplate}"]`).click();$('#inspectSubtitles').click();};
$('#toolAudioVolume').oninput=e=>{video.volume=Number(e.target.value)/100;};
$('#toolAudioMuted').onchange=e=>{video.muted=e.target.checked;};
$('#toolPlaybackRate').onchange=e=>{video.playbackRate=Number(e.target.value);};
video.addEventListener('volumechange',()=>{$('#toolAudioVolume').value=Math.round(video.volume*100);$('#toolAudioMuted').checked=video.muted;});
})();
