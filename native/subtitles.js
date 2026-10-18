(()=>{
'use strict';
const $=selector=>document.querySelector(selector),video=$('#captionVideo'),list=$('#captionCues'),overlay=$('#captionOverlay'),live=$('#captionLive');
const storageKey='sceneforge.subtitle-draft.v1';
const defaults=[{start:0,end:3.6,text:'Một hành trình mới bắt đầu.'},{start:4,end:7.5,text:'Đi chậm lại, ngắm nhìn nhiều hơn.'},{start:8,end:11.8,text:'Và giữ lại những khoảnh khắc đẹp.'}];
const presets={clean:{size:64,color:'FFFFFF',outline:3,border:1,weight:-1,shadow:1},bold:{size:76,color:'45DCFF',outline:4,border:1,weight:-1,shadow:1},box:{size:64,color:'FFFFFF',outline:12,border:3,weight:-1,shadow:0},minimal:{size:54,color:'FFFFFF',outline:0,border:1,weight:0,shadow:2}};
let state={cues:defaults.map(c=>({...c})),preset:'clean',size:64,position:20};
let undo=[],redo=[],active=-1,frame=null,blobUrl=null,pending=null,persistTimer=null,uploadRevision=0;

let samplePromise=null,usingSample=true,selectedCue=null;
const compact=matchMedia('(max-width:700px)');
function setLibrary(open){document.body.classList.toggle('library-collapsed',!open);$('#libraryToggle').setAttribute('aria-expanded',String(open));}
function setInspector(kind,reveal=true){
 if(kind==='clip')selectedCue=null;
 $('#clipInspector').hidden=kind!=='clip';$('#captionInspector').hidden=kind!=='captions';
 $('#captionToolsToggle').setAttribute('aria-expanded',String(kind==='captions'&&reveal));
 document.body.classList.toggle('inspector-open',reveal);
 $('#captionTimelineVideo').classList.toggle('is-selected',kind==='clip');
 if(kind==='captions')$('#captionStylePanel').open=true;
 if(compact.matches&&reveal)setLibrary(false);
 updateTimelineControls();
}
const toolTitles={media:'Tư liệu dự án',text:'Chữ & phụ đề',stickers:'Nhãn dán',transitions:'Chuyển cảnh',effects:'Hiệu ứng',filters:'Bộ lọc màu',templates:'Mẫu chữ',audio:'Âm thanh'};
function selectTool(tool){
 if(!toolTitles[tool])return;
 document.querySelectorAll('[data-tool-panel]').forEach(panel=>panel.hidden=panel.dataset.toolPanel!==tool);
 document.querySelectorAll('[data-workspace-tool]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.workspaceTool===tool)));
 $('#toolPanelTitle').textContent=toolTitles[tool];$('#toolPanelCount').hidden=tool!=='media';
 if(tool==='text')setInspector('captions',!compact.matches);
 setLibrary(true);
}
for(const button of document.querySelectorAll('[data-workspace-tool]'))button.onclick=()=>selectTool(button.dataset.workspaceTool);
$('#inspectSubtitles').onclick=()=>selectTool('text');
$('#closeCaptionInspector').onclick=()=>setInspector('clip',false);
$('#captionMediaCard').onclick=()=>setInspector('clip');
compact.addEventListener('change',()=>{setLibrary(!compact.matches);if(compact.matches)document.body.classList.remove('inspector-open');});
setLibrary(!compact.matches);
function updateMediaProperties(){
 const name=$('#captionSource').textContent;
 $('#workspaceMediaName').textContent=name;$('#clipName').textContent=name;
 $('#workspaceMediaDuration').textContent=(video.duration||12).toFixed(2)+' giây';$('#clipDuration').textContent=(video.duration||12).toFixed(2)+' giây';
 $('#clipDimensions').textContent=(video.videoWidth||540)+' × '+(video.videoHeight||960)+' · 9:16';
 $('#workspaceMediaPoster').hidden=!usingSample;document.querySelector('.media-file-symbol').hidden=usingSample;
}
$('#clipVolume').oninput=event=>{video.volume=Number(event.target.value)/100;};
$('#clipMuted').onchange=event=>{video.muted=event.target.checked;};
video.addEventListener('volumechange',()=>{$('#clipVolume').value=Math.round(video.volume*100);$('#clipVolumeLabel').value=Math.round(video.volume*100)+'%';$('#clipMuted').checked=video.muted;});

async function openSample(force=false){
 if(video.getAttribute('src')&&!force)return;
 const request=++uploadRevision;feedback('Đang mở video mẫu…');
 try{
  if(!samplePromise)samplePromise=fetch(video.dataset.src).then(response=>{if(!response.ok)throw Error();return response.blob();}).catch(error=>{samplePromise=null;throw error;});
  const blob=await samplePromise;if(request!==uploadRevision)return;
  video.pause();if(blobUrl)URL.revokeObjectURL(blobUrl);blobUrl=URL.createObjectURL(blob);video.src=blobUrl;video.preload='auto';video.load();$('#captionSource').textContent='Video mẫu · 9:16';usingSample=true;feedback('Đã mở video mẫu; bản chữ hiện có được giữ nguyên.');
 }catch{if(request===uploadRevision)feedback('Chưa tải được video mẫu. Bấm Video mẫu để thử lại hoặc chọn video trên thiết bị.');}
}
document.addEventListener('sceneforge:open-subtitles',()=>openSample());
$('#captionSampleButton').onclick=()=>openSample(true);


function updateTimelineControls(){
 const cue=selectedCue===null?null:state.cues[selectedCue];
 $('#timelineDelete').disabled=!cue;$('#timelineDuplicate').disabled=!cue;
 $('#timelineSplit').disabled=!cue||video.currentTime<=cue.start+.05||video.currentTime>=cue.end-.05;
}
$('#timelineUndo').onclick=()=>$('#captionUndo').click();
$('#timelineRedo').onclick=()=>$('#captionRedo').click();
$('#timelinePlay').onclick=async()=>{if(!video.paused){video.pause();return;}try{await video.play();}catch{feedback('Chưa phát được video. Kiểm tra tệp đang mở.');}};
video.addEventListener('play',()=>{$('#timelinePlay').textContent='❚❚';});
video.addEventListener('pause',()=>{$('#timelinePlay').textContent='▶';});
$('#timelineFit').onclick=()=>{$('#captionTimelineZoom').value=1;$('#captionTimeline').style.width='100%';$('#captionTimelineScroll').scrollLeft=0;};
$('#timelineDelete').onclick=()=>{if(selectedCue===null||!state.cues[selectedCue])return;const index=selectedCue;selectedCue=null;commit(()=>state.cues.splice(index,1));feedback('Đã xóa câu phụ đề. Video được giữ nguyên.');};
$('#timelineSplit').onclick=()=>{
 const cue=state.cues[selectedCue],time=Math.round(video.currentTime*100)/100;
 if(!cue||time<=cue.start+.05||time>=cue.end-.05){feedback('Chọn một câu phụ đề và đặt con trỏ vào giữa câu để tách.');return;}
 const words=cue.text.trim().split(/\s+/),part=Math.max(1,Math.min(words.length-1,Math.round(words.length*(time-cue.start)/(cue.end-cue.start))));
 const left=words.slice(0,part).join(' '),right=words.slice(part).join(' ')||cue.text;
 const index=selectedCue;commit(()=>state.cues.splice(index,1,{start:cue.start,end:time,text:left},{start:time,end:cue.end,text:right}));feedback('Đã tách phụ đề tại '+clock(time)+'. Có thể sửa lại chữ của hai đoạn.');
};
$('#timelineDuplicate').onclick=()=>{
 const cue=state.cues[selectedCue];if(!cue)return;
 const next=state.cues[selectedCue+1],end=cue.end+(cue.end-cue.start);
 if(end>(next?.start??timelineDuration())+.0005){feedback('Chưa đủ khoảng trống sau câu này để nhân đôi; hãy chỉnh thời gian trước.');return;}
 commit(()=>state.cues.splice(selectedCue+1,0,{...cue,start:cue.end,end}));feedback('Đã nhân đôi câu vào khoảng trống kế tiếp.');
};

function snapshot(){return JSON.stringify(state);}
function feedback(message){$('#captionFeedback').textContent=message;}
function validate(cues=state.cues){
 if(!cues.length)return {message:'Thêm ít nhất một câu phụ đề.',index:-1};
 if(cues.length>500)return {message:'Tối đa 500 câu trong bản thử này.',index:-1};
 for(let i=0;i<cues.length;i++){
  const c=cues[i];
  if(!Number.isFinite(c.start)||!Number.isFinite(c.end)||c.start<0||c.end<=c.start)return {message:`Câu ${i+1}: thời gian kết thúc phải lớn hơn bắt đầu.`,index:i};
  if(!c.text.trim())return {message:`Câu ${i+1}: cần nhập nội dung.`,index:i};
  if(c.text.length>1000)return {message:`Câu ${i+1}: tối đa 1.000 ký tự.`,index:i};
  if(i&&c.start<cues[i-1].end-.0005)return {message:`Câu ${i+1} đang chồng thời gian với câu trước.`,index:i};
  if(Number.isFinite(video.duration)&&c.end>video.duration+.05)return {message:`Câu ${i+1} vượt quá thời lượng video (${video.duration.toFixed(2)} giây).`,index:i};
 }
 return null;
}
function updateButtons(){
 $('#captionUndo').disabled=!undo.length;$('#captionRedo').disabled=!redo.length;$('#timelineUndo').disabled=!undo.length;$('#timelineRedo').disabled=!redo.length;updateTimelineControls();
 const error=validate();$('#captionExportSrt').disabled=!!error;$('#captionExportAss').disabled=!!error;
 list.querySelectorAll('.sub-cue').forEach((row,i)=>row.classList.toggle('is-invalid',error?.index===i));
 return error;
}
function save(){
 clearTimeout(persistTimer);if(state.cues.length&&validate())return;
 persistTimer=setTimeout(()=>{try{localStorage.setItem(storageKey,snapshot());$('#captionSaveState').textContent='Đã lưu bản chữ trên trình duyệt này.';}catch{$('#captionSaveState').textContent='Không lưu được bản chữ; hãy tải SRT hoặc ASS.';}},300);
}
function remember(before){if(before===snapshot())return;undo.push(before);if(undo.length>50)undo.shift();redo=[];updateButtons();save();}
function commit(change,redraw=true){const before=snapshot();change();remember(before);if(redraw)render();else{applyStyle();updateButtons();sync();}}
function restoreSaved(){
 try{
  const value=JSON.parse(localStorage.getItem(storageKey));
  if(!value||!Array.isArray(value.cues)||value.cues.length>500||!presets[value.preset]||!Number.isFinite(value.size)||value.size<36||value.size>96||![20,45,75].includes(value.position))return;
  if(value.cues.some(c=>!c||typeof c.text!=='string'||!Number.isFinite(c.start)||!Number.isFinite(c.end)))return;
  if(!value.cues.length||!validate(value.cues))state=value;
 }catch{}
}
function applyStyle(){
 overlay.className='caption-overlay preset-'+state.preset;overlay.style.fontSize=(state.size/10.8)+'cqw';overlay.style.bottom=state.position+'%';
 document.querySelectorAll('[data-caption-preset]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.captionPreset===state.preset)));
 $('#captionSize').value=state.size;$('#captionSizeLabel').value=state.size;$('#captionPosition').value=String(state.position);
}
function clock(seconds){const ms=Math.max(0,Math.round(seconds*100));return String(Math.floor(ms/6000)).padStart(2,'0')+':'+String(Math.floor(ms/100)%60).padStart(2,'0')+'.'+String(ms%100).padStart(2,'0');}
function timelineDuration(){return Number.isFinite(video.duration)&&video.duration>0?video.duration:12;}
function seekCue(index){selectedCue=index;setInspector('captions');const cue=state.cues[index];if(!cue||!Number.isFinite(cue.start))return;video.pause();video.currentTime=cue.start;sync();const row=list.children[index];if(row){list.scrollTop=row.offsetTop-list.firstElementChild.offsetTop;row.querySelector('textarea')?.focus({preventScroll:true});}}
function renderTimeline(){
 const duration=timelineDuration(),ruler=$('#captionRuler'),track=$('#captionSubtitleTrack');ruler.replaceChildren();track.replaceChildren();
 const step=duration<=20?2:Math.ceil(duration/8);
 for(let t=0;t<duration;t+=step){const label=document.createElement('span');label.style.left=t/duration*100+'%';label.textContent=clock(t);ruler.append(label);}
 state.cues.forEach((cue,index)=>{if(!Number.isFinite(cue.start)||!Number.isFinite(cue.end)||cue.end<=cue.start)return;const button=document.createElement('button');button.textContent=cue.text;button.dataset.cue=index;button.setAttribute('aria-label','Phụ đề câu '+(index+1)+': '+cue.text);button.style.left=Math.max(0,Math.min(100,cue.start/duration*100))+'%';button.style.width=Math.max(0,Math.min(duration,cue.end)-Math.max(0,cue.start))/duration*100+'%';button.onclick=()=>seekCue(index);track.append(button);});
 $('#captionTimelineVideo').textContent=$('#captionSource').textContent;
 ruler.setAttribute('role','slider');ruler.tabIndex=0;ruler.setAttribute('aria-valuemin','0');ruler.setAttribute('aria-valuemax',String(duration));
}
$('#captionRuler').onclick=event=>{const rect=event.currentTarget.getBoundingClientRect();video.currentTime=Math.max(0,Math.min(timelineDuration(),(event.clientX-rect.left)/rect.width*timelineDuration()));sync();};
$('#captionRuler').onkeydown=event=>{let time=video.currentTime;if(event.key==='ArrowLeft')time-=.1;else if(event.key==='ArrowRight')time+=.1;else if(event.key==='Home')time=0;else if(event.key==='End')time=timelineDuration();else return;event.preventDefault();video.currentTime=Math.max(0,Math.min(timelineDuration(),time));sync();};
$('#captionTimelineVideo').onclick=()=>setInspector('clip');
$('#captionTimelineZoom').oninput=event=>{$('#captionTimeline').style.width=Number(event.target.value)*100+'%';};
function sync(){
 updateTimelineControls();
 const t=video.currentTime||0;$('#captionPlayhead').style.left=Math.min(100,t/timelineDuration()*100)+'%';$('#captionRuler').setAttribute('aria-valuenow',String(t));$('#captionClock').textContent=clock(t);
 const index=state.cues.findIndex(c=>Number.isFinite(c.start)&&t>=c.start&&t<c.end);
 if(index!==active){if(active>=0)list.children[active]?.classList.remove('is-current');if(index>=0)list.children[index]?.classList.add('is-current');active=index;$('#captionSubtitleTrack').querySelectorAll('[data-cue]').forEach(button=>button.classList.toggle('is-current',Number(button.dataset.cue)===index));}
 const text=index>=0?state.cues[index].text:'';
 if(live.textContent!==text)live.textContent=text;
 overlay.hidden=!text;
}
function stopFrames(){if(frame!==null){if(video.cancelVideoFrameCallback)video.cancelVideoFrameCallback(frame);else cancelAnimationFrame(frame);frame=null;}}
function tick(){frame=null;sync();if(!video.paused&&!video.ended&&!document.hidden)frame=video.requestVideoFrameCallback?video.requestVideoFrameCallback(tick):requestAnimationFrame(tick);}
function render(){
 applyStyle();list.replaceChildren();active=-1;
 state.cues.forEach((cue,index)=>{
  const row=document.createElement('div');row.className='sub-cue';row.dataset.index=index;
  const seek=document.createElement('button');seek.className='cue-seek';seek.textContent=String(index+1).padStart(2,'0');seek.setAttribute('aria-label','Xem câu '+(index+1));seek.onclick=()=>seekCue(index);
  const body=document.createElement('div');body.className='cue-body';
  const text=document.createElement('textarea');text.value=cue.text;text.maxLength=1000;text.dataset.field='text';text.setAttribute('aria-label','Nội dung câu '+(index+1));
  const times=document.createElement('div');times.className='cue-times';
  for(const [field,label] of [['start','Bắt đầu'],['end','Kết thúc']]){
   const holder=document.createElement('label');holder.append(label);
   const input=document.createElement('input');input.type='number';input.min='0';input.step='0.01';input.value=Number.isFinite(cue[field])?cue[field]:'';input.dataset.field=field;input.setAttribute('aria-label',label+' câu '+(index+1));holder.append(input);times.append(holder);
  }
  body.append(text,times);
  const remove=document.createElement('button');remove.className='cue-delete';remove.textContent='×';remove.setAttribute('aria-label','Xóa câu '+(index+1));remove.onclick=()=>commit(()=>state.cues.splice(index,1));
  row.append(seek,body,remove);list.append(row);
 });
 $('#captionCount').textContent=state.cues.length;renderTimeline();updateButtons();sync();
}
list.addEventListener('focusin',event=>{if(event.target.dataset.field){pending=snapshot();selectedCue=Number(event.target.closest('[data-index]').dataset.index);updateTimelineControls();}});
list.addEventListener('input',event=>{
 const field=event.target.dataset.field;if(!field)return;
 const cue=state.cues[Number(event.target.closest('[data-index]').dataset.index)];
 cue[field]=field==='text'?event.target.value:(event.target.value===''?null:Number(event.target.value));
 renderTimeline();active=-1;sync();const error=updateButtons();feedback(error?.message||'');
});
list.addEventListener('change',event=>{if(!event.target.dataset.field)return;if(pending)remember(pending);pending=snapshot();});
$('#captionUndo').onclick=()=>{if(!undo.length)return;redo.push(snapshot());state=JSON.parse(undo.pop());render();save();feedback('Đã hoàn tác.');};
$('#captionRedo').onclick=()=>{if(!redo.length)return;undo.push(snapshot());state=JSON.parse(redo.pop());render();save();feedback('Đã làm lại.');};
$('#captionAdd').onclick=()=>{
 if(state.cues.length>=500){feedback('Tối đa 500 câu trong bản thử này.');return;}
 if(state.cues.length&&validate()){feedback('Sửa thời gian và nội dung chưa hợp lệ trước khi thêm câu.');return;}
 const start=Math.round((video.currentTime||0)*100)/100;
 if(state.cues.some(c=>start>=c.start&&start<c.end)){feedback('Vị trí này đã có phụ đề. Tua đến khoảng trống rồi thêm câu.');return;}
 const next=state.cues.find(c=>c.start>start);const end=Math.min(start+2,next?.start??Infinity,Number.isFinite(video.duration)?video.duration:Infinity);
 if(end-start<.1){feedback('Không đủ khoảng trống để thêm câu ở đây.');return;}
 commit(()=>{state.cues.push({start,end,text:'Nhập phụ đề của bạn'});state.cues.sort((a,b)=>a.start-b.start);});feedback('Đã thêm câu tại '+clock(start)+'.');
};
for(const button of document.querySelectorAll('[data-caption-preset]'))button.onclick=()=>commit(()=>{state.preset=button.dataset.captionPreset;state.size=presets[state.preset].size;},false);
$('#captionSize').oninput=event=>{overlay.style.fontSize=(Number(event.target.value)/10.8)+'cqw';$('#captionSizeLabel').value=event.target.value;};
$('#captionSize').onchange=event=>commit(()=>{state.size=Number(event.target.value);},false);
$('#captionPosition').onchange=event=>commit(()=>{state.position=Number(event.target.value);},false);
function parseTime(raw){
 const match=raw.trim().match(/^(?:(\d{1,3}):)?(\d{2}):(\d{2})[.,](\d{3})$/);
 if(!match||Number(match[2])>59||Number(match[3])>59)throw Error('Mốc thời gian không hợp lệ. Dùng HH:MM:SS,mmm hoặc MM:SS.mmm.');
 return Number(match[1]||0)*3600+Number(match[2])*60+Number(match[3])+Number(match[4])/1000;
}
function parseSubtitles(source){
 const text=source.replace(/^\uFEFF/,'').replace(/\r\n?/g,'\n').trim();
 const vtt=/^WEBVTT(?:\s|$)/.test(text);const blocks=text.split(/\n[ \t]*\n/);const cues=[];
 for(const block of blocks){
  const lines=block.split('\n');if(vtt&&/^(WEBVTT|NOTE(?:\s|$)|STYLE(?:\s|$)|REGION(?:\s|$))/.test(lines[0]))continue;
  let index=lines.findIndex(line=>line.includes('-->'));
  if(index<0)throw Error('Có đoạn không có mốc thời gian hợp lệ. Tệp cũ được giữ nguyên.');
  if(index>1)throw Error('Cấu trúc phụ đề không hợp lệ.');
  const timing=lines[index].match(/^\s*(\S+)\s+-->\s+(\S+)(?:\s+.*)?$/);if(!timing)throw Error('Mốc thời gian không hợp lệ.');
  const content=lines.slice(index+1).join('\n').replace(/<[^>]*>/g,'').trim();
  cues.push({start:parseTime(timing[1]),end:parseTime(timing[2]),text:content});
 }
 cues.sort((a,b)=>a.start-b.start);const error=validate(cues);if(error)throw Error(error.message);return cues;
}
$('#captionImportButton').onclick=()=>$('#captionTextFile').click();
$('#captionTextFile').onchange=async event=>{
 const file=event.target.files[0];event.target.value='';if(!file)return;
 if(file.size>1024*1024){feedback('Tệp phụ đề tối đa 1 MB.');return;}
 try{const cues=parseSubtitles(await file.text());setInspector('captions');commit(()=>{state.cues=cues;});feedback('Đã nhập '+cues.length+' câu. Có thể hoàn tác để lấy lại bản trước.');}catch(error){feedback(error.message);}
};
$('#captionUploadButton').onclick=()=>$('#captionVideoFile').click();
$('#captionVideoFile').onchange=async event=>{
 const file=event.target.files[0];event.target.value='';if(!file)return;
 if(file.size>500*1024*1024){feedback('Video tối đa 500 MB.');return;}
 const request=++uploadRevision,url=URL.createObjectURL(file),probe=document.createElement('video');probe.preload='metadata';
 let timeout;
 try{
  const ready=new Promise((resolve,reject)=>{probe.onloadedmetadata=resolve;probe.onerror=()=>reject(Error('Trình duyệt không đọc được video này. Thử MP4 H.264.'));timeout=setTimeout(()=>reject(Error('Chưa đọc được thông tin video. Hãy thử tệp MP4 khác.')),15000);});probe.src=url;await ready;
  if(request!==uploadRevision){URL.revokeObjectURL(url);return;}
  if(!probe.videoWidth||Math.abs(probe.videoWidth/probe.videoHeight-9/16)>.02)throw Error('Chọn video dọc 9:16 để giữ bố cục phụ đề.');
  if(!Number.isFinite(probe.duration)||probe.duration>600)throw Error('Video phải có thời lượng tối đa 10 phút.');
  video.pause();if(blobUrl)URL.revokeObjectURL(blobUrl);blobUrl=url;video.src=url;video.load();$('#captionSource').textContent=file.name;usingSample=false;
  feedback('Đã mở video trên thiết bị. Bản chữ hiện có vẫn được giữ; nhập SRT/VTT tương ứng hoặc sửa lại từng câu.');
 }catch(error){URL.revokeObjectURL(url);feedback(error.message);}
 finally{clearTimeout(timeout);probe.removeAttribute('src');probe.load();}
};
function srtTime(value){const ms=Math.round(value*1000);return String(Math.floor(ms/3600000)).padStart(2,'0')+':'+String(Math.floor(ms/60000)%60).padStart(2,'0')+':'+String(Math.floor(ms/1000)%60).padStart(2,'0')+','+String(ms%1000).padStart(3,'0');}
function assTime(value){const cs=Math.round(value*100);return Math.floor(cs/360000)+':'+String(Math.floor(cs/6000)%60).padStart(2,'0')+':'+String(Math.floor(cs/100)%60).padStart(2,'0')+'.'+String(cs%100).padStart(2,'0');}
function download(text,extension){const url=URL.createObjectURL(new Blob(['\uFEFF'+text],{type:'text/plain;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='sceneforge-phu-de.'+extension;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('#captionExportSrt').onclick=()=>{const error=validate();if(error){feedback(error.message);return;}download(state.cues.map((c,i)=>`${i+1}\n${srtTime(c.start)} --> ${srtTime(c.end)}\n${c.text.trim()}\n`).join('\n'),'srt');feedback('Đã tải SRT. Kiểu chữ nằm trong tệp ASS, không nằm trong SRT.');};
$('#captionExportAss').onclick=()=>{
 const error=validate();if(error){feedback(error.message);return;}
 const p=presets[state.preset];
 const header=`[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,${state.size},&H00${p.color},&H00FFFFFF,&H00101010,&H40101010,${p.weight},0,0,0,100,100,0,0,${p.border},${p.outline},${p.shadow},2,76,76,${Math.round(1920*state.position/100)},1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n`;
 const body=state.cues.map(c=>'Dialogue: 0,'+assTime(c.start)+','+assTime(c.end)+',Default,,0,0,0,,'+c.text.trim().replace(/\\/g,'＼').replace(/{/g,'｛').replace(/}/g,'｝').replace(/\n/g,'\\N')).join('\n');
 download(header+body+'\n','ass');feedback('Đã tải ASS với kiểu chữ. Đây chưa phải MP4 đã gắn phụ đề.');
};
video.addEventListener('play',()=>{stopFrames();tick();});video.addEventListener('pause',()=>{stopFrames();sync();});video.addEventListener('ended',stopFrames);
for(const name of ['timeupdate','seeked','loadedmetadata'])video.addEventListener(name,()=>{sync();if(name==='loadedmetadata'){updateMediaProperties();renderTimeline();active=-1;sync();const error=updateButtons();if(error)feedback(error.message);}});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopFrames();});
window.addEventListener('pagehide',event=>{stopFrames();clearTimeout(persistTimer);if(!validate())try{localStorage.setItem(storageKey,snapshot());}catch{};if(blobUrl&&!event.persisted)URL.revokeObjectURL(blobUrl);});
restoreSaved();render();
setInspector(new URLSearchParams(location.search).get('tool')==='subtitles'?'captions':'clip',new URLSearchParams(location.search).get('tool')==='subtitles');
openSample();
})();
