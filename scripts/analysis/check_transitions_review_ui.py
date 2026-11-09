"""Real native-sound joins: dissolve/fade, fixed timing, hold handles and tabbed review."""
import asyncio,base64,importlib,io,json,math,array,subprocess,sys,tempfile,zipfile
from pathlib import Path
import httpx
from fastapi import FastAPI
from PIL import Image
from playwright.async_api import async_playwright,expect
from review_ui_helpers import ensure_review_tab

async def main():
 html=Path('workflow.html').read_text()
 with tempfile.TemporaryDirectory()as td:
  root=Path(td);red=root/'red.mp4';blue=root/'blue.mp4'
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=red:s=90x160:r=30:d=2','-f','lavfi','-i','color=c=lime:s=90x160:r=30:d=1','-f','lavfi','-i','sine=frequency=440:duration=3','-filter_complex','[0:v][1:v]concat=n=2:v=1:a=0[v]','-map','[v]','-map','2:a','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(red)],check=True)
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=90x160:r=30:d=3','-f','lavfi','-i','sine=frequency=660:duration=3','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(blue)],check=True)
  package=root/'transition_runtime';package.mkdir();(package/'__init__.py').write_text('')
  with zipfile.ZipFile('/workspace/3/downloads/v46/SceneForge-Veo-v46-Source.zip')as archive:
   for name in ['local_jobs.py','schema.py']:(package/name).write_bytes(archive.read('local_engine/'+name))
  source=Path('local_engine/timeline_export.py');source=source if source.is_file()else Path('/workspace/3/veo-node-v46/local_engine/timeline_export.py')
  for name in ['timeline_export.py','export_save_as.py']:(package/name).write_bytes(source.with_name(name).read_bytes())
  sys.path.insert(0,td);renderer=importlib.import_module('transition_runtime.timeline_export');app=FastAPI();renderer.install_timeline_exports(app,root);client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local');models=[];ids=[]
  async with async_playwright()as p:
   browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1450,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));await page.add_init_script('window.showSaveFilePicker=undefined')
   async def route(r):
    if '/local-api/export/'in r.request.url:
     path=r.request.url.split('/local-api/')[1]
     if path=='export/timeline'and r.request.method=='POST':models.append(json.loads(r.request.post_data_buffer))
     response=await client.request(r.request.method,'/local-api/'+path,content=r.request.post_data_buffer,headers={'X-SceneForge-Local':'1','Content-Type':r.request.headers.get('content-type','application/json')})
     if path=='export/timeline'and r.request.method=='POST'and response.status_code==200:ids.append(response.json()['id'])
     await r.fulfill(status=response.status_code,body=response.content,headers={'Content-Type':response.headers.get('content-type','application/json')});return
    if '/local-api/'in r.request.url:await r.fulfill(json={});return
    await r.fulfill(body=html,content_type='text/html')
   await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFAudioNodes&&!!window.SFReferenceNodes')
   await page.evaluate("""async raws=>{project=blankProject();project.id='transition-review';const image='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';project.scenes=raws.map((raw,i)=>{const s=sceneRecord(i*2,(i+1)*2,i,[image]);s.approvedFrame='source';s.sourceFrame={id:'source',image,asset:'frame'};s.clipPlanning={mode:'legacy',continuity:false};assets.set('clip'+i,new File([Uint8Array.from(atob(raw),c=>c.charCodeAt(0))],'clip'+i+'.mp4',{type:'video/mp4'}));s.clips=[{id:'c'+i,asset:'clip'+i,part:'a',duration:2,version:1,frameId:'source',reviewDecision:{status:'accepted'}}];s.chosen={a:'c'+i};return s;});project.voiceOver={mode:'flow',duration:0};project.merge.ndInclude={voice:true,music:false,captions:false};project.merge.captions=false;document.body.classList.add('compactWorkspaceFrame');render();await SFAudioNodes.refresh();const n=document.querySelector('#node-merge');view.z=1;view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView();window.originalScenes=JSON.stringify(project.scenes);}""",[base64.b64encode(f.read_bytes()).decode()for f in [red,blue]])
   node=page.locator('#node-merge');await node.screenshot(path='/tmp/sceneforge-merge-node-v88.png');await node.locator('[data-nd=assembly-play]').click();dialog=page.locator('#anCaptionDialog');await expect(dialog).to_be_visible()
   assert await dialog.locator('[data-cap-panel]').all_text_contents()==['Ghép','Chữ','Logo','Xuất']
   assert await dialog.locator('[data-cap-panel-body]:visible').count()==1;await expect(dialog.locator('[data-cap-export]')).to_be_visible()
   async def geometry():return await dialog.locator('.anCaptionScreen').bounding_box()
   baseline=await geometry();await page.evaluate("window.reviewVideo=document.querySelector('video[data-cap-active]')")
   for key in ['captions','logo','export','assemble']:
    await dialog.locator('[data-cap-panel='+key+']').click();assert await page.evaluate("reviewVideo===document.querySelector('video[data-cap-active]')");box=await geometry();assert all(abs(box[k]-baseline[k])<.6 for k in ['x','y','width','height'])
   await dialog.locator('[data-cap-transition=dissolve]').click();await dialog.locator('[data-cap-transition-duration]').fill('0.6');await dialog.locator('[data-cap-play]').click()
   await page.wait_for_function('SFAudioNodes.getState().captionPreview.joined&&!SFAudioNodes.getState().captionPreview.buffering',timeout=60000)
   await page.wait_for_function("document.querySelector('video[data-cap-active]').currentTime>.1")
   if await page.evaluate('SFAudioNodes.getState().captionPreview.playing'):await dialog.locator('[data-cap-play]').click()
   async def video_file(rid,name):
    result=await client.get('/local-api/export/timeline/'+rid+'/file');assert result.status_code==200;file=root/name;file.write_bytes(result.content);return file
   preview=await video_file(ids[-1],'preview.mp4');assert models[-1]['width']==360 and len(models[-1]['clips'])==2
   assert models[-1]['clips'][0]['transition']=='dissolve'and models[-1]['clips'][0]['transitionAudio']=='cut'
   def pixel(file,at):
    raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(at),'-i',str(file),'-frames:v','1','-f','image2pipe','-vcodec','png','-threads','1','-']);im=Image.open(io.BytesIO(raw)).convert('RGB');return im.getpixel((im.width//2,im.height//2))
   center=pixel(preview,2);assert center[0]>70 and center[2]>70 and center[1]<25,center
   for at in [1.8,2.0,2.1,2.2]:assert pixel(preview,at)[1]<30,('Removed green source tail leaked',at,pixel(preview,at))
   assert pixel(preview,1.5)[0]>200 and pixel(preview,2.5)[2]>200
   def frequency(file,at):
    raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(at),'-i',str(file),'-t','0.1','-vn','-ac','1','-ar','48000','-f','s16le','-']);samples=array.array('h',raw);assert math.sqrt(sum(x*x for x in samples)/len(samples))>800;return sum(samples[i-1]<=0<samples[i]for i in range(1,len(samples)))/.1
   assert abs(frequency(preview,1.85)-440)<35 and abs(frequency(preview,2.05)-660)<35,'Native speech must not overlap or move'
   await dialog.locator('[data-cap-seek]').evaluate("(e)=>{e.value=2;e.dispatchEvent(new Event('input',{bubbles:true}))}");await page.wait_for_function('!SFAudioNodes.getState().captionPreview.buffering')
   count=len(models);await dialog.locator('[data-cap-joined]').click();await page.wait_for_function('!SFAudioNodes.getState().captionPreview.buffering');assert len(models)==count,'Same transition preview should be cached'
   await dialog.locator('[data-cap-final-rate]').select_option('1.5');assert not await page.evaluate('SFAudioNodes.getState().captionPreview.joined')
   await dialog.locator('[data-cap-joined]').click();await page.wait_for_function('SFAudioNodes.getState().captionPreview.joined',timeout=60000);assert abs(models[-1]['clips'][0]['transitionDuration']-.9)<.001
   await ensure_review_tab(page,'[data-cap-export-size]');await dialog.locator('[data-cap-export-size]').select_option('720')
   async def export(name):
    await dialog.locator('[data-cap-export]').click();await page.wait_for_function('!SFAudioNodes.getState().captionPreview.exportBusy',timeout=60000);assert await page.evaluate('SFAudioNodes.getState().captionPreview.exportReady'),await dialog.locator('[data-cap-export-status]').inner_text()
    async with page.expect_download()as download:await dialog.locator('[data-cap-browser-download]').click()
    target=root/name;await(await download.value).save_as(str(target));return target
   final=await export('dissolve.mp4');model=models[-1];assert abs(model['duration']-4/1.5)<.04 and abs(model['clips'][0]['transitionDuration']-.6)<.001
   middle=pixel(final,2/1.5);assert middle[0]>65 and middle[2]>65 and middle[1]<25,middle
   assert abs(frequency(final,1.2)-440)<40 and abs(frequency(final,1.45)-660)<40
   await dialog.locator('[data-cap-panel=assemble]').click();await dialog.locator('[data-cap-transition=fade]').click();fade=await export('fade.mp4');assert max(pixel(fade,2/1.5))<45
   await dialog.locator('[data-cap-panel=assemble]').click();await dialog.locator('[data-cap-transition=none]').click();assert await dialog.locator('[data-cap-transition-duration]').is_disabled()
   assert await page.evaluate('originalScenes===JSON.stringify(project.scenes)')
   await dialog.locator('aside .anReviewBody').evaluate('e=>e.scrollTop=0');await dialog.screenshot(path='/tmp/sceneforge-review-v88.png')
   await dialog.locator('[data-cap-close]').click();assert not errors,errors;await browser.close();await client.aclose()
 print('PASS tabbed compact review and fixed video geometry; real dissolve/fade preview+720p output; native sound stays at cut; removed tail does not leak; final speed and effect length match; preview cache invalidates; original scenes unchanged')
if __name__=='__main__':asyncio.run(main())
