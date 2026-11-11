/* Real-source default and durable source choice; old jobs retain their bound source. */
(()=>{
 const valid=value=>Object.hasOwn(batchSources,value);
 const mount=batchMount;
 batchMount=function(){
  mount();const select=$('#batchEngine');
  // The old option had no value, so its text was treated as an unknown source.
  const simulation=[...select.options].find(o=>o.textContent.includes('Mô phỏng'));if(simulation){simulation.value='simulation';simulation.textContent='Mô phỏng · chỉ thử giao diện';}
  select.closest('label').firstChild.textContent='Nguồn tạo ảnh';
  select.value=valid(batchState.preferredSource)?batchState.preferredSource:'gemini_chat';
  const note=document.createElement('p');note.id='batchSourceScope';note.className='batchHint';note.setAttribute('role','status');select.closest('label').after(note);
  const previous=select.onchange;
  select.onchange=async event=>{const value=select.value;if(!valid(value))return;batchState.preferredSource=value;await batchPersist();await previous?.(event);paintSource();};
  const paintBefore=batchPaint;batchPaint=function(...args){const result=paintBefore(...args);paintSource();return result;};
  // Run existing model/account UI wiring without dispatching image creation.
  previous?.(new Event('change'));paintSource();
 };
 function paintSource(){const select=$('#batchEngine'),note=$('#batchSourceScope');if(!select||!note)return;const source=select.value,sim=source==='simulation';note.textContent=sim?'Chỉ tạo ảnh minh họa mô phỏng, không gửi AI.':'Nguồn cho prompt thêm mới: '+(batchSources[source]||source)+'. Thêm prompt → Chạy lượt → xác nhận gửi.';const old=(typeof batchActiveJobs==='function'?batchActiveJobs():batchState.jobs).filter(j=>j.engine==='simulation'&&j.status==='waiting').length;if(old&&!sim)note.textContent+=' '+old+' việc mô phỏng cũ vẫn giữ nguyên; thêm prompt mới để tạo ảnh thật.';note.dataset.real=String(!sim);}
 const read=batchAccountNow;
 batchAccountNow=async function(){await read();const node=$('#batchAccountNow');if(node&&$('#batchEngine')?.value==='gemini_chat')node.title='Dùng tài khoản Gemini Chat trong Cài đặt; không cần key Gemini API.';};
})();
