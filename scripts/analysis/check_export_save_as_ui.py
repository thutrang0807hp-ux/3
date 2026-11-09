"""Stable player geometry, synchronized preview speed and reversible non-destructive trims."""
from review_ui_helpers import ensure_review_tab
import asyncio,base64,subprocess,tempfile,zipfile,sys,importlib,json
import httpx,io,math,array,hashlib
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
  sys.path.insert(0,tmp);renderer=importlib.import_module('runtime82.timeline_export');app=FastAPI();jobs=renderer.install_timeline_exports(app,Path(tmp));saver=importlib.import_module("runtime82.export_save_as")
  selected=Path(tmp)/'Thành phẩm đã chọn.mp4';selected.write_bytes(b'old destination')
  choices=[None,selected,Path(tmp)/'missing folder'/'denied.mp4'];dialog_calls=[];saver.powershell_path=lambda:'test-save-dialog'
  async def choose(name):dialog_calls.append(name);return choices.pop(0)
  saver.choose_windows_file=choose
  client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local');requests=[];models=[];hold_start=False;start_entered=asyncio.Event();start_gate=asyncio.Event()
  async with async_playwright() as p:
   browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1450,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.add_init_script("window.previewAudioElements=[];const OriginalAudio=Audio;window.Audio=function(...args){const el=new OriginalAudio(...args);previewAudioElements.push(el);return el};Audio.prototype=OriginalAudio.prototype")
   async def route(r):
    if '/local-api/export/' in r.request.url:
     path=r.request.url.split('/local-api/')[1];requests.append((r.request.method,path))
     if path=='export/timeline' and r.request.method=='POST':models.append(json.loads(r.request.post_data_buffer))
     if hold_start and path.endswith('/start'):start_entered.set();await start_gate.wait()
     response=await client.request(r.request.method,'/local-api/'+path,content=r.request.post_data_buffer,headers={'Content-Type':r.request.headers.get('content-type','application/json'),'X-SceneForge-Local':'1'});await r.fulfill(status=response.status_code,body=response.content,headers={'Content-Type':response.headers.get('content-type','application/json')});return
    if '/local-api/' in r.request.url:await r.fulfill(json={});return
    await r.fulfill(body=html,content_type='text/html')
   await page.add_init_script("""window.pickerMode='cancel';window.pickerCalls=[];window.savedHash=null;window.writerAborted=false;window.showSaveFilePicker=async options=>{pickerCalls.push({options,activated:navigator.userActivation.isActive});if(pickerMode==='cancel')throw new DOMException('cancelled','AbortError');return{name:'Bản đã đặt tên.mp4',async createWritable(){return{async write(blob){if(pickerMode==='write-error')throw Error('disk fixture');const bytes=await blob.arrayBuffer();savedHash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(n=>n.toString(16).padStart(2,'0')).join('');},async close(){window.writerClosed=true;},async abort(){window.writerAborted=true;}}}}};""")
   await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFAudioNodes&&!!window.SFReferenceNodes')
   await page.evaluate('''async({video,voice,music})=>{project=blankProject();project.id='preview-controls';const image='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';const blob=(data,name,type)=>new File([Uint8Array.from(atob(data),c=>c.charCodeAt(0))],name,{type});assets.set('clip',blob(video,'clip.mp4','video/mp4'));assets.set('voice',blob(voice,'voice.wav','audio/wav'));project.scenes=[0,1].map(i=>{const s=sceneRecord(i*3,(i+1)*3,i,[image]);s.approvedFrame='source';s.sourceFrame={id:'source',image,asset:'frame'};s.clipPlanning={mode:'legacy',continuity:false};s.clips=[{id:'c'+i,asset:'clip',part:'a',duration:3,version:1,frameId:'source',reviewDecision:{status:'accepted'}}];s.chosen={a:'c'+i};return s;});assets.set('music',blob(music,'music.wav','audio/wav'));project.merge.musicMode='selected';project.merge.musicAsset='music';project.merge.musicName='music.wav';project.merge.musicLibrary=[{asset:'music',name:'music.wav',duration:1}];project.merge.musicVolume=.2;project.voiceOver={mode:'separate',origin:'import',assetId:'voice',duration:5.44,clipSound:'mute',versions:[]};project.merge.captions=true;project.merge.captionWords=0;project.merge.captionDraft=[{start:0,end:3,text:'một hai ba bốn năm sáu',manual:true},{start:3,end:6,text:'bảy tám chín mười mười một',manual:true}];project.merge.captionDraftSignature=productionCaptionSignature();document.body.classList.add('compactWorkspaceFrame');render();await SFAudioNodes.refresh();window.originalPreviewData=JSON.stringify({scenes:project.scenes,cues:project.merge.captionDraft,voice:project.voiceOver});const n=document.querySelector('#node-captions');view.z=1;view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView();}''',{'video':video,'voice':voice,'music':music})
   await page.locator('#node-captions [data-an=caption-preview]').click();dialog=page.locator('#anCaptionDialog');await expect(dialog).to_be_visible()


   downloads=[];page.on('download',lambda d:downloads.append(d))
   # Small real completed MP4; native capability is supplied by the real API with only the dialog mocked.
   await ensure_review_tab(page,'[data-cap-end-number]');await dialog.locator('[data-cap-end-number]').fill('0.2');await dialog.locator('[data-cap-end-number]').dispatch_event('change');await ensure_review_tab(page,'[data-cap-cut-clip]');await dialog.locator('[data-cap-cut-clip]').select_option('1');await ensure_review_tab(page,'[data-cap-end-number]');await dialog.locator('[data-cap-end-number]').fill('0.2');await dialog.locator('[data-cap-end-number]').dispatch_event('change');await ensure_review_tab(page,'[data-cap-export-size]');await dialog.locator('[data-cap-export-size]').select_option('720')
   await ensure_review_tab(page,'[data-cap-export]');await dialog.locator('[data-cap-export]').click();await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('Đã hủy chọn nơi lưu',timeout=60000)
   assert len(models)==1 and len(dialog_calls)==1 and await page.evaluate('SFAudioNodes.getState().captionPreview.exportReady')
   assert selected.read_bytes()==b'old destination' and not downloads
   await ensure_review_tab(page,'[data-cap-download]');await dialog.locator('[data-cap-download]').click();await expect(dialog.locator('[data-cap-export-status]')).to_contain_text(str(selected))
   assert selected.read_bytes()!=b'old destination' and selected.read_bytes()[:4]!=b'old ' and len(models)==1 and not downloads
   digest=hashlib.sha256(selected.read_bytes()).hexdigest();meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(selected)]));assert meta['streams'][0]['codec_name']=='h264'
   # Failed native save preserves the completed export, then offers an explicit browser picker.
   await ensure_review_tab(page,'[data-cap-download]');await dialog.locator('[data-cap-download]').click();await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('Chưa lưu được video')
   assert await page.evaluate('SFAudioNodes.getState().captionPreview.exportReady') and len(models)==1
   await ensure_review_tab(page,'[data-cap-browser-save]');await dialog.locator('[data-cap-browser-save]').click();await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('Đã hủy chọn nơi lưu')
   assert len(models)==1 and not downloads
   await page.evaluate("pickerMode='write-error'");await ensure_review_tab(page,'[data-cap-download]');await dialog.locator('[data-cap-download]').click();await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('disk fixture')
   assert await page.evaluate('writerAborted&&SFAudioNodes.getState().captionPreview.exportReady')
   await page.evaluate("pickerMode='ok'");await ensure_review_tab(page,'[data-cap-download]');await dialog.locator('[data-cap-download]').click();await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('Bản đã đặt tên.mp4')
   assert await page.evaluate('savedHash')==digest and await page.evaluate('writerClosed')
   calls=await page.evaluate('pickerCalls');assert all(c['activated']for c in calls);assert calls[-1]['options']['suggestedName'].endswith('.mp4')
   assert len(models)==1 and len(dialog_calls)==3 and not downloads
   # Unsupported environments expose an explicit download fallback, never an automatic one.
   await page.evaluate('showSaveFilePicker=undefined');await ensure_review_tab(page,'[data-cap-download]');await dialog.locator('[data-cap-download]').click();await expect(dialog.locator('[data-cap-export-status]')).to_contain_text('chưa hỗ trợ chọn nơi lưu')
   assert not downloads
   async with page.expect_download()as fallback:await ensure_review_tab(page,'[data-cap-browser-download]');await dialog.locator('[data-cap-browser-download]').click()
   exported=Path(tmp)/'fallback.mp4';await(await fallback.value).save_as(str(exported));assert hashlib.sha256(exported.read_bytes()).hexdigest()==digest and len(models)==1
   # New route cannot be used to supply a destination path or from an untrusted origin.
   rid=next(iter(jobs))
   bad=await client.post('/local-api/export/timeline/'+rid+'/save-as',json={});assert bad.status_code==403
   bad=await client.post('/local-api/export/timeline/'+rid+'/save-as',headers={'X-SceneForge-Local':'1','Origin':'https://outside.invalid'},json={});assert bad.status_code==403
   bad=await client.post('/local-api/export/timeline/'+rid+'/save-as',headers={'X-SceneForge-Local':'1'},json={'path':'/tmp/not-selected.mp4'});assert bad.status_code==400
   bad=await client.post('/local-api/export/timeline/'+rid+'/save-as',headers={'X-SceneForge-Local':'1'},content=b'x'*4097);assert bad.status_code==413
   # A failed copy must preserve an existing file and remove the partial temporary output.
   destination=Path(tmp)/'preserved.mp4';destination.write_bytes(b'keep me');original_copy=saver.shutil.copyfileobj
   def failed_copy(reader,writer,length):writer.write(b'partial');raise OSError('copy fixture')
   saver.shutil.copyfileobj=failed_copy
   try:
    try:saver.atomic_save(selected,destination)
    except OSError:pass
    else:raise AssertionError('expected write failure')
   finally:saver.shutil.copyfileobj=original_copy
   assert destination.read_bytes()==b'keep me' and not list(Path(tmp).glob('.SceneForge-*.tmp'))
   await ensure_review_tab(page,'[data-cap-close]');await dialog.locator('[data-cap-close]').click();assert not errors,errors;await browser.close();await client.aclose()
 print('PASS real MP4 Save As with mocked native choice, Unicode path and overwrite; native/browser cancel, failed write and retry preserve one rendered file; picker has click activation; SHA matches; no automatic downloads; route rejects destination injection; failed copy preserves old file')
if __name__=='__main__':asyncio.run(main())
