/* Keep the video-settings slot useful in the photo branch as well. */
(()=>{
 const nav=document.querySelector('.roomBar>nav');if(!nav)return;
 const button=document.createElement('button');button.id='branchVideoSettings';button.hidden=true;button.textContent='⚙ Cấu hình video';button.title='Mở cấu hình video của nhánh từ ảnh';nav.append(button);
 button.onclick=async()=>{if(switching||changingWorkflow)return;try{await wsAPI()?.openVideoSettings?.();}catch(e){fail(e);}};
 const paint=wsPaint;wsPaint=function(...args){const result=paint(...args);button.hidden=currentView!=='analysis'||currentRoom?.mode!=='photos';button.disabled=switching||changingWorkflow||!wsAPI()?.openVideoSettings;return result;};
})();
