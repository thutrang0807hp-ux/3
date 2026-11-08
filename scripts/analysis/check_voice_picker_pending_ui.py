"""Browser responsiveness with deliberately blocked saves and TTS/media responses."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright,expect
async def main():
 html=Path('workflow.html').read_text();wav=Path('/workspace/3/docs/voice-cpu-real.wav').read_bytes();tts_started=asyncio.Event();release_tts=asyncio.Event();media_started=asyncio.Event();release_media=asyncio.Event();posts=[]
 voices=[{'id':v,'label':'Giọng '+v} for v in ['A','B','C']]
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1450,'height':1000})
  await page.add_init_script("window.audioPlayCalls=0;const originalPlay=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){if(this.tagName==='AUDIO')audioPlayCalls++;return originalPlay.call(this)}")
  async def route(r):
   url=r.request.url
   if url.endswith('/tts/status'):await r.fulfill(json={'model_ready':True,'installed':True,'voices':voices});return
   if url.endswith('/tts/previews/status'):await r.fulfill(json={'state':'not-prepared','total':3,'ready':[{'id':'B','url':'/local-api/media/shared-B.wav'}]});return
   if url.endswith('/tts') and r.request.method=='POST':
    posts.append(r.request.post_data_json);tts_started.set();await release_tts.wait();await r.fulfill(json={'url':'/local-api/media/generated-A.wav','request_id':'fixture-tts-A','duration':5.44,'segments':[{'id':'sample','start':0,'end':5.44}]});return
   if url.endswith('/media/shared-B.wav'):media_started.set();await release_media.wait();await r.fulfill(body=wav,content_type='audio/wav');return
   if url.endswith('/media/generated-A.wav'):await r.fulfill(body=wav,content_type='audio/wav');return
   if '/local-api/' in url:await r.fulfill(json={});return
   await r.fulfill(body=html,content_type='text/html')
  await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFAudioNodes&&!!window.SceneForgeWorkflow')
  await page.evaluate('''async()=>{project=blankProject();project.id='picker-pending';project.scenes=[sceneRecord(0,8,0,['data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'])];project.script=[{id:'line',start:0,end:8,newText:'Lời đọc thử.'}];project.voiceOver={mode:'separate',origin:'vieneu',preset:'A',voice:'A',versions:[]};document.body.classList.add('compactWorkspaceFrame');render();await SFAudioNodes.refresh();window.retainedFrame=document.querySelector('[id^=frame-]');window.originalVoiceStore=storeProject;window.voiceSaves=0;window.releaseVoiceSaves=[];storeProject=()=>{voiceSaves++;return new Promise(resolve=>releaseVoiceSaves.push(resolve));};}''')
  node=page.locator('#node-voice-over');picker=page.locator('#anVoicePicker')
  async def focus():
   await page.evaluate("()=>{const n=document.querySelector('#node-voice-over');view.z=1;view.x=30-n.offsetLeft;view.y=150-n.offsetTop;applyView();}")
  async def choose(v):
   await focus();await node.locator('[data-an=voices]').click();await picker.locator('[data-an=preset][data-id='+v+']').click();await expect(picker).not_to_be_visible(timeout=1000);await expect(node.locator('[data-an=voices]')).to_contain_text('Giọng '+v)
  await page.evaluate("project.voiceOver.mode='flow';render();retainedFrame=document.querySelector('[id^=frame-]')")
  await focus();await node.locator('[data-an=voice][data-id=ai]').click();await expect(node.locator('[data-an=voices]')).to_be_visible();await page.wait_for_function('!SFAudioNodes.getState().busy')
  await focus();await node.locator('[data-an=sample]').click();await asyncio.wait_for(tts_started.wait(),3)
  assert await page.evaluate('SFAudioNodes.getState().sampleGenerating&&!SFAudioNodes.getState().busy')
  await choose('B');await page.wait_for_function('voiceSaves>0');assert not release_tts.is_set()
  await choose('C');assert len(posts)==1 and await page.evaluate('project.voiceOver.voice')=='C'
  await expect(node.locator('[data-an=generate]')).to_be_disabled()
  release_tts.set();await page.wait_for_function('!SFAudioNodes.getState().sampleBusy&&!SFAudioNodes.getState().sampleGenerating')
  assert await page.evaluate("project.voiceOver.voice==='C'&&!!project.audioNodes.samples.A&&audioPlayCalls===0"),'Old voice result must cache quietly, never change selection or autoplay'
  # A blocked read of a prepared sample must also leave the picker usable.
  await choose('B');await focus();await node.locator('[data-an=sample]').click();await asyncio.wait_for(media_started.wait(),3);await choose('C');release_media.set();await page.wait_for_function('!SFAudioNodes.getState().sampleBusy')
  assert len(posts)==1 and await page.evaluate("audioPlayCalls===0&&!!project.audioNodes.samples.B&&project.voiceOver.voice==='C'")
  assert await page.evaluate("retainedFrame===document.querySelector('[id^=frame-]')")
  # Cached sample plays without TTS, even though all project-save promises remain blocked.
  await choose('A');await focus();await node.locator('[data-an=sample]').click();await page.wait_for_function('SFAudioNodes.getState().playback.active&&SFAudioNodes.getState().playback.time>0.1');assert len(posts)==1
  await page.evaluate('''async()=>{storeProject=originalVoiceStore;for(const resolve of releaseVoiceSaves)resolve();await storeProject();}''')
  print('PASS picker changes/opens while saves, TTS and sample reads are blocked; only one TTS; old results cache without autoplay or selection overwrite; cached replay works during pending saves; frame DOM retained')
  await browser.close()
if __name__=='__main__':asyncio.run(main())
