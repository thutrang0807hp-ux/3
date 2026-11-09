"""Stable player geometry, synchronized preview speed and reversible non-destructive trims."""
from review_ui_helpers import ensure_review_tab
import asyncio,base64,subprocess,tempfile,zipfile,sys,importlib,json
import httpx,io,math,array
from PIL import Image,ImageDraw
from fastapi import FastAPI
from pathlib import Path
from playwright.async_api import async_playwright,expect
async def main():
 html=Path('workflow.html').read_text();voice=base64.b64encode(Path('/workspace/3/docs/voice-cpu-real.wav').read_bytes()).decode()
 with tempfile.TemporaryDirectory() as tmp:
  file=Path(tmp)/'clip.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=90x160:rate=24','-t','3','-c:v','libx264','-pix_fmt','yuv420p',str(file)],check=True);video=base64.b64encode(file.read_bytes()).decode()
  logo=Path(tmp)/'brand.png';im=Image.new('RGBA',(120,60),(0,0,0,0));ImageDraw.Draw(im).rectangle((12,6,107,53),fill=(229,123,35,255));im.save(logo)
  musicfile=Path(tmp)/'music.wav';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=880:sample_rate=48000','-t','1',str(musicfile)],check=True);music=base64.b64encode(musicfile.read_bytes()).decode()
  # Use the installed renderer protocol with real FFmpeg, without starting a server.
  runtime=Path(tmp)/'runtime82';runtime.mkdir();(runtime/'__init__.py').write_text('')
  with zipfile.ZipFile('/workspace/3/downloads/v42/SceneForge-Veo-v42-Source.zip') as archive:
   for name in ['timeline_export.py','local_jobs.py','schema.py']:(runtime/name).write_bytes(archive.read('local_engine/'+name))
  patched=Path('local_engine/timeline_export.py');patched=patched if patched.is_file() else Path('/workspace/3/veo-node-v46/local_engine/timeline_export.py');(runtime/'timeline_export.py').write_bytes(patched.read_bytes());save_module=patched.with_name('export_save_as.py');(runtime/'export_save_as.py').write_bytes(save_module.read_bytes())
  sys.path.insert(0,tmp);renderer=importlib.import_module('runtime82.timeline_export');app=FastAPI();renderer.install_timeline_exports(app,Path(tmp))
  client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local');requests=[];models=[];hold_start=False;start_entered=asyncio.Event();start_gate=asyncio.Event()
  async with async_playwright() as p:
   browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1450,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.add_init_script("window.showSaveFilePicker=undefined;window.previewAudioElements=[];const OriginalAudio=Audio;window.Audio=function(...args){const el=new OriginalAudio(...args);previewAudioElements.push(el);return el};Audio.prototype=OriginalAudio.prototype")
   async def route(r):
    if '/local-api/export/timeline' in r.request.url:
     path=r.request.url.split('/local-api/')[1];requests.append((r.request.method,path))
     if path=='export/timeline' and r.request.method=='POST':models.append(json.loads(r.request.post_data_buffer))
     if hold_start and path.endswith('/start'):start_entered.set();await start_gate.wait()
     response=await client.request(r.request.method,'/local-api/'+path,content=r.request.post_data_buffer,headers={'Content-Type':r.request.headers.get('content-type','application/json'),'X-SceneForge-Local':'1'});await r.fulfill(status=response.status_code,body=response.content,headers={'Content-Type':response.headers.get('content-type','application/json')});return
    if '/local-api/' in r.request.url:await r.fulfill(json={});return
    await r.fulfill(body=html,content_type='text/html')
   await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFAudioNodes&&!!window.SFReferenceNodes')
   await page.evaluate('''async({video,voice,music})=>{project=blankProject();project.id='preview-controls';const image='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';const blob=(data,name,type)=>new File([Uint8Array.from(atob(data),c=>c.charCodeAt(0))],name,{type});assets.set('clip',blob(video,'clip.mp4','video/mp4'));assets.set('voice',blob(voice,'voice.wav','audio/wav'));project.scenes=[0,1].map(i=>{const s=sceneRecord(i*3,(i+1)*3,i,[image]);s.approvedFrame='source';s.sourceFrame={id:'source',image,asset:'frame'};s.clipPlanning={mode:'legacy',continuity:false};s.clips=[{id:'c'+i,asset:'clip',part:'a',duration:3,version:1,frameId:'source',reviewDecision:{status:'accepted'}}];s.chosen={a:'c'+i};return s;});assets.set('music',blob(music,'music.wav','audio/wav'));project.merge.musicMode='selected';project.merge.musicAsset='music';project.merge.musicName='music.wav';project.merge.musicLibrary=[{asset:'music',name:'music.wav',duration:1}];project.merge.musicVolume=.2;project.voiceOver={mode:'separate',origin:'import',assetId:'voice',duration:5.44,clipSound:'mute',versions:[]};project.merge.captions=true;project.merge.captionWords=0;project.merge.captionDraft=[{start:0,end:3,text:'một hai ba bốn năm sáu',manual:true},{start:3,end:6,text:'bảy tám chín mười mười một',manual:true}];project.merge.captionDraftSignature=productionCaptionSignature();document.body.classList.add('compactWorkspaceFrame');render();await SFAudioNodes.refresh();window.originalPreviewData=JSON.stringify({scenes:project.scenes,cues:project.merge.captionDraft,voice:project.voiceOver});const n=document.querySelector('#node-captions');view.z=1;view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView();}''',{'video':video,'voice':voice,'music':music})
   await page.locator('#node-captions [data-an=caption-preview]').click();dialog=page.locator('#anCaptionDialog');await expect(dialog).to_be_visible()

   await expect(dialog.locator('[data-cap-export]')).to_be_enabled()
   await ensure_review_tab(page,'[data-cap-play]');await dialog.locator('[data-cap-play]').click();await page.wait_for_function('document.querySelector("video[data-cap-active]").currentTime>.15')
   # Simulate a stalled media clock while readyState remains ready. Timeline must not run ahead.
   fixed=await page.evaluate("""()=>{const v=document.querySelector('video[data-cap-active]');window.clockDescriptor=Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype,'currentTime');const at=v.currentTime;Object.defineProperty(v,'currentTime',{configurable:true,get:()=>at,set:value=>clockDescriptor.set.call(v,value)});return at}""")
   await page.wait_for_timeout(400);state=await page.evaluate('SFAudioNodes.getState().captionPreview');assert abs(state['time']-fixed)<.03,state
   await ensure_review_tab(page,'[data-cap-play]');await dialog.locator('[data-cap-play]').click();await page.evaluate("delete document.querySelector('video[data-cap-active]').currentTime")
   await ensure_review_tab(page,'[data-cap-end-number]');await dialog.locator('[data-cap-end-number]').fill('2.117');await dialog.locator('[data-cap-end-number]').dispatch_event('change')
   await ensure_review_tab(page,'[data-cap-source]');await dialog.locator('[data-cap-source]').click();source=page.locator('.anSourceDialog');await expect(source).to_be_visible()
   await page.wait_for_function("document.querySelector('.anSourceDialog video').currentTime>1.05")
   assert not await page.evaluate('SFAudioNodes.getState().captionPreview.playing');assert abs(await source.locator('video').evaluate('v=>v.duration')-3)<.02
   await source.locator('button').click();await expect(source).to_have_count(0)
   await ensure_review_tab(page,'.anLogoTools summary');await dialog.locator('.anLogoTools summary').click();await ensure_review_tab(page,'[data-cap-logo-file]');await dialog.locator('[data-cap-logo-file]').set_input_files(str(logo));await expect(dialog.locator('[data-cap-logo-status]')).to_contain_text('Đã thêm')
   assert await page.evaluate('SFAudioNodes.logoSettings().enabled&&assets.has(SFAudioNodes.logoSettings().key)')
   await ensure_review_tab(page,'[data-cap-logo-width]');await dialog.locator('[data-cap-logo-width]').fill('25');await ensure_review_tab(page,'[data-cap-logo-corner=tl]');await dialog.locator('[data-cap-logo-corner=tl]').click();await ensure_review_tab(page,'[data-cap-logo-opacity]');await dialog.locator('[data-cap-logo-opacity]').fill('0.8');await ensure_review_tab(page,'[data-cap-logo-plate]');await dialog.locator('[data-cap-logo-plate]').uncheck()
   assert await page.evaluate("(()=>{const c=document.querySelector('[data-cap-logo-layer]'),d=c.getContext('2d').getImageData(151,103,1,1).data;return d[0]===229&&Math.abs(d[3]-204)<2})()")
   await ensure_review_tab(page,'[data-cap-logo-corner=br]');await dialog.locator('[data-cap-logo-corner=br]').click();await ensure_review_tab(page,'[data-cap-logo-opacity]');await dialog.locator('[data-cap-logo-opacity]').fill('1');await ensure_review_tab(page,'[data-cap-logo-plate]');await dialog.locator('[data-cap-logo-plate]').check();await ensure_review_tab(page,'[data-cap-logo-plate-color]');await dialog.locator('[data-cap-logo-plate-color]').fill('#123456')
   await ensure_review_tab(page,'[data-cap-color]');await dialog.locator('[data-cap-color]').fill('#12ab34');await ensure_review_tab(page,'[data-cap-bg-color]');await dialog.locator('[data-cap-bg-color]').fill('#2345cd');await ensure_review_tab(page,'[data-cap-bg-enabled]');await dialog.locator('[data-cap-bg-enabled]').check();await ensure_review_tab(page,'[data-cap-bg-opacity]');await dialog.locator('[data-cap-bg-opacity]').fill('0.4');await ensure_review_tab(page,'[data-cap-y]');await dialog.locator('[data-cap-y]').fill('50');await ensure_review_tab(page,'[data-cap-words]');await dialog.locator('[data-cap-words]').select_option('3');await dialog.locator('[data-cap-words]').dispatch_event('input')
   await expect(dialog.locator('[data-cap-export]')).to_be_enabled();assert not await page.evaluate('SFAudioNodes.getState().captionPreview.joined');assert models==[]

   # Stale captions are blocked before the final renderer is started and controls recover.
   await page.evaluate('project.merge.audioChanged=true');await ensure_review_tab(page,'[data-cap-export]');await dialog.locator('[data-cap-export]').click();await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('Phụ đề cần rà')
   assert len(models)==0;await expect(dialog.locator('[data-cap-export]')).to_be_enabled()
   await ensure_review_tab(page,'[data-cap-review-open]');await dialog.locator('[data-cap-review-open]').click();await ensure_review_tab(page,'[data-cap-cue="0"][data-field=text]');await dialog.locator('[data-cap-cue="0"][data-field=text]').fill('MỘT hai ba bốn năm sáu');await ensure_review_tab(page,'[data-cap-cue="0"][data-field=end]');await dialog.locator('[data-cap-cue="0"][data-field=end]').fill('2.95');await ensure_review_tab(page,'[data-cap-review-accept]');await dialog.locator('[data-cap-review-accept]').click()
   await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('Đã giữ bản phụ đề');assert await page.evaluate('!project.merge.audioChanged&&project.merge.captionDraft[0].text.startsWith("MỘT")&&project.merge.captionDraft[0].end===2.95')
   await ensure_review_tab(page,'[data-cap-final-rate]');await dialog.locator('[data-cap-final-rate]').select_option('1.5');assert await dialog.locator('[data-cap-rate]').input_value()=='1.5';await expect(dialog.locator('[data-cap-final-duration]')).to_contain_text('3.41 giây')

   await ensure_review_tab(page,'[data-cap-export-size]');await dialog.locator('[data-cap-export-size]').select_option('720');await ensure_review_tab(page,'[data-cap-rate]');await dialog.locator('[data-cap-rate]').select_option('2')
   async with page.expect_download(timeout=90000) as pending:
    await ensure_review_tab(page,'[data-cap-export]');await dialog.locator('[data-cap-export]').click();await page.wait_for_function('!SFAudioNodes.getState().captionPreview.exportBusy',timeout=60000);assert await page.evaluate('SFAudioNodes.getState().captionPreview.exportReady'),await dialog.locator('[data-cap-export-status]').inner_text();await ensure_review_tab(page,'[data-cap-browser-download]');await dialog.locator('[data-cap-browser-download]').click()
   download=await pending.value;assert download.suggested_filename.endswith('-thanh-pham.mp4');output=Path(tmp)/'final.mp4';await download.save_as(str(output))
   await page.wait_for_function('!SFAudioNodes.getState().captionPreview.exportBusy&&SFAudioNodes.getState().captionPreview.exportReady')
   model=models[-1];assert model['width']==720 and model['height']==1280 and model['fps']==30 and abs(model['duration']-5.117/1.5)<1/30+.001
   voices=[r for r in model['clips'] if r['track']=='voice'];songs=[r for r in model['clips'] if r['track']=='music'];captions=[r for r in model['clips'] if r['track']=='captions']
   assert len(voices)==2 and abs(voices[1]['mediaIn']-3)<.001 and abs(voices[1]['start']-2.117/1.5)<.001 and all(r['speed']==1.5 and r['preservePitch'] for r in voices)
   assert len(songs)==6 and abs(sum(r['duration'] for r in songs)-5.117/1.5)<.001 and len(captions)>=4
   assert all(r['kind']=='image' and r['start']+r['duration']<=5.117/1.5+1/30+.001 for r in captions)
   meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)]))
   v=next(r for r in meta['streams'] if r['codec_type']=='video');a=next(r for r in meta['streams'] if r['codec_type']=='audio')
   assert (v['width'],v['height'],v['codec_name'],a['codec_name'])==(720,1280,'h264','aac');assert abs(float(meta['format']['duration'])-5.117/1.5)<.07
   # Inspect burned-in custom green text in actual decoded MP4 frames, including both sides of the cut.
   for at in [.5,1.39,1.45,1.6]:
    frame=subprocess.check_output(['ffmpeg','-v','error','-ss',str(at),'-i',str(output),'-frames:v','1','-f','image2pipe','-vcodec','png','-threads','1','-'])
    im=Image.open(io.BytesIO(frame)).convert('RGB');region=list(im.crop((80,590,640,690)).get_flattened_data());green=sum(1 for r,g,b in region if abs(r-18)<35 and abs(g-171)<35 and abs(b-52)<35)
    assert green>20,(at,green);assert sum(sum(p) for p in im.resize((12,20)).get_flattened_data())/240>60,('Black boundary frame',at,sum(sum(p) for p in im.resize((12,20)).get_flattened_data())/240)
   assert len([r for r in model['clips'] if r['track']=='logo'])==1
   frame=subprocess.check_output(['ffmpeg','-v','error','-ss','0.5','-i',str(output),'-frames:v','1','-f','image2pipe','-vcodec','png','-threads','1','-']);brand_frame=Image.open(io.BytesIO(frame)).convert('RGB')
   orange=brand_frame.getpixel((612,1204));plate=brand_frame.getpixel((519,1156));assert all(abs(a-b)<30 for a,b in zip(orange,(229,123,35))),orange;assert all(abs(a-b)<25 for a,b in zip(plate,(18,52,86))),plate
   assert not any(m['width']==360 for m in models),'Export must not create or download a low resolution preview'
   # Voice has ended here; nonzero final audio proves short background music repeats to the end.
   pcm=subprocess.check_output(['ffmpeg','-v','error','-ss','3.2','-i',str(output),'-t','0.15','-vn','-ac','1','-ar','48000','-f','s16le','-']);samples=array.array('h',pcm);rms=math.sqrt(sum(x*x for x in samples)/len(samples));assert rms>150,rms;frequency=sum(1 for i in range(1,len(samples)) if samples[i-1]<=0<samples[i])/.15;assert abs(frequency-880)<40,frequency
   created=len(models)
   async with page.expect_download():await ensure_review_tab(page,'[data-cap-browser-download]');await dialog.locator('[data-cap-browser-download]').click()
   assert len(models)==created,'Download again must reuse completed MP4'
   # Also render the 1080p path using a short retained interval in each original clip.
   for index in ['0','1']:
    await ensure_review_tab(page,'[data-cap-cut-clip]');await dialog.locator('[data-cap-cut-clip]').select_option(index);await ensure_review_tab(page,'[data-cap-end-number]');await dialog.locator('[data-cap-end-number]').fill('0.2');await dialog.locator('[data-cap-end-number]').dispatch_event('change')
   await expect(dialog.locator('[data-cap-export]')).to_be_enabled();await ensure_review_tab(page,'[data-cap-export-size]');await dialog.locator('[data-cap-export-size]').select_option('1080');await ensure_review_tab(page,'[data-cap-final-rate]');await dialog.locator('[data-cap-final-rate]').select_option('0.5')
   async with page.expect_download(timeout=90000) as pending1080:
    await ensure_review_tab(page,'[data-cap-export]');await dialog.locator('[data-cap-export]').click();await page.wait_for_function('!SFAudioNodes.getState().captionPreview.exportBusy',timeout=60000);assert await page.evaluate('SFAudioNodes.getState().captionPreview.exportReady'),await dialog.locator('[data-cap-export-status]').inner_text();await ensure_review_tab(page,'[data-cap-browser-download]');await dialog.locator('[data-cap-browser-download]').click()
   final1080=Path(tmp)/'final1080.mp4';await(await pending1080.value).save_as(str(final1080))
   meta1080=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(final1080)]));v1080=next(r for r in meta1080['streams'] if r['codec_type']=='video');assert (v1080['width'],v1080['height'])==(1080,1920) and abs(float(meta1080['format']['duration'])-.8)<.07
   for at in [0.39,0.41,0.44]:
    frame1080=subprocess.check_output(['ffmpeg','-v','error','-ss',str(at),'-i',str(final1080),'-frames:v','1','-f','image2pipe','-vcodec','png','-threads','1','-']);im1080=Image.open(io.BytesIO(frame1080)).convert('RGB');assert sum(sum(p) for p in im1080.resize((12,20)).get_flattened_data())/240>60,('Slow join black frame',at)
   await dialog.locator('aside').evaluate('e=>e.scrollTop=0');await dialog.screenshot(path='/tmp/sceneforge-export-speed-v85.png')
   # Skip stale captions only by an explicit one-off action; preserve the draft and its warning.
   await page.evaluate('project.merge.audioChanged=true');await ensure_review_tab(page,'[data-cap-final-rate]');await dialog.locator('[data-cap-final-rate]').select_option('1');await ensure_review_tab(page,'[data-cap-export]');await dialog.locator('[data-cap-export]').click();await expect(dialog.locator('[data-cap-caption-review]')).to_be_visible()
   before=len(models)
   async with page.expect_download(timeout=90000) as no_captions:
    await ensure_review_tab(page,'[data-cap-export-no-captions]');await dialog.locator('[data-cap-export-no-captions]').click();await page.wait_for_function('!SFAudioNodes.getState().captionPreview.exportBusy',timeout=60000);assert await page.evaluate('SFAudioNodes.getState().captionPreview.exportReady'),await dialog.locator('[data-cap-export-status]').inner_text();await ensure_review_tab(page,'[data-cap-browser-download]');await dialog.locator('[data-cap-browser-download]').click()
   await(await no_captions.value).save_as(str(Path(tmp)/'without-captions.mp4'));assert len(models)==before+1 and not any(r['track']=='captions' for r in models[-1]['clips']);assert any(r['track']=='logo' for r in models[-1]['clips'])
   assert await page.evaluate('project.merge.captions&&project.merge.audioChanged&&project.merge.captionDraft[0].text.startsWith("MỘT")')
   await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('không kèm phụ đề')
   # A normal export must not silently reuse the no-caption final.
   await ensure_review_tab(page,'[data-cap-export]');await dialog.locator('[data-cap-export]').click();await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('Phụ đề cần rà');assert len(models)==before+1
   await ensure_review_tab(page,'[data-cap-review-accept]');await dialog.locator('[data-cap-review-accept]').click();await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('Đã giữ bản phụ đề')
   # New caption settings retire the old final; cancellation recovers all editing controls.
   await ensure_review_tab(page,'[data-cap-color]');await dialog.locator('[data-cap-color]').fill('#ff9933');await expect(dialog.locator('[data-cap-download]')).to_be_hidden()
   hold_start=True;await ensure_review_tab(page,'[data-cap-export]');await dialog.locator('[data-cap-export]').click();await asyncio.wait_for(start_entered.wait(),15);await ensure_review_tab(page,'[data-cap-export-cancel]');await dialog.locator('[data-cap-export-cancel]').click();start_gate.set()
   await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('Đã hủy');await expect(dialog.locator('[data-cap-color]')).to_be_enabled();await expect(dialog.locator('[data-cap-export]')).to_be_enabled();assert not await page.evaluate('SFAudioNodes.getState().captionPreview.exportReady')
   assert any(method=='POST' and path.endswith('/cancel') for method,path in requests)
   await ensure_review_tab(page,'[data-cap-logo-enabled]');await dialog.locator('[data-cap-logo-enabled]').uncheck();assert await page.evaluate('!SFAudioNodes.logoSettings().enabled');assert await page.evaluate('(async()=>await SFAudioNodes.logoLayer()===null)()')
   await ensure_review_tab(page,'[data-cap-logo-enabled]');await dialog.locator('[data-cap-logo-enabled]').check();await expect(dialog.locator('[data-cap-logo-status]')).to_contain_text('Đã thêm')
   await ensure_review_tab(page,'[data-cap-close]');await dialog.locator('[data-cap-close]').click();await page.locator('#node-captions [data-an=caption-preview]').click();dialog=page.locator('#anCaptionDialog');await expect(dialog.locator('[data-cap-logo-status]')).to_contain_text('Logo đã sẵn sàng')
   assert await page.evaluate('SFAudioNodes.logoSettings().width===25&&SFAudioNodes.logoSettings().plateColor==="#123456"')
   await ensure_review_tab(page,'.anLogoTools summary');await dialog.locator('.anLogoTools summary').click();await ensure_review_tab(page,'[data-cap-logo-remove]');await dialog.locator('[data-cap-logo-remove]').click();assert await page.evaluate('!SFAudioNodes.logoSettings().key&&!SFAudioNodes.logoSettings().enabled')
   await ensure_review_tab(page,'[data-cap-close]');await dialog.locator('[data-cap-close]').click();await page.evaluate("project.scenes[1].clips[0].asset='missing';render()");await page.locator('#node-captions [data-an=caption-preview]').click();dialog=page.locator('#anCaptionDialog');await expect(dialog.locator('[data-cap-export]')).to_be_disabled();await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('Còn thiếu')
   await ensure_review_tab(page,'[data-cap-close]');await dialog.locator('[data-cap-close]').click();assert not errors,errors;await browser.close();await client.aclose()
 print('PASS inline stale-caption review preserves edited text/times; explicit no-caption export leaves source draft unchanged; actual 1.5x 720p and 0.5x 1080p MP4s with retimed voice/music/captions/logo and preserved 880Hz pitch; no stale cache reuse; cancel recovery')
if __name__=='__main__':asyncio.run(main())
