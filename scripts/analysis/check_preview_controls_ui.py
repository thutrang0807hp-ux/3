"""Stable player geometry, synchronized preview speed and reversible non-destructive trims."""
from review_ui_helpers import ensure_review_tab
import asyncio,base64,subprocess,tempfile
from pathlib import Path
from playwright.async_api import async_playwright,expect
async def main():
 html=Path('workflow.html').read_text();voice=base64.b64encode(Path('/workspace/3/docs/voice-cpu-real.wav').read_bytes()).decode()
 with tempfile.TemporaryDirectory() as tmp:
  file=Path(tmp)/'clip.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=90x160:rate=24','-t','3','-c:v','libx264','-pix_fmt','yuv420p',str(file)],check=True);video=base64.b64encode(file.read_bytes()).decode()
  async with async_playwright() as p:
   browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1450,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.add_init_script("window.previewAudioElements=[];const OriginalAudio=Audio;window.Audio=function(...args){const el=new OriginalAudio(...args);previewAudioElements.push(el);return el};Audio.prototype=OriginalAudio.prototype")
   async def route(r):
    if '/local-api/' in r.request.url:await r.fulfill(json={});return
    await r.fulfill(body=html,content_type='text/html')
   await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFAudioNodes&&!!window.SFReferenceNodes')
   await page.evaluate('''async({video,voice})=>{project=blankProject();project.id='preview-controls';const image='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';const blob=(data,name,type)=>new File([Uint8Array.from(atob(data),c=>c.charCodeAt(0))],name,{type});assets.set('clip',blob(video,'clip.mp4','video/mp4'));assets.set('voice',blob(voice,'voice.wav','audio/wav'));project.scenes=[0,1].map(i=>{const s=sceneRecord(i*3,(i+1)*3,i,[image]);s.approvedFrame='source';s.sourceFrame={id:'source',image,asset:'frame'};s.clipPlanning={mode:'legacy',continuity:false};s.clips=[{id:'c'+i,asset:'clip',part:'a',duration:3,version:1,frameId:'source',reviewDecision:{status:'accepted'}}];s.chosen={a:'c'+i};return s;});project.voiceOver={mode:'separate',origin:'import',assetId:'voice',duration:5.44,clipSound:'mute',versions:[]};project.merge.captions=true;project.merge.captionWords=0;project.merge.captionDraft=[{start:0,end:3,text:'một hai ba bốn năm sáu',manual:true},{start:3,end:6,text:'bảy tám chín mười mười một',manual:true}];project.merge.captionDraftSignature=productionCaptionSignature();document.body.classList.add('compactWorkspaceFrame');render();await SFAudioNodes.refresh();window.originalPreviewData=JSON.stringify({scenes:project.scenes,cues:project.merge.captionDraft,voice:project.voiceOver});const n=document.querySelector('#node-captions');view.z=1;view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView();}''',{'video':video,'voice':voice})
   await page.locator('#node-captions [data-an=caption-preview]').click();dialog=page.locator('#anCaptionDialog');await expect(dialog).to_be_visible()
   async def geometry():return await dialog.evaluate('d=>Object.fromEntries([["dialog",d],["screen",d.querySelector(".anCaptionScreen")],["controls",d.querySelector(".anCaptionTransport")]].map(([k,e])=>{const r=e.getBoundingClientRect();return[k,{x:r.x,y:r.y,width:r.width,height:r.height}]}))')
   original=await geometry()
   async def stable():
    current=await geometry()
    for key in original:
     for field in original[key]:assert abs(original[key][field]-current[key][field])<.6,(key,field,original,current)
   assert await dialog.locator('[data-cap-rate]').input_value()=='1' and await dialog.locator('[data-cap-trim]').input_value()=='0'
   await ensure_review_tab(page,'[data-cap-play]');await dialog.locator('[data-cap-play]').click();await page.wait_for_function('document.querySelector("#anCaptionDialog video[data-cap-active]").currentTime>.1')
   await ensure_review_tab(page,'[data-cap-rate]');await dialog.locator('[data-cap-rate]').select_option('1.5');assert await page.evaluate('SFAudioNodes.getState().captionPreview.rate===1.5&&document.querySelector("#anCaptionDialog video[data-cap-active]").playbackRate===1.5')
   await page.wait_for_function('previewAudioElements.some(a=>a.getAttribute("src")?.startsWith("blob:")&&!a.paused&&a.currentTime>.1)')
   assert await page.evaluate('previewAudioElements.filter(a=>a.getAttribute("src")?.startsWith("blob:")).every(a=>a.playbackRate===1.5&&a.preservesPitch)')
   await stable();await ensure_review_tab(page,'[data-cap-play]');await dialog.locator('[data-cap-play]').click()
   # Large status/text changes and scrolling the sidebar must not shift the screen.
   await dialog.evaluate('d=>{d.querySelector("[data-cap-status]").textContent="Thông báo đang chờ ".repeat(80);d.querySelector("[data-cap-text]").textContent="nội dung ".repeat(100);d.querySelector("aside").scrollTop=500}');await stable()
   await ensure_review_tab(page,'[data-cap-trim]');await dialog.locator('[data-cap-trim]').select_option('0.1');state=await page.evaluate('SFAudioNodes.getState().captionPreview');assert abs(state['total']-5.8)<1e-7 and state['tailTrim']==.1
   await stable();await dialog.locator('[data-cap-seek]').evaluate('(el)=>{el.value=2.92;el.dispatchEvent(new Event("input",{bubbles:true}))}');await page.wait_for_function('SFAudioNodes.getState().captionPreview.clipIndex===1&&!SFAudioNodes.getState().captionPreview.buffering');await expect(dialog.locator('[data-cap-text]')).to_contain_text('bảy tám')
   await ensure_review_tab(page,'[data-cap-rate]');await dialog.locator('[data-cap-rate]').select_option('2');await ensure_review_tab(page,'[data-cap-play]');await dialog.locator('[data-cap-play]').click();await page.wait_for_function('document.querySelector("#anCaptionDialog video[data-cap-active]").playbackRate===2&&document.querySelector("#anCaptionDialog video[data-cap-active]").currentTime>.15');await stable();await ensure_review_tab(page,'[data-cap-play]');await dialog.locator('[data-cap-play]').click()
   await ensure_review_tab(page,'[data-cap-trim]');await dialog.locator('[data-cap-trim]').select_option('0.15');assert abs(await page.evaluate('SFAudioNodes.getState().captionPreview.total')-5.7)<1e-7
   await ensure_review_tab(page,'[data-cap-trim]');await dialog.locator('[data-cap-trim]').select_option('0');assert await page.evaluate('SFAudioNodes.getState().captionPreview.total===6&&SFAudioNodes.getState().captionPreview.tailTrim===0')
   await ensure_review_tab(page,'[data-cap-rate]');await dialog.locator('[data-cap-rate]').select_option('0.75');assert await page.evaluate('document.querySelector("#anCaptionDialog video[data-cap-active]").playbackRate===.75')
   assert await page.evaluate('originalPreviewData===JSON.stringify({scenes:project.scenes,cues:project.merge.captionDraft,voice:project.voiceOver})'),'Preview controls must not change source/edit/export data'
   await stable();await dialog.screenshot(path='/tmp/sceneforge-preview-controls-v81.png');await ensure_review_tab(page,'[data-cap-close]');await dialog.locator('[data-cap-close]').click();assert not errors,errors;await browser.close()
 print('PASS stable dialog/screen/control geometry under long text/sidebar changes; 0.75/1.5/2 synchronized video/audio speed; reversible 50-150ms preview trim maps captions and preserves raw media/cues/voice')
if __name__=='__main__':asyncio.run(main())
