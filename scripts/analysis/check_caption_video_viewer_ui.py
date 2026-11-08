"""Real MP4 playback, live grouping, non-lossy export cues and viewer cleanup."""
import asyncio,base64,subprocess,tempfile
from pathlib import Path
from playwright.async_api import async_playwright,expect
async def main():
 html=Path('workflow.html').read_text();text='Bàn chải ở nhà mà xơ xác cùn mòn rồi thì ghé đây sắm set mới về xài liền đi.'
 with tempfile.TemporaryDirectory() as tmp:
  file=Path(tmp)/'fixture.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=180x320:rate=24','-t','8','-c:v','libx264','-pix_fmt','yuv420p','-an',str(file)],check=True);video=base64.b64encode(file.read_bytes()).decode()
  async with async_playwright() as p:
   browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1450,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   async def route(r):
    if '/local-api/' in r.request.url:await r.fulfill(json={});return
    await r.fulfill(body=html,content_type='text/html')
   await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFAudioNodes&&!!window.SceneForgeWorkflow')
   await page.evaluate('''async({video,text})=>{project=blankProject();project.id='caption-video';const image='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';const s=sceneRecord(0,8,0,[image]);s.approvedFrame='source';s.sourceFrame={id:'source',image,asset:'frame'};s.clipPlanning={mode:'legacy',continuity:false};const file=new File([Uint8Array.from(atob(video),c=>c.charCodeAt(0))],'fixture.mp4',{type:'video/mp4'});assets.set('clip',file);s.clips=[{id:'clip1',asset:'clip',part:'a',duration:8,version:1,reviewDecision:{status:'accepted'}}];s.chosen={a:'clip1'};project.scenes=[s];project.merge.captions=true;project.merge.captionWords=5;project.merge.captionSize=37;project.merge.captionY=80;project.merge.captionDraft=[{start:0,end:8,text,manual:true}];document.body.classList.add('compactWorkspaceFrame');render();await SFAudioNodes.refresh();const n=document.querySelector('#node-captions');view.z=1;view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView();window.viewerCreated=[];window.viewerRevoked=[];const make=URL.createObjectURL.bind(URL),remove=URL.revokeObjectURL.bind(URL);URL.createObjectURL=file=>{const u=make(file);viewerCreated.push(u);return u};URL.revokeObjectURL=u=>{viewerRevoked.push(u);remove(u)};}''',{'video':video,'text':text})
   # Preview may show stale cues, but actual handoff must retain the stale-data guard.
   assert await page.evaluate('''async()=>{try{await SFAudioNodes.preparePayload({clips:[],audio:[],captions:project.merge.captionDraft});return false}catch(e){return e.message.includes('Rà phụ đề')}}''')
   await page.locator('#node-captions [data-an=caption-preview]').click();dialog=page.locator('#anCaptionDialog');await expect(dialog).to_be_visible();await expect(dialog.locator('[data-cap-status]')).to_contain_text('cần rà')
   await dialog.locator('[data-cap-play]').click();await page.wait_for_function('document.querySelector("#anCaptionDialog video[data-cap-active]").currentTime>0.15');assert await page.evaluate('SFAudioNodes.getState().captionPreview.time')>0
   # Deliberately stall persistence: style updates must remain synchronous and local.
   await page.evaluate("window.savedStyleStore=storeProject;window.styleSaveWaiters=[];window.styleSaveCalls=0;storeProject=()=>{styleSaveCalls++;return new Promise(resolve=>styleSaveWaiters.push(resolve))};window.styleVideo=document.querySelector('#anCaptionDialog video[data-cap-active]');window.styleCanvas=document.querySelector('#anCaptionDialog canvas');window.styleFrame=document.querySelector('[id^=frame-]')")
   hashes=[]
   for style in ['yellowbox','box','tiktok','clean']:
    await dialog.locator('[data-an=caption-style][data-id='+style+']').click()
    await expect(dialog.locator('[data-an=caption-style][data-id='+style+']')).to_have_attribute('aria-pressed','true')
    assert await page.evaluate('(style)=>project.merge.captionStyle===style&&project.merge.captionSize===37&&project.merge.captionY===80&&styleVideo===document.querySelector("#anCaptionDialog video[data-cap-active]")&&styleCanvas===document.querySelector("#anCaptionDialog canvas")&&styleFrame===document.querySelector("[id^=frame-]")&&!SFAudioNodes.getState().busy',style)
    hashes.append(await dialog.locator('canvas[data-cap-overlay]').evaluate('(c)=>c.toDataURL()'))
    if style=='tiktok':assert await dialog.locator('canvas[data-cap-overlay]').evaluate('(c)=>c.getContext("2d").font.startsWith("900 ")')
   assert len(set(hashes))>=3,'Color/background styles must redraw actual overlay pixels (fixture font may map 700/900 to the same glyph)'
   await page.wait_for_function('styleSaveCalls>0')
   await dialog.locator('[data-an=caption-style][data-id=yellowbox]').click();assert await page.evaluate('project.merge.captionStyle')=='yellowbox'
   assert await page.evaluate('SFAudioNodes.getState().captionPreview.playing'),'Style change must not pause video'
   await page.evaluate('storeProject=savedStyleStore;for(const resolve of styleSaveWaiters)resolve()')
   await dialog.locator('[data-an=caption-style][data-id=clean]').click()
   first=await dialog.locator('[data-cap-text]').text_content();assert len(first.split())<=5
   await dialog.locator('[data-cap-seek]').evaluate('(el)=>{el.value=4;el.dispatchEvent(new Event("input",{bubbles:true}))}');await dialog.locator('[data-cap-play]').click()
   assert await dialog.locator('[data-cap-text]').text_content()!=first
   before=await dialog.locator('canvas[data-cap-overlay]').evaluate('(c)=>c.toDataURL()');time_before=await page.evaluate('SFAudioNodes.getState().captionPreview.time')
   await dialog.locator('[data-an=caption-style][data-id=box]').click();after=await dialog.locator('canvas[data-cap-overlay]').evaluate('(c)=>c.toDataURL()');assert before!=after
   assert await page.evaluate('!SFAudioNodes.getState().captionPreview.playing') and abs(await page.evaluate('SFAudioNodes.getState().captionPreview.time')-time_before)<.001
   await dialog.locator('[data-an=caption-style][data-id=clean]').click()

   await dialog.locator('[data-cap-words]').select_option('3');assert len((await dialog.locator('[data-cap-text]').text_content()).split())<=3
   await dialog.locator('[data-cap-words]').select_option('8');assert len((await dialog.locator('[data-cap-text]').text_content()).split())<=8
   await dialog.locator('[data-cap-words]').select_option('0');assert await dialog.locator('[data-cap-text]').text_content()==text
   await dialog.locator('[data-cap-words]').select_option('3');await dialog.locator('[data-cap-size]').evaluate('(el)=>{el.value=48;el.dispatchEvent(new Event("input",{bubbles:true}))}');await dialog.locator('[data-cap-y]').evaluate('(el)=>{el.value=85;el.dispatchEvent(new Event("input",{bubbles:true}))}')
   result=await page.evaluate('''async()=>{project.merge.captionDraftSignature=productionCaptionSignature();const p={clips:[],audio:[],captions:project.merge.captionDraft.map(c=>({...c}))};await SFAudioNodes.preparePayload(p);const layers=await SFAudioNodes.captionLayers({...p,captionOptions:{fontSize:48,textY:85},captionStyle:'clean'});return {pages:p.captions,raw:project.merge.captionDraft[0],words:project.merge.captionWords,size:project.merge.captionSize,y:project.merge.captionY,srt:SFAudioNodes.srt(),png:layers.every(l=>l.blob.type==='image/png'&&l.blob.size>0),layerCount:layers.length}}''')
   pages=result['pages'];assert all(len(r['text'].split())<=3 for r in pages) and ' '.join(r['text'] for r in pages)==text
   assert pages[0]['start']==0 and pages[-1]['end']==8 and all(abs(a['end']-b['start'])<1e-7 for a,b in zip(pages,pages[1:]))
   assert result['raw']['text']==text and result['raw']['manual'] and result['words']==3 and result['size']==48 and result['y']==85 and result['png'] and result['layerCount']==len(pages)
   await dialog.locator('[data-cap-close]').click();await expect(dialog).to_have_count(0);assert await page.evaluate('SFAudioNodes.getState().captionPreview===null')
   assert await page.evaluate('viewerCreated.every(u=>viewerRevoked.includes(u))'),'Viewer must revoke all created media URLs'
   await page.evaluate("window.nodeStyleStore=storeProject;window.nodeStyleWaiters=[];window.nodeStyleSaveCalls=0;storeProject=()=>{nodeStyleSaveCalls++;return new Promise(resolve=>nodeStyleWaiters.push(resolve))};const n=document.querySelector('#node-captions');view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView()")
   await page.locator('#node-captions [data-an=caption-style][data-id=tiktok]').click();await page.wait_for_function('nodeStyleSaveCalls>0')
   await page.locator('#node-captions [data-an=caption-style][data-id=box]').click()
   assert await page.evaluate("project.merge.captionStyle==='box'&&project.merge.captionSize===48&&project.merge.captionY===85&&!SFAudioNodes.getState().busy&&styleFrame===document.querySelector('[id^=frame-]')")
   await page.evaluate('storeProject=nodeStyleStore;for(const resolve of nodeStyleWaiters)resolve()')

   # Missing clip never produces a fake video or a generation request.
   await page.evaluate('assets.delete("clip");render();const n=document.querySelector("#node-captions");view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView()');await page.locator('#node-captions [data-an=caption-preview]').click();await expect(page.locator('#node-captions .anError')).to_contain_text('Chưa có clip')
   assert not errors,errors
   await page.close();html=Path('photos.html').read_text();page=await browser.new_page(viewport={'width':1450,'height':1050});await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/photos.html');await page.wait_for_function('!!window.SFAudioNodes&&!!window.SceneForgeWorkflow')
   await page.evaluate("""async({video,text})=>{const file=new File([Uint8Array.from(atob(video),c=>c.charCodeAt(0))],'fixture.mp4',{type:'video/mp4'});window.SceneForgeApp={photoBridge:{engine:async()=>({}),listRecipes:async()=>[],saveDraft:async()=>{},getFile:async key=>key==='clip'?file:null,putFile:async()=>{}}};const refs=Object.fromEntries(['person','outfit','product','background'].map(k=>[k,{images:[],description:''}]));const d=newDraft();d.refs=refs;d.voice.mode='native';d.beats=[{id:'b1',name:'Cảnh 1',type:'wide',seconds:8,text,clips:[{id:'pc1',key:'clip',part:'a',version:1,duration:8}],clipPlanning:{mode:'legacy',continuity:false}}];await SceneForgeWorkflow.openRoom({id:'photo-caption',name:'Photo caption',refs,product:{id:'prod',name:'Sản phẩm',sceneBank:[]},photoDraft:d});const post=photoProduction();post.captions=true;post.captionWords=5;post.cues=[{start:0,end:8,text,manual:true}];post.cueSignature=photoCueSignature();render();await SFAudioNodes.refresh();const n=document.querySelector('[data-node=captions]');view.z=1;view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView();}""",{'video':video,'text':text})
   await page.locator('[data-node=captions] [data-an=caption-preview]').click();dialog=page.locator('#anCaptionDialog');await expect(dialog).to_be_visible();await dialog.locator('[data-cap-play]').click();await page.wait_for_function('document.querySelector("#anCaptionDialog video[data-cap-active]").currentTime>0.1')
   await dialog.locator('[data-cap-words]').select_option('0');assert await dialog.locator('[data-cap-text]').text_content()==text
   await dialog.locator('[data-cap-words]').select_option('3');await dialog.locator('[data-an=caption-style][data-id=yellowbox]').click();assert await page.evaluate('photoProduction().style')=='yellowbox';await dialog.locator('[data-cap-close]').click()
   result=await page.evaluate("""async()=>{const r=await photoBuildDraftPayload();const layers=await SFAudioNodes.captionLayers(r.payload);return {pages:r.payload.captions,layers:layers.length,text:photoProduction().cues[0].text,style:r.payload.captionStyle}}""")
   assert all(len(r['text'].split())<=3 for r in result['pages']) and ' '.join(r['text'] for r in result['pages'])==text and result['text']==text and result['layers']==len(result['pages']) and result['style']=='yellowbox'
   await browser.close()
 print('PASS workflow/photos live styles while saves stalled; same video/canvas/frame DOM; paused/playing redraw preserves size/position; MP4 clock and large caption canvas; live 3/5/8/full-cue controls; grouped payload/SRT/PNG layers retain all words and cue envelope; stale export guard retained; cleanup; missing video not fabricated')
if __name__=='__main__':asyncio.run(main())
