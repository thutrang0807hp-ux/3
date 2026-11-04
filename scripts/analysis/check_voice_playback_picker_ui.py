"""Real browser WAV playback and compact voice picker; TTS endpoints are fixtures, not a model test."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright,expect
async def main():
 html=Path('workflow.html').read_text();wav=Path('/workspace/3/docs/voice-cpu-real.wav').read_bytes();posts=[];fail_tts=False
 voices=[{'id':'voice'+str(i),'label':'Giọng '+str(i)+' · Nam Bắc · Phong cách tự nhiên'} for i in range(25)]
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await browser.new_page(viewport={'width':1450,'height':1000})
  async def route(r):
   url=r.request.url
   if '/local-api/media/fixture.wav' in url:await r.fulfill(body=wav,content_type='audio/wav');return
   if url.endswith('/tts/status'):await r.fulfill(json={'installed':True,'model_ready':True,'voices':voices});return
   if url.endswith('/audio-effects/status'):await r.fulfill(status=503,json={'detail':'fixture optional effects unavailable'});return
   if url.endswith('/tts') and r.request.method=='POST':
    body=r.request.post_data_json;posts.append(body)
    if fail_tts:await r.fulfill(status=503,json={'detail':'fixture VieNeu worker unavailable'});return
    rows=body['beats'];length=5.44/len(rows);await r.fulfill(json={'url':'/local-api/media/fixture.wav','request_id':'tts-fixture-'+str(len(posts)),'duration':5.44,'segments':[{'id':row['id'],'start':i*length,'end':(i+1)*length} for i,row in enumerate(rows)]});return
   if '/local-api/' in url:await r.fulfill(json={'enabled':True,'native_pipeline':True,'accounts':[],'unresolved':[],'selection':{'available':False}});return
   await r.fulfill(body=html,content_type='text/html')
  await page.route('**/*',route)
  await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFAudioNodes&&!!window.SceneForgeWorkflow')
  await page.evaluate('''async()=>{project=blankProject();project.id='voice-fixture';project.scenes=[sceneRecord(0,8,0,["data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"])];project.script=[{id:'line1',start:0,end:3,newText:'Xin chào bạn.',original:'Xin chào bạn.'},{id:'line2',start:3,end:8,newText:'Đây là lời đọc thử.',original:'Đây là lời đọc thử.'}];render();await SFAudioNodes.refresh();}''')
  async def focus():
   await page.evaluate("()=>{const n=document.querySelector('#node-voice-over');view.z=1;view.x=30-n.offsetLeft;view.y=150-n.offsetTop;applyView();}")
   await page.wait_for_timeout(80)
  await focus();await page.locator('#node-voice-over [data-an=voice][data-id=ai]').click();await focus()
  node=page.locator('#node-voice-over')
  assert await node.locator('.anVoices').count()==0
  assert (await node.bounding_box())['height']<650
  assert await page.evaluate('SFAudioNodes.getState().tts.model_ready'),'Optional effects error must not hide ready TTS'
  await node.locator('[data-an=voices]').click();picker=page.locator('#anVoicePicker');await expect(picker).to_be_visible()
  bounds=await picker.locator('.anVoicePickerList').evaluate('(el)=>({height:el.clientHeight,scroll:el.scrollHeight})');assert bounds['height']<=340 and bounds['scroll']>bounds['height']
  await picker.locator('#anVoiceSearch').fill('Giọng 17');await expect(picker.locator('[data-an=preset]')).to_have_count(1)
  await picker.locator('[data-an=preset]').click();await focus();await expect(picker).not_to_be_visible()
  await expect(node.locator('[data-an=voices]')).to_contain_text('Giọng 17');assert not posts,'Selecting voice must not synthesize'
  # Simulate a browser denying async autoplay once. A ready sample must remain reusable.
  await page.evaluate('''()=>{window.audioPlayOriginal=HTMLMediaElement.prototype.play;window.denyAudioOnce=true;HTMLMediaElement.prototype.play=function(){if(this.tagName==='AUDIO'&&window.denyAudioOnce){window.denyAudioOnce=false;return Promise.reject(new DOMException('fixture autoplay policy','NotAllowedError'))}return audioPlayOriginal.call(this)};}''')
  await focus();await node.locator('[data-an=sample]').click()
  await expect(node.locator('.anError')).to_contain_text('bấm ▶ Nghe lại')
  await expect(node.locator('[data-an=sample]')).to_be_enabled();assert len(posts)==1 and posts[0]['voice']=='voice17' and posts[0]['beats'][0]['id']=='sample'
  assert await page.evaluate('!project.voiceOver.assetId'),'Sample must not masquerade as complete narration'
  await focus();await node.locator('[data-an=sample]').click();await page.wait_for_function('SFAudioNodes.getState().playback.active&&SFAudioNodes.getState().playback.time>0.1')
  assert len(posts)==1,'Replaying saved sample must not synthesize again'
  await node.locator('[data-an=sample]').click();await page.wait_for_function('!SFAudioNodes.getState().playback.active')
  await focus();await node.locator('[data-an=generate]').click();await page.wait_for_function('!!project.voiceOver.assetId&& !SFAudioNodes.getState().busy')
  assert len(posts)==2 and len(posts[1]['beats'])==2
  assert await page.evaluate('project.voiceOver.generatedPreset===\'voice17\'&&assets.has(project.voiceOver.assetId)&&project.voiceOver.duration>5')
  await focus();await node.locator('[data-an=play-voice]').click();await page.wait_for_function('SFAudioNodes.getState().playback.active&&SFAudioNodes.getState().playback.time>0.1')
  # A worker error must be visible at the top of the node, with controls restored.
  fail_tts=True;await node.locator('[data-an=voices]').click();await picker.locator('#anVoiceSearch').fill('Giọng 18');await picker.locator('[data-an=preset]').click();await focus()
  await node.locator('[data-an=sample]').click();await expect(node.locator('.anError')).to_contain_text('fixture VieNeu worker unavailable');await expect(node.locator('[data-an=sample]')).to_be_enabled();await expect(node.locator('[data-an=generate]')).to_be_enabled()
  print('PASS 25-voice picker stays compact/searchable; real WAV playback advances; autoplay denial keeps sample and retry makes no new TTS; full narration saved; optional effects do not block TTS; worker errors remain visible')
  await browser.close()
if __name__=='__main__':asyncio.run(main())
