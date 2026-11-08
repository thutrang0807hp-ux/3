"""Sample composited browser pixels across real clip joins, including delayed decoding."""
import asyncio,base64,io,subprocess,tempfile
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright,expect
async def main():
 html=Path('workflow.html').read_text();posts=[]
 with tempfile.TemporaryDirectory() as tmp:
  clips=[]
  for color in ['red','blue','lime']:
   file=Path(tmp)/(color+'.mp4');subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i',f'color=c={color}:size=90x160:rate=24','-t','2','-c:v','libx264','-pix_fmt','yuv420p',str(file)],check=True);clips.append(base64.b64encode(file.read_bytes()).decode())
  async with async_playwright() as p:
   browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1450,'height':1050})
   async def route(r):
    if '/local-api/' in r.request.url:
     if r.request.method=='POST':posts.append(r.request.url)
     await r.fulfill(json={});return
    await r.fulfill(body=html,content_type='text/html')
   await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFAudioNodes&&!!window.SFReferenceNodes')
   await page.evaluate('''async clips=>{project=blankProject();project.id='join-test';const image='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';project.scenes=clips.map((raw,i)=>{const s=sceneRecord(i*2,(i+1)*2,i,[image]);s.approvedFrame='source';s.sourceFrame={id:'source',image,asset:'frame'};s.clipPlanning={mode:'legacy',continuity:false};assets.set('clip'+i,new File([Uint8Array.from(atob(raw),c=>c.charCodeAt(0))],'clip'+i+'.mp4',{type:'video/mp4'}));s.clips=[{id:'c'+i,asset:'clip'+i,part:'a',duration:2,version:1,frameId:'source',reviewDecision:{status:'accepted'}}];s.chosen={a:'c'+i};s.receivedClipIds=['c'+i];return s;});project.merge.ndInclude={voice:true,music:false,captions:false};document.body.classList.add('compactWorkspaceFrame');render();await SFAudioNodes.refresh();const n=document.querySelector('#node-merge');view.z=1;view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView();window.holdBlue=true;const descriptor=Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype,'readyState');Object.defineProperty(HTMLMediaElement.prototype,'readyState',{configurable:true,get(){if(this.dataset.capClip==='1'&&holdBlue)return 0;return descriptor.get.call(this)}});}''',clips)
   merge=page.locator('#node-merge')
   # Mode labels use available width instead of wrapping into a narrow text column.
   for key in ['library','assembled']:
    bounds=await merge.locator('[data-nd=placement][data-id='+key+'] .ndModeCopy b').bounding_box();assert bounds['width']>150 and bounds['height']<45,bounds
   await merge.screenshot(path='/tmp/sceneforge-assembly-node-v80.png')
   await merge.locator('[data-nd=assembly-play]').click();dialog=page.locator('#anCaptionDialog');await expect(dialog).to_be_visible();await page.wait_for_function('document.querySelector("#anCaptionDialog video[data-cap-active]").currentTime>0.1')
   assert await dialog.locator('video').count()==2,'Keep exactly two decoders, not all clips'
   screen=await dialog.locator('.anCaptionScreen').bounding_box();clip={'x':screen['x']+screen['width']/2-3,'y':screen['y']+screen['height']/2-3,'width':6,'height':6}
   async def pixel():
    raw=await page.screenshot(clip=clip);im=Image.open(io.BytesIO(raw)).convert('RGB');values=[im.getpixel((x,y)) for y in range(im.height) for x in range(im.width)];return tuple(sum(p[c] for p in values)/len(values) for c in range(3))
   await page.wait_for_function('document.querySelector("#anCaptionDialog .anJoinFreeze").hidden');red=await pixel();assert red[0]>180 and red[1]<50 and red[2]<50,red
   await page.wait_for_function('SFAudioNodes.getState().captionPreview.clipIndex===1&&SFAudioNodes.getState().captionPreview.buffering')
   start=await page.evaluate('SFAudioNodes.getState().captionPreview.time');await page.wait_for_timeout(350)
   assert abs(await page.evaluate('SFAudioNodes.getState().captionPreview.time')-start)<.01,'Timeline must pause while next decoder is waiting'
   held=await pixel();assert held[0]>180 and held[2]<50,held
   assert await page.evaluate('document.querySelector("#anCaptionDialog .anJoinFreeze").hidden===false')
   assert await page.evaluate('[...document.querySelectorAll("#anCaptionDialog video")].every(v=>v.paused||v.muted)'),'No clip audio runs ahead while buffering'
   await page.evaluate('holdBlue=false');await page.wait_for_function('SFAudioNodes.getState().captionPreview.clipIndex===1&&!SFAudioNodes.getState().captionPreview.buffering&&document.querySelector("#anCaptionDialog video[data-cap-active]").currentTime>0.1')
   await page.wait_for_function('document.querySelector("#anCaptionDialog .anJoinFreeze").hidden');blue=await pixel();assert blue[2]>180 and blue[0]<50,blue
   await page.wait_for_function('SFAudioNodes.getState().captionPreview.time>3.75')
   samples=[]
   for _ in range(18):
    rgb=await pixel();samples.append(rgb);assert max(rgb)>150,('Black join frame',rgb)
   await page.wait_for_function('SFAudioNodes.getState().captionPreview.clipIndex===2&&!SFAudioNodes.getState().captionPreview.buffering')
   green=await pixel();assert green[1]>180 and green[0]<50 and green[2]<50,green
   # Seek back and preserve a decoded frame while the new target is prepared.
   await dialog.locator('[data-cap-seek]').evaluate('(el)=>{el.value=.5;el.dispatchEvent(new Event("input",{bubbles:true}))}');await page.wait_for_function('SFAudioNodes.getState().captionPreview.clipIndex===0&&!SFAudioNodes.getState().captionPreview.buffering');assert (await pixel())[0]>180
   await dialog.locator('[data-cap-close]').click();assert await page.evaluate('SFAudioNodes.getState().captionPreview===null');assert not posts,posts;await browser.close()
 print('PASS real red/blue/green joins: previous frame stays visible under forced decode delay, timeline/audio wait, no black pixels across preloaded join, two decoders only, seeking/cleanup; mode labels readable; node screenshot saved')
if __name__=='__main__':asyncio.run(main())
