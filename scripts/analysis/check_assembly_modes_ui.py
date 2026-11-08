"""Automatic playback stays local; manual mode transfers library placement explicitly."""
import asyncio,base64,subprocess,tempfile
from pathlib import Path
from playwright.async_api import async_playwright,expect
async def main():
 html=Path('workflow.html').read_text();posts=[]
 with tempfile.TemporaryDirectory() as tmp:
  file=Path(tmp)/'clip.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=90x160:rate=24','-t','8','-c:v','libx264','-pix_fmt','yuv420p',str(file)],check=True);data=base64.b64encode(file.read_bytes()).decode()
  async with async_playwright() as p:
   b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':1450,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   async def route(r):
    if '/local-api/' in r.request.url:
     if r.request.method=='POST':posts.append(r.request.url)
     await r.fulfill(json={});return
    await r.fulfill(body=html,content_type='text/html')
   await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference&room=assembly-mode');await page.wait_for_function('!!window.SFAudioNodes&&!!window.SFReferenceNodes&&!!window.SceneForgeWorkflow.flushRoom')
   await page.evaluate('''async data=>{project=blankProject();project.id='assembly-mode';const image='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';const file=new File([Uint8Array.from(atob(data),c=>c.charCodeAt(0))],'clip.mp4',{type:'video/mp4'});project.scenes=[0,1].map(i=>{const s=sceneRecord(i*8,(i+1)*8,i,[image]);s.approvedFrame='source';s.sourceFrame={id:'source',image,asset:'frame'};s.clipPlanning={mode:'legacy',continuity:false};s.clips=[{id:'c'+i,asset:'f'+i,part:'a',duration:8,version:1,frameId:'source',reviewDecision:{status:'accepted'}}];s.chosen={a:'c'+i};s.receivedClipIds=['c'+i];assets.set('f'+i,file);return s;});project.merge.ndInclude={voice:true,music:false,captions:false};project.merge.captions=true;project.merge.captionDraft=[{start:0,end:8,text:'Cảnh thứ nhất'},{start:8,end:16,text:'Cảnh thứ hai'}];project.merge.captionDraftSignature=productionCaptionSignature();project.merge.ndTransferred={signature:'prior-editor',at:1234};window.editorTransfers=[];const send=window.postMessage.bind(window);window.postMessage=(data,...args)=>{if(data.type==='sceneforge:workflow-open-editor')editorTransfers.push(data.payload);return send(data,...args)};document.body.classList.add('compactWorkspaceFrame');render();await SFAudioNodes.refresh();window.assemblyFrame=document.querySelector('#node-frames');}''',data)
   merge=page.locator('#node-merge')
   async def focus():await page.evaluate("()=>{const n=document.querySelector('#node-merge');view.z=1;view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView();}")
   await focus();await expect(merge.locator('[data-nd=assembly-play]')).to_be_enabled();await merge.locator('[data-nd=assembly-play]').click();dialog=page.locator('#anCaptionDialog');await expect(dialog).to_be_visible();await expect(dialog.locator('header b')).to_have_text('Bản ghép tự động')
   await page.wait_for_function('document.querySelector("#anCaptionDialog video").currentTime>0.1&&SFAudioNodes.getState().captionPreview.playing')
   assert await dialog.locator('[data-cap-text]').text_content()==''
   first=await dialog.locator('video').get_attribute('src');await dialog.locator('[data-cap-seek]').evaluate('(el)=>{el.value=8.2;el.dispatchEvent(new Event("input",{bubbles:true}))}');await page.wait_for_function('(src)=>document.querySelector("#anCaptionDialog video").src!==src',arg=first)
   assert await page.evaluate('editorTransfers.length===0&&project.merge.ndTransferred.at===1234'),'Play must not overwrite/open Dựng'
   await dialog.locator('[data-cap-close]').click();await focus();await merge.locator('[data-nd-include=captions]').check();await merge.locator('[data-nd=assembly-play]').click();await expect(dialog).to_be_visible();await expect(dialog.locator('[data-cap-text]')).to_contain_text('Cảnh thứ nhất');await dialog.locator('[data-cap-close]').click()
   # Switching to manual while automatic preparation is delayed cancels the late viewer.
   await page.evaluate('window.originalAssemblyPlay=SFAudioNodes.playAssembly;window.assemblyDelayDone=false;SFAudioNodes.playAssembly=async guard=>{await new Promise(resolve=>window.releaseAssemblyDelay=resolve);try{return await originalAssemblyPlay(guard)}finally{assemblyDelayDone=true}};void 0')
   await focus();await merge.locator('[data-nd=assembly-play]').click();await page.wait_for_function('typeof releaseAssemblyDelay==="function"');await expect(merge.locator('[data-nd=assembly-play]')).to_be_disabled()
   await merge.locator('[data-nd=placement][data-id=library]').click();await page.evaluate('releaseAssemblyDelay()');await page.wait_for_function('assemblyDelayDone');await expect(dialog).to_have_count(0);await page.evaluate('SFAudioNodes.playAssembly=originalAssemblyPlay;void 0')
   await expect(merge.locator('[data-nd=handoff]')).to_contain_text('tự ghép');assert await merge.locator('[data-nd=assembly-play]').count()==0
   assert await page.evaluate("assemblyFrame===document.querySelector('#node-frames')")
   await merge.locator('[data-nd=handoff]').click();await page.wait_for_function('editorTransfers.length===1')
   result=await page.evaluate('({placement:editorTransfers[0].placement,clips:editorTransfers[0].clips.length,captions:editorTransfers[0].captions.length,replace:editorTransfers[0].replaceSlots})')
   assert result['placement']=='library' and result['clips']==2 and result['captions']>=2 and not result['replace'],result
   await focus();await merge.locator('[data-nd=placement][data-id=assembled]').click();await merge.locator('[data-nd=handoff]').click();await page.wait_for_function('editorTransfers.length===2');assert await page.evaluate("editorTransfers[1].placement==='assembled'")
   # Missing file stays an explicit gap during play; no automatic generation.
   await page.evaluate("assets.delete('f1');SFReferenceNodes.refreshHandoff(project.id)");await focus();await expect(merge.locator('[data-nd=assembly-play]')).to_contain_text('1/2');await merge.locator('[data-nd=assembly-play]').click();await expect(dialog).to_be_visible();await expect(dialog.locator('[data-cap-status]')).to_contain_text('thiếu 1');await dialog.locator('[data-cap-close]').click()
   assert not posts,posts;assert not errors,errors;await b.close()
 print('PASS two assembly paths: auto opens/plays both real clips locally and honors caption toggle, no editor mutation; manual sends library placement; optional assembled handoff retained; partial gaps explicit; no generation; frame DOM retained')
if __name__=='__main__':asyncio.run(main())
