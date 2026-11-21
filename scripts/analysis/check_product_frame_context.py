"""Actual workflow: current product/script enter frame prompt and generation refs."""
import threading,http.server,functools
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('window.SFPromptPipeline&&window.SFProductScript')
  result=page.evaluate('''async()=>{
   const check=(v,m)=>{if(!v)throw Error(m)};
   const canvas=document.createElement('canvas');canvas.width=16;canvas.height=16;const ctx=canvas.getContext('2d');ctx.fillStyle='red';ctx.fillRect(0,0,16,16);const source=canvas.toDataURL();ctx.fillStyle='blue';ctx.fillRect(0,0,16,16);const product=canvas.toDataURL();
   project=blankProject();project.id='current-product-frames';project.source={asset:'source'};project.script=[{id:'line',start:0,end:4,original:'OLD BRAND',newText:'Sáp mới của tôi cho xe'}];
   const s=sceneRecord(0,4,0,[source]);s.refsUsed=[];s.hasProduct=true;s.visual={en:{product:'OLD BRAND blue jar',composition:'Hand holding OLD BRAND'},vi:{product:'lọ mẫu'}};s.promptFrame={vi:'Giữ nhãn OLD BRAND',en:'Keep OLD BRAND'};project.scenes=[s];
   project.refs.product={description:'Sáp của tôi',images:[{id:'actual-product',image:product}]};SFProductScript.setProduct({id:'new',name:'Sáp của tôi',refs:{product:{description:'Hương gỗ, dùng trong xe'}}});
   check(refsFor(s).includes('product'),'replacement not connected');const first=SFPromptPipeline.snapshot(s,'image');
   const packed=await SFPromptPipeline.pack(s,'image');check(packed.bindings[1].role==='product'&&packed.bindings[1].replace,'missing product binding');check(packed.references.length===2,'wrong attached image count');check(packed.references[1].data===product.split(',')[1],'replacement bytes not attached');
   const data=JSON.parse(packed.prompt.split('SCENE DATA:\\n')[1].split('\\nFRAME IDENTITY RULES')[0]);check(data.product_adaptation.product.name==='Sáp của tôi','new product missing');check(data.product_adaptation.selected_script[0].text==='Sáp mới của tôi cho xe','new speech missing');check(!data.observed_geometry.en.product,'old product detail retained');check(packed.prompt.includes('original product brand, label, claims'),'source-brand restriction missing');
   check(!imageFramePrompt(s).includes('Keep OLD BRAND'),'stale fallback displayed');
   const records=SFPromptPipeline.records().records;records[s.id+':image:']={template:SFPromptContract.version,input:first,applied:true,job:{state:'applied'},result:{promptFrame:{vi:'Sáp mới từ R2',en:'Current product from R2'}}};check(SFPromptPipeline.current(s,'image'),'fresh prompt rejected');check(imageFramePrompt(s).includes('Current product from R2'),'fresh prompt not used');
   project.script[0].newText='Lời mới đã sửa';check(!SFPromptPipeline.current(s,'image'),'script edit kept old prompt current');check(!SFPromptPipeline.reviewText(s,'image').includes('Sáp mới từ R2'),'stale Vietnamese shown as current');
   const second=SFPromptPipeline.snapshot(s,'image');SFProductScript.brief().facts='Thông tin đổi';check(second!==SFPromptPipeline.snapshot(s,'image'),'product facts edit missed');
   project.refs.product.images=[];let blocked=false;try{await SFPromptPipeline.pack(s,'image')}catch(e){blocked=e.message.includes('thêm ảnh sản phẩm')}check(blocked,'missing replacement fell back to source');
   project.refs.product.images=[{id:'actual-product',image:product}];records[s.id+':image:'].input=SFPromptPipeline.snapshot(s,'image');s.approvedFrame='old-source';window.framePosts=[];storeProject=async()=>{};
   workflowLocalRequest=async(path,body)=>{if(path==='gemini-chat/status')return {installed:true,selection:{available:true,token:'selected'}};if(path==='gemini-chat/jobs'){framePosts.push(body);throw Error('fixture-stop-after-dispatch');}throw Error('Unexpected '+path);};
   let dispatched=false;try{await SFPromptPipeline.runImages([s])}catch(e){dispatched=e.message==='fixture-stop-after-dispatch'}check(dispatched&&framePosts.length===1,'approved stale source silently skipped new frame');check(framePosts[0].kind==='image'&&framePosts[0].references[1].data===product.split(',')[1],'image generation missing product reference');check(framePosts[0].prompt.includes('Current product from R2')&&!framePosts[0].prompt.includes('Keep OLD BRAND'),'wrong image prompt dispatched');
   return {newScript:true,newProduct:true,actualReferenceBytes:true,staleBlocked:true,actualImageDispatch:true};
  }''');assert not errors,errors;print('PASS',result);browser.close()
finally:server.shutdown()
