"""Real browser fixture: reference bytes/order, image-only anchor, clothing rules and guards."""
import threading,http.server,functools
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('!!window.SFFrameIdentity&&!!window.SFPromptPipeline')
  result=page.evaluate('''async()=>{
    const check=(v,m)=>{if(!v)throw Error(m)};window.savedCount=0;storeProject=async()=>{savedCount++};
    const canvas=document.createElement('canvas');canvas.width=16;canvas.height=16;const ctx=canvas.getContext('2d');ctx.fillStyle='red';ctx.fillRect(0,0,16,16);const source=canvas.toDataURL('image/png');ctx.fillStyle='blue';ctx.fillRect(0,0,16,16);const anchorFile=await new Promise(r=>canvas.toBlob(r,'image/png'));
    project=blankProject();project.id='frame-identity-test';project.refs.person={images:[{id:'p',image:source,name:'person.png'}],description:'Person A'};project.refs.product={images:[{id:'o',image:source,name:'product.png'}],description:'Product A'};
    const a=sceneRecord(0,8,0,[source]),b=sceneRecord(8,16,1,[source]);a.refsUsed=b.refsUsed=['person','product'];a.frames=[{id:'approved',asset:'anchor',image:source,version:1,status:'approved'}];a.approvedFrame='approved';b.frames=[{id:'b-approved',asset:'b-frame',image:source,version:1,status:'approved'}];b.approvedFrame='b-approved';assets.set('anchor',anchorFile);assets.set('b-frame',anchorFile);project.scenes=[a,b];render();
    check(!!document.querySelector('[data-frame-anchor]'),'settings UI missing');
    const original=SFPromptPipeline.snapshot(b,'image');document.querySelector('[data-frame-outfit]').value='person';document.querySelector('[data-frame-outfit]').dispatchEvent(new Event('change',{bubbles:true}));await new Promise(r=>setTimeout(r,40));
    const select=document.querySelector('[data-frame-anchor]');select.value=JSON.stringify([a.id,'approved']);select.dispatchEvent(new Event('change',{bubbles:true}));await new Promise(r=>setTimeout(r,40));
    check(a.approvedFrame==='approved'&&b.approvedFrame==='b-approved','existing approvals lost');check(a.frames[0].pinned,'anchor not protected from version pruning');
    const packed=await SFPromptPipeline.pack(b,'image');check(packed.references.length===4&&packed.bindings.length===4,'reference order/count mismatch');check(packed.bindings[3].role==='appearance'&&packed.bindings[3].code==='R4','anchor binding wrong');
    const expected=await cpuEncode(anchorFile);check(packed.references[3].data===expected,'actual anchor bytes not sent');check(packed.prompt.includes('Clothing as well as face/hair'),'clothing rule missing');check(SFPromptPipeline.snapshot(b,'image')!==original,'settings did not invalidate image prompt');
    const prompt=imageFramePrompt(b);check(prompt.includes('R4 is an approved generated appearance'),'final generation prompt missing anchor');const clean=SFPromptContract.sceneText(prompt);check(!clean.includes('FRAME IDENTITY RULES'),'manual prompt would accumulate obsolete rules');
    const direct=await directRefs(b);check(direct[3].data===expected,'direct dispatch differs from writing dispatch');
    const part=clipParts(b)[0];b.frameSelectionId='b-approved';const video=await SFPromptPipeline.generationRefs(b,part,false);check(video.length===1,'anchor leaked into video');
    assets.delete('anchor');let missing=false;try{await SFPromptPipeline.pack(b,'image')}catch(e){missing=e.message.includes('khung chuẩn')}check(missing,'missing anchor file not blocked');assets.set('anchor',anchorFile);
    project.refs.outfit={description:'explicit outfit',images:[{id:'outfit',image:source}]};b.refsUsed=['person','product','outfit'];const outfit=await SFPromptPipeline.pack(b,'image');check(outfit.prompt.includes('Clothing comes from the connected outfit'),'explicit outfit did not override person');
    project.refs.person.images[0].name='changed-image.png';let stale=false;try{await SFPromptPipeline.pack(b,'image')}catch(e){stale=e.message.includes('đã đổi')}check(stale,'stale reference anchor not blocked');render();check(!!document.querySelector('[data-frame-anchor]'),'stale anchor prevents correcting settings');
    return {references:packed.references.length,videoReferences:video.length,approvalsPreserved:true,actualAnchorBytes:true,savedCount};
  }''')
  assert not errors,errors
  print('PASS',result);browser.close()
finally:server.shutdown()
