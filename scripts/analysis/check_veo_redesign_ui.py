"""Real workflow and Chromium; intercepted CLI endpoints, no Google calls."""
import asyncio,base64,io,json,subprocess,tempfile,sys
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright,expect

async def main():
 html=Path('workflow.html').read_text();errors=[];posts=[];records={};submit_mode='done';short_tail='--short-tail' in sys.argv
 image=io.BytesIO();Image.new('RGB',(90,160),'#35636c').save(image,format='PNG');data='data:image/png;base64,'+base64.b64encode(image.getvalue()).decode()
 with tempfile.TemporaryDirectory() as tmp:
  video=Path(tmp)/'fixture.mp4'
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=teal:s=90x160:r='+('24' if short_tail else '8'),'-t','7.90' if short_tail else '8','-c:v','libx264','-pix_fmt','yuv420p','-y',str(video)],check=True)
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
   page=await browser.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
   async def route(r):
    url=r.request.url
    if '/local-api/flow/simple/files/' in url:await r.fulfill(body=video.read_bytes(),content_type='video/mp4');return
    if url.endswith('/local-api/flow/simple/jobs') and r.request.method=='POST':
     body=r.request.post_data_json;posts.append((url,body));rid=body['request_id'];records[rid]={'request_id':rid,'state':submit_mode,'result':{'room_id':body['room_id'],'scene_id':body['scene_id'],'part':body['part'],'mime_type':'video/mp4','settings':body['settings']}};await r.fulfill(json={'request_id':rid,'state':'submitted'});return
    if '/local-api/flow/simple/diagnostics/' in url:
     rid=url.split('/diagnostics/',1)[1].split('?',1)[0];record=records.get(rid)
     await r.fulfill(json={'code':'found','request_id':rid,'current_store_id':record.get('store_id') if record else 'fixture-store','record':record});return
    if '/local-api/flow/simple/jobs/' in url:
     rid=url.rsplit('/',1)[1];await r.fulfill(json=records.get(rid,{'request_id':rid,'state':'missing'}));return
    if '/local-api/' in url:
     if r.request.method=='POST':posts.append((url,r.request.post_data_json))
     await r.fulfill(json={'enabled':True,'native_pipeline':True,'selection':{'available':True,'token':'token','account_id':'fixture'},'unresolved':[]});return
    await r.fulfill(content_type='text/html',body=html)
   await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFVeoNode')
   await page.evaluate('''async image=>{
project=blankProject();project.id='node-ui';project.source={poster:image,asset:'source'};project.analysis.frameQualityRequired=false;
assets.set('frame',new File([await(await fetch(image)).blob()],'frame.png',{type:'image/png'}));
project.scenes=Array.from({length:9},(_,i)=>sceneRecord(i*8,(i+1)*8,i,[image]));
for(const s of project.scenes){s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',asset:'frame',image};s.approvedFrame='source';s.frameSelectionId='source';s.videoPromptOverrides={a:'A gentle movement.'};}
await storeProject();render();await SFVeoNode.refresh();
}''',data)
   # Tiles, grouping, detail, editing does not submit.
   await page.locator('#node-videos').screenshot(path='/tmp/veo-v58-grid.png')
   await expect(page.locator('#node-videos .vnTile')).to_have_count(9)
   assert await page.locator('#node-videos [data-vn=show-settings]').count()==0
   assert await page.locator('#node-videos [data-vn-advanced-body] > *').count()==0
   assert await page.locator('#sfFlowSettingsDock').count()==1
   await page.evaluate("document.querySelector('#node-videos .vnTile').click()")
   await expect(page.locator('#vnDetail')).to_be_visible()
   await page.locator('#vnDetail [data-vn-prompt]').fill('A slow turn toward the camera.')
   await page.wait_for_timeout(350)
   assert not posts,'Editing must not submit'
   await page.locator('#vnDetail [data-vn=next]').click()
   await expect(page.locator('#vnDetail [data-vn-prompt]')).to_be_enabled()
   await page.locator('#vnDetail [data-vn=prev]').click()
   await expect(page.locator('#vnDetail [data-vn-prompt]')).to_have_value('A slow turn toward the camera.')
   await expect(page.locator('#vnDetail [data-vn-prompt]')).to_be_enabled()
   await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled()
   await page.locator('#modal [data-action=close-modal]').first.click()
   # Real receive + actual video metadata; pending -> imported with zero approval clicks.
   job=await page.evaluate('''async()=>{const row=SFVeoNode.slots()[0];const job={id:'flow-ui-fixture',provider:'flow',kind:'video',sceneId:row.s.id,part:row.p.id,settings:{kind:'video',mode:'ingredients',ratio:'9:16',model:'lite',outputs:1},signature:await directSignature(row.s,row.p.id,'video'),prompt:makePrompt(row.s,row.p),state:'submitted',at:Date.now(),veoNodeVersion:43};project.cloudJobs=[job];await storeProject();render();return job;}''')
   records[job['id']]={'request_id':job['id'],'state':'running','message':'Flow đang tạo video','phase':'generating','provider_task':{'media_id':'22222222-2222-4222-8222-222222222222','state':'generating'}}
   await page.evaluate("SFVeoNode.sync('flow-ui-fixture')")
   assert await page.evaluate("""async()=>{const image=document.querySelector('#node-videos .vnTile img'),save=storeProject;let writes=0;storeProject=async()=>{writes++;return save();};try{await SFVeoNode.sync('flow-ui-fixture');await SFVeoNode.sync('flow-ui-fixture');return writes===0&&image===document.querySelector('#node-videos .vnTile img');}finally{storeProject=save;}}""")
   await page.evaluate("document.querySelector('#node-videos .vnTile').click()")
   await expect(page.locator('#vnDetail [data-vn-generation] progress')).to_have_attribute('value','60')
   await expect(page.locator('#vnDetail [data-vn-generation]')).to_contain_text('Ước tính theo bước')
   # A pre-CLI failure must release disabled controls and replace stale running labels.
   records[job['id']]={'request_id':job['id'],'state':'failed','message':'Không tìm thấy GFlow gốc. Chưa gọi CLI.','submitted':False}
   await page.evaluate("SFVeoNode.sync('flow-ui-fixture')")
   await expect(page.locator('#vnDetail [data-vn-generation]')).to_contain_text('Không tìm thấy GFlow gốc')
   await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled()
   await expect(page.locator('#vnDetail [data-vn=write]')).to_be_enabled()
   assert 'Đang tạo' not in await page.locator('#vnDetail .vnDetailPlayer').inner_text()
   await page.evaluate("window.handoffFrameNode=document.querySelector('#node-frames');window.handoffVeoNode=document.querySelector('#node-videos');project.merge.ndTransferred={signature:SFReferenceNodes.snapshot(),at:Date.now()};window.handoffMessages=[];const send=window.postMessage.bind(window);window.postMessage=(data,...rest)=>{handoffMessages.push(data);return send(data,...rest)}")
   records[job['id']]={'request_id':job['id'],'state':'done','result':{'room_id':'node-ui','scene_id':job['sceneId'],'part':job['part'],'mime_type':'video/mp4','settings':job['settings']}}
   await page.evaluate("SFVeoNode.sync('flow-ui-fixture')")
   await expect(page.locator('#vnDetail video')).to_have_count(1)
   await expect(page.locator('#vnDetail [data-vn-generation] progress')).to_have_attribute('value','100')
   state=await page.evaluate("({job:project.cloudJobs[0],clip:project.scenes[0].clips[0],chosen:project.scenes[0].chosen})")
   assert state['job']['state']=='imported' and state['clip']['autoReceivedAt'] and state['chosen']['a']==state['clip']['id']
   assert not state['clip'].get('reviewDecision'),'Receiving is not quality approval'
   await expect(page.locator('#node-merge > header span')).to_have_text('1/9 clip')
   await expect(page.locator('#node-merge .ndClipStrip em').first).to_have_text('✓')
   await expect(page.locator('#node-merge [data-nd=handoff]')).to_contain_text('1/9')
   assert await page.evaluate("handoffFrameNode===document.querySelector('#node-frames')&&handoffVeoNode===document.querySelector('#node-videos')")
   assert await page.evaluate('readyCount()')==0,'Receiving must not silently approve quality'
   await expect(page.locator('#node-merge .ndNew')).to_contain_text('Có lựa chọn clip mới')
   assert await page.evaluate("handoffMessages.every(m=>m?.type!=='sceneforge:workflow-open-editor')"),'Receiving must not overwrite an existing editor timeline'
   assert await page.evaluate("SFReferenceNodes.refreshHandoff('other-room')===false"),'Foreign-room refresh must be ignored'

   # Re-reading an imported job also repairs stale handoff UI, without choosing another version.
   await page.evaluate("document.querySelector('#node-merge > header span').textContent='STALE HANDOFF'")

   # Repeated reads never duplicate import.
   await page.evaluate("SFVeoNode.sync('flow-ui-fixture')")
   assert await page.evaluate('project.scenes[0].clips.length')==1
   await expect(page.locator('#node-merge > header span')).to_have_text('1/9 clip')
   if short_tail:
    assert 7.85<=state['clip']['duration']<8,'Fixture must reproduce a 7.9-second source'
    assert await page.evaluate('''(()=>{const r=SFVeoNode.slots()[0],c=r.s.clips[0];return !clipTimingInfo({...c,duration:7.849},r.p).ok&&clipTimingInfo({...c,duration:7.85},r.p).ok&&!clipTimingInfo({...c,duration:7.9,requestId:''},r.p).ok&&!clipTimingInfo({...c,duration:'7.9'},r.p).ok})()''')

    result=await page.evaluate('''async()=>{const row=SFVeoNode.slots()[0],c=row.s.clips[0],cases=[['frameId','wrong-frame','Ảnh đầu'],['prompt','wrong-prompt','Prompt'],['slotStart',row.p.start+.1,'Mốc cảnh'],['duration',7.7,'7.700s'],['tail','','7.'],['origin','imported','7.'],['sourceIn',.1,'7.']];const messages=[];for(const [key,value,expected]of cases){const had=Object.hasOwn(c,key),previous=c[key];try{c[key]=value;try{await SFVeoNode.acceptClip(row);throw Error('BAD ACCEPT '+key);}catch(e){if(!e.message.includes('Cảnh 1')||!e.message.includes(expected))throw e;messages.push(e.message);}}finally{if(had)c[key]=previous;else delete c[key];}}return {messages,approved:!!c.reviewDecision,ready:readyCount(),duration:c.duration};}''')
    assert len(result['messages'])==7 and not result['approved'] and result['ready']==0
   # Human approval still works; other scenes untouched.
   await page.locator('#vnDetail [data-vn=accept]').click()
   await expect(page.locator('#vnDetail [data-vn=accept]')).to_have_text('Đã duyệt')
   assert await page.evaluate("project.scenes[0].clips[0].reviewDecision.status")=='accepted'
   assert await page.evaluate('readyCount()')==1
   if short_tail:
    assert await page.evaluate('''(()=>{const c=project.scenes[0].clips[0];return c.duration<8&&c.timingAdjustment.kind==='codec-tail-hold'&&c.timingAdjustment.seconds>0&&c.timingAdjustment.seconds<=.15&&!!c.tail})()''')

   assert await page.evaluate("handoffFrameNode===document.querySelector('#node-frames')")
   await expect(page.locator('#runBar')).to_contain_text('1/9 cảnh đã duyệt')
   await page.locator('#modal [data-action=close-modal]').first.click()
   await page.evaluate("document.querySelector('#node-videos [data-vn=filter-review]').click()")
   await expect(page.locator('#node-videos .vnTile')).to_have_count(0)
   # Unknown/missing has no raw missing text / 100% nor successful badge.
   await page.evaluate("project.cloudJobs[0].state='missing';project.cloudJobs[0].phaseMessage='missing';render()")
   await expect(page.locator('#node-videos .vnTile')).to_have_count(1)
   await page.evaluate("document.querySelector('#node-videos .vnTile').click()")
   assert 'missing' not in await page.locator('#vnDetail [data-vn-generation]').inner_text()
   assert await page.locator('#vnDetail [data-vn-generation] progress').count()==0
   assert not posts,posts
   # Full actual create path: queue uses two original API requests, one per scene.
   await page.locator('#modal [data-action=close-modal]').first.click()
   await page.evaluate('''async()=>{project.scenes=project.scenes.slice(0,3);project.cloudJobs[0].state='imported';project.cloudJobs[0].phaseMessage='';project.veoNode=undefined;delete project.scenes[1].videoPromptOverrides;window.queuePromptCalls=0;SFPromptPipeline.rewriteVideo=async(s,p)=>{queuePromptCalls++;s.videoPromptOverrides??={};s.videoPromptOverrides[p.id]='A queue-generated movement.';};await storeProject();render();await SFVeoNode.refresh();}''')
   await page.evaluate("document.querySelector('#node-videos [data-vn=filter-review]').click()")
   await expect(page.locator('#node-videos .vnTile')).to_have_count(0)
   await expect(page.locator('#node-videos [data-vn=create-ready]')).to_contain_text('Tạo toàn bộ 2')
   await page.evaluate("()=>{window.canvasRenders=0;window.canvasRenderStacks=[];window.beforeQueueRender=render;render=function(...args){canvasRenders++;canvasRenderStacks.push(new Error().stack);return beforeQueueRender(...args);};}")
   dialog_handler=lambda d:d.accept()
   page.on('dialog',dialog_handler)
   await page.evaluate("document.querySelector('#node-videos [data-vn=create-ready]').click()")
   await page.wait_for_function("project.cloudJobs.some(j=>j.state==='submitted')")
   await page.evaluate('pollWorkflowResults()')
   await page.wait_for_function("project.cloudJobs.length===3&&project.cloudJobs.every(j=>j.state==='imported')",timeout=15000)
   assert len(posts)==2,posts
   assert await page.evaluate('canvasRenders')==0,await page.evaluate('canvasRenderStacks')
   await page.evaluate('()=>{render=beforeQueueRender;}')
   assert await page.evaluate('queuePromptCalls')==1
   assert await page.evaluate('project.scenes[0].clips.length')==1
   assert all(p[1]['settings']['outputs']==1 for p in posts)
   await page.wait_for_function("!document.querySelector('#node-videos [data-vn=cancel-queue]')")
   # Uncertain first job stops the rest, without any replay.
   submit_mode='unknown';posts.clear()
   await page.evaluate('''async()=>{for(const s of project.scenes){s.clips=[];s.chosen={};s.receivedClipIds=[];}project.cloudJobs=[];await storeProject();render();await SFVeoNode.refresh();}''')
   await page.evaluate("document.querySelector('#node-videos [data-vn=create-ready]').click()")
   await page.wait_for_function("project.cloudJobs.length===1&&project.cloudJobs[0].state==='unknown'",timeout=10000)
   await page.wait_for_function("!document.querySelector('#node-videos [data-vn=cancel-queue]')")
   assert len(posts)==1,posts
   # Continuity keeps its quality gate: no second command until part a is approved.
   submit_mode='done';posts.clear()
   await page.evaluate('''async image=>{const s=sceneRecord(0,16,0,[image]);s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',asset:'frame',image};s.approvedFrame='source';s.frameSelectionId='source';s.clipPlanning={mode:'legacy',continuity:true};s.videoPromptOverrides={a:'Move gently.',b:'Continue the movement.'};project.scenes=[s];project.cloudJobs=[];project.veoNode=undefined;await storeProject();render();await SFVeoNode.refresh();}''',data)
   await page.evaluate("document.querySelector('#node-videos [data-vn=create-ready]').click()")
   await page.wait_for_function("project.cloudJobs.length===1&&project.cloudJobs[0].state==='imported'",timeout=10000)
   await expect(page.locator('#node-videos')).to_contain_text('Đợi duyệt phần trước')
   assert len(posts)==1
   await page.evaluate("SFVeoNode.acceptClip(SFVeoNode.slots()[0])")
   await page.wait_for_function("project.cloudJobs.length===2&&project.cloudJobs.every(j=>j.state==='imported')",timeout=15000)
   assert len(posts)==2,posts
   await page.wait_for_function("!document.querySelector('#node-videos [data-vn=cancel-queue]')")
   # Old room receipts must not permanently disable the new Create button.
   posts.clear()
   old=await page.evaluate('''async image=>{const s=sceneRecord(0,4.2,0,[image]);s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',asset:'frame',image};s.approvedFrame='source';s.frameSelectionId='source';s.videoPromptOverrides={a:'Move gently.'};project.scenes=[s];const old={id:'flow-old-unsubmitted',provider:'flow',kind:'video',sceneId:s.id,part:'a',state:'unknown',veoNodeVersion:42,store_id:'fixture-store'};project.cloudJobs=[old];project.veoNode=undefined;await storeProject();render();await SFVeoNode.refresh();return old;}''',data)
   records[old['id']]={'request_id':old['id'],'store_id':'fixture-store','state':'failed','submitted':False,'native_inputs':{'room_id':'node-ui','scene_id':old['sceneId'],'part':'a'}}
   await page.evaluate('SFVeoNode.openClipDetail(SFVeoNode.slots()[0])')
   await page.wait_for_function("project.cloudJobs[0].state==='failed'")
   await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled()
   assert not posts,'Receipt inspection must never submit'
   assert await page.evaluate('!!project.cloudJobs[0].legacyNegativeReceipt')
   # Truly unknown history stays recorded; cancelling confirmation sends nothing.
   unknown_id='flow-old-unknown-case'
   records[unknown_id]={'request_id':unknown_id,'store_id':'fixture-store','state':'unknown','submitted':None}
   records['flow-old-wrong-scene']={'request_id':'flow-old-wrong-scene','store_id':'fixture-store','state':'failed','submitted':False,'native_inputs':{'room_id':'node-ui','scene_id':'different-scene','part':'a'}}
   await page.evaluate("()=>{project.cloudJobs.push({...project.cloudJobs[0],id:'flow-old-unknown-case',state:'unknown'},{...project.cloudJobs[0],id:'flow-old-wrong-scene',state:'unknown'});SFVeoNode.openClipDetail(SFVeoNode.slots()[0]);}")
   await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled()
   await expect(page.locator('#vnDetail [data-vn=create]')).to_contain_text('Kiểm tra lượt cũ')
   page.remove_listener('dialog',dialog_handler)
   dismiss_handler=lambda d:d.dismiss();page.on('dialog',dismiss_handler)
   await page.locator('#vnDetail [data-vn=create]').click()
   await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled()
   assert not posts and await page.evaluate("project.cloudJobs[1].state")=='unknown'
   assert await page.evaluate("project.cloudJobs[2].state")=='unknown','Receipt for another scene must not auto-unlock'
   # Explicit acknowledgement unlocks one NEW request without deleting old history.
   page.remove_listener('dialog',dismiss_handler);page.on('dialog',dialog_handler)
   await page.locator('#vnDetail [data-vn=review-legacy]').click()
   await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled()
   await page.wait_for_function("!!project.veoNode.reviewedLegacy['flow-old-unknown-case']")
   assert not posts
   await page.locator('#vnDetail [data-vn=create]').click()
   await page.wait_for_function("project.cloudJobs.some(j=>j.veoNodeVersion===43&&j.state==='imported')",timeout=10000)
   assert len(posts)==1 and posts[0][1]['request_id'] not in (old['id'],unknown_id),posts
   assert await page.evaluate("project.cloudJobs.filter(j=>j.veoNodeVersion===42).length")==3
   assert not errors,errors
   await page.screenshot(path='/tmp/veo-v58-detail.png',full_page=False)
   await browser.close()
 print(('SHORT-TAIL ' if short_tail else '')+'PASS Veo receive/idempotent reread refresh assembly without full render, auto-approval or editor overwrite; real node tiles/filter/detail/edit; live stage estimate; automatic file import + 100%; idempotency; separate approval; missing not presented as success; stable images/no writes on unchanged polls; all-missing queue prepares prompt despite filter and skips completed clips; stop on uncertainty; legacy negative receipts auto-unlock, unknown confirmation cancel sends nothing, acknowledgement permits one new request; local intercepted generation only')
if __name__=='__main__':asyncio.run(main())
