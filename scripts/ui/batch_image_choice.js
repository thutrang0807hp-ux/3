/* One visible source+model choice; existing durable job bindings stay unchanged. */
(()=>{
 const mount=batchMount;batchMount=function(...args){mount(...args);
  const engine=$('#batchEngine'),model=$('#batchImageModel');engine.closest('label').hidden=true;model.closest('label').hidden=true;
  const label=document.createElement('label');label.textContent='Tạo ảnh bằng';const select=document.createElement('select');select.id='batchImageChoice';label.append(select);engine.closest('label').before(label);
  const catalog=new Map();let last=engine.value,pending=null;
  const names={gemini_chat:'Gemini Chat · tài khoản trong Cài đặt',gemini:'Gemini API · key riêng',flow:'Flow · tài khoản trong Cài đặt',meta:'Meta AI',grok:'Grok Chat',chatgpt:'ChatGPT',simulation:'Mô phỏng · không gửi AI'};
  const specific=s=>['gemini','flow'].includes(s);
  function paint(){const selected=JSON.stringify([engine.value,specific(engine.value)?model.value:'']);const options=[];for(const [source,name]of Object.entries(names)){const models=catalog.get(source)||[];if(specific(source)&&models.length)for(const id of models)options.push(new Option(name+' · '+id,JSON.stringify([source,id])));else options.push(new Option(name+(specific(source)?' · đọc model để chọn':''),JSON.stringify([source,''])));}select.replaceChildren(...options);if([...select.options].some(o=>o.value===selected))select.value=selected;else select.value=JSON.stringify([engine.value,'']);}
  function fill(){const list=catalog.get(engine.value)||[];model.replaceChildren(...(list.length?list.map(n=>new Option(n,n)):[new Option('Chưa đọc danh sách model','')]));}
  const change=engine.onchange;engine.onchange=async function(e){if(engine.value!==last){last=engine.value;fill();}await change?.call(this,e);paint();};
  select.onchange=()=>{const [source,id]=JSON.parse(select.value);if(engine.value!==source){engine.value=source;pending=id;engine.dispatchEvent(new Event('change',{bubbles:true}));}if(id&&[...model.options].some(o=>o.value===id)){model.value=id;pending=null;}paint();};
  $('#batchCheckModels').onclick=async()=>{const button=$('#batchCheckModels'),source=engine.value;if(!specific(source))return;button.disabled=true;try{const status=source==='flow'?await engineRequest('flow/models',{}):await batchImageAPI('/models',{});const list=(status.models||[]).filter(n=>typeof n==='string'&&/^[A-Za-z0-9._:-]+$/.test(n)&&(source!=='flow'||/image|imagen|flux|banana/i.test(n)&&!n.startsWith('veo-')));catalog.set(source,list);if(engine.value===source){fill();if(pending&&list.includes(pending))model.value=pending;pending=null;$('#batchProviderHint').textContent='Đã đọc '+list.length+' model. Chọn nguồn và model trong ô Tạo ảnh bằng; chưa gửi tạo ảnh.';paint();}}catch(e){if(engine.value===source)$('#batchProviderHint').textContent=e.message;}finally{button.disabled=false;}};
  paint();
 };
})();
