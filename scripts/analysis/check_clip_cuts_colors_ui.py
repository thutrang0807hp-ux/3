"""Stable player geometry, synchronized preview speed and reversible non-destructive trims."""
from review_ui_helpers import ensure_review_tab
import asyncio,base64,subprocess,tempfile,zipfile,sys,importlib,json
import httpx
from fastapi import FastAPI
from pathlib import Path
from playwright.async_api import async_playwright,expect
async def main():
 html=Path('workflow.html').read_text();voice=base64.b64encode(Path('/workspace/3/docs/voice-cpu-real.wav').read_bytes()).decode()
 with tempfile.TemporaryDirectory() as tmp:
  file=Path(tmp)/'clip.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=90x160:rate=24','-t','3','-c:v','libx264','-pix_fmt','yuv420p',str(file)],check=True);video=base64.b64encode(file.read_bytes()).decode()
  # Use the installed renderer protocol with real FFmpeg, without starting a server.
  runtime=Path(tmp)/'runtime82';runtime.mkdir();(runtime/'__init__.py').write_text('')
  with zipfile.ZipFile('/workspace/3/downloads/v42/SceneForge-Veo-v42-Source.zip') as archive:
   for name in ['timeline_export.py','local_jobs.py','schema.py']:(runtime/name).write_bytes(archive.read('local_engine/'+name))
  sys.path.insert(0,tmp);renderer=importlib.import_module('runtime82.timeline_export');app=FastAPI();renderer.install_timeline_exports(app,Path(tmp))
  client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local');requests=[]
  async with async_playwright() as p:
   browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1450,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.add_init_script("window.previewAudioElements=[];const OriginalAudio=Audio;window.Audio=function(...args){const el=new OriginalAudio(...args);previewAudioElements.push(el);return el};Audio.prototype=OriginalAudio.prototype")
   async def route(r):
    if '/local-api/export/timeline' in r.request.url:
     path=r.request.url.split('/local-api/')[1];requests.append((r.request.method,path));response=await client.request(r.request.method,'/local-api/'+path,content=r.request.post_data_buffer,headers={'Content-Type':r.request.headers.get('content-type','application/json'),'X-SceneForge-Local':'1'});await r.fulfill(status=response.status_code,body=response.content,headers={'Content-Type':response.headers.get('content-type','application/json')});return
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
   await ensure_review_tab(page,'[data-cap-rate]');await dialog.locator('[data-cap-rate]').select_option('1')
   # A one-second cut exceeds the old 150ms options, applies only to clip 1, and survives reopening.
   await ensure_review_tab(page,'[data-cap-cut-clip]');await dialog.locator('[data-cap-cut-clip]').select_option('0');await ensure_review_tab(page,'[data-cap-end-number]');await dialog.locator('[data-cap-end-number]').fill('2');await dialog.locator('[data-cap-end-number]').dispatch_event('change')
   assert await page.evaluate('SFAudioNodes.getState().captionPreview.total===5')
   await expect(dialog.locator('[data-cap-cut-info]')).to_contain_text('bỏ 1.000s');await stable()
   await ensure_review_tab(page,'[data-cap-frame="1"]');await dialog.locator('[data-cap-frame="1"]').click();assert abs(float(await dialog.locator('[data-cap-end-number]').input_value())-2-1/30)<.001
   await ensure_review_tab(page,'[data-cap-frame="-1"]');await dialog.locator('[data-cap-frame="-1"]').click()
   await ensure_review_tab(page,'[data-cap-color]');await dialog.locator('[data-cap-color]').fill('#12ab34');await ensure_review_tab(page,'[data-cap-bg-color]');await dialog.locator('[data-cap-bg-color]').fill('#2345cd');await ensure_review_tab(page,'[data-cap-bg-enabled]');await dialog.locator('[data-cap-bg-enabled]').check();await ensure_review_tab(page,'[data-cap-bg-opacity]');await dialog.locator('[data-cap-bg-opacity]').fill('0.4')
   # Look for actual colored canvas pixels, not just saved input values.
   await page.wait_for_function("(()=>{const c=document.querySelector('[data-cap-overlay]'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let text=false,bg=false;for(let i=0;i<d.length;i+=4){if(Math.abs(d[i]-18)<3&&Math.abs(d[i+1]-171)<3&&Math.abs(d[i+2]-52)<3&&d[i+3]>250)text=true;if(Math.abs(d[i]-35)<4&&Math.abs(d[i+1]-69)<4&&Math.abs(d[i+2]-205)<4&&Math.abs(d[i+3]-102)<3)bg=true;if(text&&bg)return true;}return false})()")
   exported=await page.evaluate("""async()=>{const clips=project.scenes.map((s,i)=>({key:s.clips[0].id,sceneId:s.id,part:'a',file:assets.get('clip'),start:i*3,duration:3,sourceDuration:3,sourceIn:0}));window.cutExport={clips,audio:[{file:assets.get('voice'),role:'voice',start:0,duration:5.44,place:true}],captions:structuredClone(project.merge.captionDraft),captionStyle:project.merge.captionStyle,partial:true,totalDuration:6,placement:'assembled'};await SFAudioNodes.preparePayload(cutExport);return{clips:cutExport.clips.map(({file,...c})=>c),audio:cutExport.audio.map(({file,...a})=>a),captions:cutExport.captions,options:cutExport.captionOptions,total:cutExport.totalDuration,srt:SFAudioNodes.srt()}}""")
   assert abs(exported['total']-5)<.001 and abs(exported['clips'][1]['start']-2)<.001
   assert len(exported['audio'])==2 and abs(exported['audio'][1]['sourceIn']-3)<.001 and abs(exported['audio'][1]['start']-2)<.001
   assert abs(exported['captions'][1]['start']-2)<.001 and '00:00:02,000' in exported['srt']
   assert exported['options']['textColor']=='#12ab34' and exported['options']['backgroundOpacity']==.4
   # Real renderer generates one MP4; playback crosses the original cut without changing src.
   await ensure_review_tab(page,'[data-cap-joined]');await dialog.locator('[data-cap-joined]').click();await page.wait_for_function('SFAudioNodes.getState().captionPreview.joined',timeout=60000)
   creates=sum(1 for method,path in requests if method=='POST' and path=='export/timeline');assert creates==1
   await dialog.locator('[data-cap-seek]').evaluate('(el)=>{el.value=1.7;el.dispatchEvent(new Event("input",{bubbles:true}))}');await page.wait_for_function('!SFAudioNodes.getState().captionPreview.buffering')
   src=await dialog.locator('video[data-cap-active]').get_attribute('src');await ensure_review_tab(page,'[data-cap-play]');await dialog.locator('[data-cap-play]').click();await page.wait_for_function('SFAudioNodes.getState().captionPreview.time>2.3',timeout=10000)
   assert await dialog.locator('video[data-cap-active]').get_attribute('src')==src
   await ensure_review_tab(page,'[data-cap-play]');await dialog.locator('[data-cap-play]').click();await ensure_review_tab(page,'[data-cap-joined]');await dialog.locator('[data-cap-joined]').click();assert sum(1 for method,path in requests if method=='POST' and path=='export/timeline')==1,'cached replay should not encode again'
   await ensure_review_tab(page,'[data-cap-listen]');await dialog.locator('[data-cap-listen]').click();await page.wait_for_function('SFAudioNodes.getState().captionPreview.time>=3.99&&!SFAudioNodes.getState().captionPreview.playing',timeout=15000)
   await ensure_review_tab(page,'[data-cap-close]');await dialog.locator('[data-cap-close]').click();await page.locator('#node-captions [data-an=caption-preview]').click();dialog=page.locator('#anCaptionDialog');assert await dialog.locator('[data-cap-end-number]').input_value()=='2.000';assert await dialog.locator('[data-cap-color]').input_value()=='#12ab34'
   await dialog.locator('aside').evaluate('e=>e.scrollTop=0');await dialog.screenshot(path='/tmp/sceneforge-cuts-colors-v82.png')
   await ensure_review_tab(page,'[data-cap-reset]');await dialog.locator('[data-cap-reset]').click();assert await page.evaluate('SFAudioNodes.getState().captionPreview.total===6&&!SFAudioNodes.getState().captionPreview.joined');await ensure_review_tab(page,'[data-cap-close]');await dialog.locator('[data-cap-close]').click()
   # Import exact handoff rows in the native editor and check export-ready timing/style.
   editor=await browser.new_page();native=Path('native/index.html').read_text()
   async def editor_route(r):
    if r.request.resource_type=='document':await r.fulfill(body=native,content_type='text/html')
    else:await r.fulfill(status=404,body='')
   await editor.route('**/*',editor_route);await editor.goto('http://127.0.0.1:43891/native/index.html');await editor.wait_for_function('!!window.SceneForgeEditor')
   await editor.evaluate("""({video,voice,exported})=>{const file=(data,name,type)=>new File([Uint8Array.from(atob(data),c=>c.charCodeAt(0))],name,{type});const clip=file(video,'clip.mp4','video/mp4'),audio=file(voice,'voice.wav','audio/wav');window.importAck=null;addEventListener('message',e=>{if(e.data?.type==='sceneforge:workflow-import-ack')window.importAck=e.data});postMessage({type:'sceneforge:workflow-import',id:'cut82',payload:{clips:exported.clips.map((c,i)=>({...c,sourceIn:i===0?.2:c.sourceIn,file:clip})),audio:exported.audio.map(a=>({...a,file:audio})),captions:exported.captions,captionOptions:exported.options,totalDuration:exported.total,partial:true,placement:'assembled'}},location.origin)}""",{'video':video,'voice':voice,'exported':exported})
   await editor.wait_for_function('!!window.importAck',timeout=20000);ack=await editor.evaluate('importAck');assert not ack.get('error'),ack
   state=await editor.evaluate('SceneForgeEditor.getState()');texts=[i for i in state['items'] if i['kind']=='text'];audio_rows=[i for i in state['items'] if i['kind']=='audio'];videos=[i for i in state['items'] if i['kind']=='video']
   assert texts and all(i['color']=='#12ab34' and i['background']=='#2345cd66' and i['textBg'] for i in texts)
   assert len(videos)==2 and abs(videos[0]['mediaIn']-.2)<.001 and abs(videos[1]['start']-2)<.001 and len(audio_rows)==2 and abs(audio_rows[1]['mediaIn']-3)<.001
   assert len(set(i['assetId'] for i in audio_rows))==1,'split voice should reuse source file'
   assert not errors,errors;await browser.close();await client.aclose()
 print('PASS per-clip cuts beyond 150ms, frame nudges, restore/reopen, real canvas colors/alpha, mapped captions and voice, real FFmpeg single-file joins/cache, audition stop, native editor handoff')
if __name__=='__main__':asyncio.run(main())
