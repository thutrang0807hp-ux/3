"""Production adapter/broker/ledger + actual frame node/DOM; extension wire and Gemini website are fixtures."""
import asyncio,base64,io,json,os,re,shutil,sys,tempfile,threading,zipfile
from pathlib import Path
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from playwright.async_api import async_playwright
from PIL import Image
import uvicorn
ROOT=Path(__file__).resolve().parents[2]
PORT=int(os.environ.get('SCENEFORGE_TEST_PORT','8840'))
class Vault:
 def __init__(self):self.lock=threading.RLock();self.tables={};self.secrets={}
 def secret(self,k):return self.secrets.get(k)
 def set_secret(self,k,v):self.secrets[k]=v
 def rows(self,table):return [dict(v)for v in self.tables.get(table,{}).values()]
 def put(self,table,row):self.tables.setdefault(table,{})[row['id']]=dict(row)
 def delete(self,table,key):self.tables.get(table,{}).pop(key,None)
 def delete_secret(self,k):self.secrets.pop(k,None)
async def main():
 with tempfile.TemporaryDirectory()as tmp:
  folder=Path(tmp);pkg=folder/'production';(pkg/'local_engine').mkdir(parents=True)
  with zipfile.ZipFile(ROOT/'downloads/v46/SceneForge-Veo-v46-Source.zip')as z:
   for n in z.namelist():
    if n.startswith('local_engine/')and n.endswith('.py')and '/'not in n[len('local_engine/'):]: (pkg/n).write_bytes(z.read(n))
  for p in (ROOT/'veo-node-v46/local_engine').glob('*.py'):shutil.copyfile(p,pkg/'local_engine'/p.name)
  shutil.copytree(ROOT/'veo-node-v46/scripts/browser-extension',pkg/'scripts/browser-extension')
  sys.path.insert(0,str(pkg))
  from local_engine.gemini_chat import install_gemini_chat
  from local_engine.browser_bridge import BrowserBridge,EXCHANGE
  from local_engine.request_ledger import RequestLedger
  data=folder/'data';data.mkdir();vault=Vault();(data/'ledger').mkdir();ledger=RequestLedger(data/'ledger');app=FastAPI();service=install_gemini_chat(app,vault,data,ledger);bridge=BrowserBridge(app,service,SimpleNamespace())
  @app.middleware('http')
  async def guard(request,call_next):return await bridge.extension_request(request,call_next)if request.url.path in EXCHANGE else await call_next(request)
  app.mount('/',StaticFiles(directory=str(ROOT),html=True))
  buf=io.BytesIO();Image.new('RGB',(360,640),'#325977').save(buf,'PNG');png=buf.getvalue();image=base64.b64encode(png).decode()
  fixture='''<rich-textarea><div contenteditable="true" role="textbox"></div></rich-textarea><input type="file" multiple><button class="send-button" aria-label="Send message">Send</button><script>document.querySelector('input').onchange=e=>{for(const f of e.target.files){const n=document.createElement('div');n.className='file-preview';n.textContent=f.name;document.body.append(n);}};document.querySelector('button').onclick=()=>{window.sends=(window.sends||0)+1;window.refCount=document.querySelector('input').files.length;window.sentText=document.querySelector('[contenteditable]').innerText;const n=document.createElement('model-response');n.innerHTML='<generated-image><img src="data:image/png;base64,IMAGE"></generated-image>';document.body.append(n);};</script>'''.replace('IMAGE',image)
  server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,log_level='error'));server_task=asyncio.create_task(server.serve());extension_task=None
  try:
   for _ in range(100):
    if server.started:break
    await asyncio.sleep(.05)
   async with async_playwright()as pw:
    browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);context=await browser.new_context()
    import httpx
    async def extension():
     async with httpx.AsyncClient(base_url=f'http://127.0.0.1:{PORT}',headers={'Origin':bridge.origin,'X-SceneForge-Bridge':'1'},timeout=30)as client:
      found=(await client.post('/local-api/browser-bridge/gemini-discover',json={'installation_id':'12345678-1234-4234-8234-123456789abc','version':'1.7.1'})).json()
      assert 'code'not in found and 'submission'not in found
      auth={'id':found['relay']['id'],'key':found['relay']['browser_key']}
      while True:
       packet=(await client.post('/local-api/browser-bridge/gemini-poll',json=auth)).json()
       if not packet.get('job'):continue
       job=packet['job'];tab=await context.new_page();await tab.set_content(fixture);await tab.add_script_tag(path=str(ROOT/'veo-node-v46/scripts/browser-extension/gemini-tab.js'))
       if job['request'].get('engine')=='frame-studio':
        await tab.add_script_tag(path=str(ROOT/'veo-node-v46/scripts/browser-extension/studio-gemini-original.js'));await tab.add_script_tag(path=str(ROOT/'veo-node-v46/scripts/browser-extension/frame-studio-tab.js'))
        result=await tab.evaluate('(r)=>SFStudioBridge.run(r)',{**job['request'],'request_id':job['id']})
       else:result=await tab.evaluate('(r)=>sceneForgeGeminiTab(r)',{**job['request'],'request_id':job['id']})
       if job['request']['operation']=='generate':
        assert job['request'].get('engine')=='frame-studio'
        assert job['request']['prompt']==await page.evaluate('SFFrameImages.prompt(project.scenes[0])')
        assert '200 g' in job['request']['prompt'] and '9 cm' in job['request']['prompt']
        assert 'Weight and capacity alone do not establish exact physical dimensions.' in job['request']['prompt']
        assert 'giảm 50%' not in job['request']['prompt']
        keys=re.findall(r'^## \[([A-Z_]+)\]',job['request']['prompt'],re.M)
        assert len(keys)==len(set(keys)) and keys==await page.evaluate('SFUniversalFrame.keys')
        assert job['request']['prompt'].startswith('# UNIVERSAL REFERENCE IMAGE EDIT V'+await page.evaluate('SFUniversalFrame.version'))
        body=re.sub(r'^## \[[A-Z_]+\]\s*$','',job['request']['prompt'],flags=re.M)
        assert not re.search(r'\[[A-Z][A-Z0-9_]*\]',body)
        assert 'IMAGE EDIT CONTRACT' not in job['request']['prompt'] and 'FINAL FRAME EDIT SETTINGS' not in job['request']['prompt']
        assert 'Mở nắp sản phẩm' not in job['request']['prompt'] and 'CLOUD MOUNTAIN' not in job['request']['prompt']
        assert ' '.join(job['request']['prompt'].split())in ' '.join((await tab.evaluate('sentText')).split())
        assert await tab.evaluate('sends')==1
        assert await tab.evaluate('refCount')==len(job['request']['references'])
        if job['request'].get('engine')=='frame-studio':
         assert job['request']['ratio'] in await tab.evaluate('sentText')
       reply=await client.post('/local-api/browser-bridge/gemini-result',json={**auth,'job_id':job['id'],'result':result});assert reply.status_code==200,reply.text
       await tab.close()
    extension_task=asyncio.create_task(extension())
    for _ in range(100):
     if bridge.gemini_browser.auto_status()['ready']:break
     if extension_task.done():await extension_task
     await asyncio.sleep(.05)
    assert bridge.gemini_browser.auto_status()['ready']
    assert len(service.accounts())==1 and service.selection()['available']and not service.engine().exists()
    page=await context.new_page();await page.goto(f'http://127.0.0.1:{PORT}/workflow.html?demo=1');await page.wait_for_function('window.SFFrameImages&&window.SFMediaNodes')
    if os.environ.get('SCENEFORGE_TEST_BACKGROUND')=='1':
     # Visibility seam only: actual Win32 tray/controller hiding is tested separately/on Windows.
     await page.evaluate("""async()=>{closeChooser();storeProject=async()=>{};SFProviderReceipts.persistIntent=async()=>{};const canvas=document.createElement('canvas');canvas.width=180;canvas.height=320;const source=canvas.toDataURL();project=blankProject();project.id='background-two-scenes';project.source={poster:source};project.productScript={brief:{name:'Product',facts:'Khối lượng tịnh: 200 g; chiều cao: 9 cm'}};project.refs.product.images=[{id:'same-product',name:'Product',image:source}];project.scenes=[sceneRecord(0,4,0,[source]),sceneRecord(4,8,1,[source])];for(const sc of project.scenes){sc.refsUsed=['product'];await SFFrameImages.prepare(sc);}Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});Object.defineProperty(document,'visibilityState',{configurable:true,get:()=> 'hidden'});document.dispatchEvent(new Event('visibilitychange'));window.backgroundRun=SFFrameImages.create(project.scenes);window.backgroundRun.catch(e=>window.backgroundError=e.message);}""")
     for _ in range(180):
      if extension_task.done():await extension_task
      if await page.evaluate("project.scenes.every(s=>s.frames.length===1)||window.backgroundError"):break
      await asyncio.sleep(.25)
     assert not await page.evaluate('window.backgroundError'),await page.evaluate('window.backgroundError')
     assert await page.evaluate("document.hidden&&project.scenes.every(s=>s.frames.length===1)&&SFFrameImages.runState().completed===2&&!SFFrameImages.isRunning()")
     jobs=await page.evaluate("project.cloudJobs.filter(j=>j.frameStudioVersion===164).map(j=>({id:j.id,scene:j.sceneId}))")
     assert len(jobs)==2
     for j in jobs:assert service.lookup(j['id'])['result']['scene_id']==j['scene']
     assert bridge.gemini_browser.auto_status()['ready']
     extension_task.cancel();await asyncio.gather(extension_task,return_exceptions=True);await browser.close()
     print('PASS visibility-hidden production frame queue: two original job IDs, extension dispatch, correct per-scene image import, no resend, broker stays ready. Hidden visibility is simulated, not native Windows WebView2 occlusion.')
     return
    await page.evaluate('''async()=>{closeChooser();storeProject=async()=>{};SFProviderReceipts.persistIntent=async()=>{};const c=document.createElement('canvas');c.width=180;c.height=320;c.getContext('2d').fillRect(0,0,180,320);const source=c.toDataURL();project=blankProject();project.id='auto-e2e';project.source={poster:source};project.productScript={brief:{name:'Product brief title not printed',facts:['NƯỚC HOA Ô TÔ GLYTWIN 200G – CLOUD MOUNTAIN SERIES No.5','Trọng lượng lớn 200g, sử dụng bền bỉ trong thời gian dài.','Mở nắp sản phẩm.','Khối lượng tịnh: 200 g','Kích thước: cao 9 cm, đường kính 7 cm','Ưu đãi: giảm 50%'].join(String.fromCharCode(10))}};project.scenes=[sceneRecord(0,4,0,[source])];project.refs.product.images=[{image:source,name:'Product'}];const s=project.scenes[0];s.refsUsed=['product'];s.framePromptOverride=['IMAGE EDIT CONTRACT v2','[SCENE DESCRIPTION]','Legacy app-generated instructions'].join(String.fromCharCode(10));s.frameManualInput=SFPromptPipeline.snapshot(s,'image');await SFFrameImages.prepare(s);if(s.framePromptOverride||!s.framePromptBackups?.some(b=>b.text.startsWith('IMAGE EDIT CONTRACT')))throw Error('Managed V2 was not replaced/archived');render();await SFMediaNodes.open('frame',s.id);project.cloudJobs=[{id:'gchat-'+crypto.randomUUID(),kind:'image',provider:'gemini-chat',sceneId:s.id,state:'unknown',error:'LEGACY_NODE_ERROR'}];window.confirm=()=>false;await SFFrameImages.create([s]);if(project.cloudJobs.length!==1||project.cloudJobs[0].state!=='unknown')throw Error('Cancelled migration changed old receipt');window.confirm=()=>true;window.runResult=SFFrameImages.create([s]);runResult.catch(e=>window.runError=e.message);SFFrameImages.create([s]).catch(e=>window.duplicateBlocked=!!e.message);}''')
    for _ in range(140):
     if extension_task.done():await extension_task
     if await page.evaluate('project.scenes[0].frames.length===1||window.runError'):break
     await asyncio.sleep(.25)
    assert not await page.evaluate('window.runError'),await page.evaluate('window.runError')
    if extension_task.done():await extension_task
    assert await page.evaluate('project.cloudJobs.filter(j=>j.frameStudioVersion===164).length===1&&!project.scenes[0].approvedFrame')
    jobs=await page.evaluate('project.cloudJobs.filter(j=>j.frameStudioVersion===164).map(j=>j.id)');result=service.lookup(jobs[0]);assert result['state']=='done'and result['result']['scene_id']==await page.evaluate('project.scenes[0].id')
    assert Path(service.file(jobs[0]).path).read_bytes()==png and result['result']['download_variant']=='browser-authenticated'
    (Path('/tmp')/'frame-prompt-v51.txt').write_text(await page.evaluate('project.cloudJobs.at(-1).prompt'))
    assert await page.evaluate('project.cloudJobs.at(-1).frameStudioVersion===164&&window.duplicateBlocked&&project.cloudJobs[0].state==="abandoned"&&project.cloudJobs[0].previousState==="unknown"')
    assert await page.locator('#node-frames [data-mn]').count()==0
    # Exercise real per-scene controls and attachment packing without sending another request.
    await page.evaluate("""()=>{const other=sceneRecord(4,8,1,[project.source.poster]);other.refsUsed=['product'];project.scenes.push(other);}""")
    await page.click('[data-studio="ref-mode"][data-role="person"][data-mode="keep"]')
    await page.click('[data-studio="ref-mode"][data-role="background"][data-mode="custom"]')
    await page.locator('[data-studio-upload="background"]').set_input_files({'name':'interior.png','mimeType':'image/png','buffer':png})
    await page.wait_for_function("project.scenes[0].frameReferenceChoices.background.images?.length===1")
    await page.wait_for_function("!SFFrameImages.isRunning()")
    await page.evaluate("""async()=>{const [s,other]=project.scenes;const refs=await SFPromptPipeline.generationRefs(s,null,true);if(refs.length!==3)throw Error('Wrong attachment count '+refs.length);if(refsFor(s).includes('person')||!refsFor(s).includes('background'))throw Error('Wrong roles');if(other.frameReferenceChoices)throw Error('Leaked scene override');if(!SFFrameImages.prompt(s).includes('Replace only the selected environment/background using '+SFPromptPipeline.imageBindings(s).find(b=>b.role==='background').code))throw Error('Prompt missed background');}""")
    await page.click('[data-studio="tab"][data-tab="prompt"]')
    await page.wait_for_function("document.querySelector('#studioEnglish').offsetParent!==null")
    assert await page.locator('#studioEnglish').input_value()
    await page.click('[data-studio="tab"][data-tab="refs"]')
    await page.wait_for_function("document.querySelector('#studioResultSize').textContent.includes('360 × 640')")
    assert '9:16' in await page.locator('#studioResultSize').inner_text()
    await page.locator('#studioCompare').fill('70')
    assert '70%' in await page.locator('.sfStudioResult').get_attribute('style')
    await page.locator('#modalContent').evaluate('(el)=>el.scrollTop=0')
    await page.screenshot(path='/tmp/frame-studio165-editor.png')
    await page.click('[data-studio="ref-mode"][data-role="product"][data-mode="keep"]')
    await page.wait_for_function("!SFFrameImages.isRunning()")
    assert await page.evaluate("!refsFor(project.scenes[0]).includes('product')&&!productFrameContext(project.scenes[0])?.visible_in_scene")
    await page.click('[data-studio="ref-mode"][data-role="product"][data-mode="shared"]')
    await page.wait_for_function("!SFFrameImages.isRunning()")
    assert await page.evaluate("refsFor(project.scenes[0]).includes('product')&&project.cloudJobs.filter(j=>j.frameStudioVersion===164).length===1")
    await page.click('[data-studio="reset-refs"]')
    await page.wait_for_function("!project.scenes[0].frameReferenceChoices&&!SFFrameImages.isRunning()")
    assert await page.evaluate("!project.scenes[1].frameReferenceChoices&&project.scenes[0].frames.length===1")
    assert await page.locator('#frameStudioEditor').count()==1
    assert await page.locator('[data-studio-progress] progress').first.get_attribute('value')=='1'
    assert await page.locator('#modal [data-mn]').count()==0
    await page.screenshot(path='/tmp/frame-studio164.png')
    # Actual ratio control must update both the sent prompt and the backend-to-browser ratio.
    assert await page.evaluate("project.cloudJobs.at(-1).requestedOutput.width===1080&&SFFrameImages.prompt(project.scenes[0]).includes('1080 x 1920')")
    assert (await page.locator('.sfStudioCompare').bounding_box())['height']>=320
    await page.click('[data-studio="preview-mode"][data-view="result"]')
    assert await page.locator('.sfStudioCompare').get_attribute('data-view')=='result'
    await page.click('[data-studio="large"]')
    assert await page.locator('#studioLightbox').evaluate('(el)=>el.open')
    await page.keyboard.press('Escape')
    await page.wait_for_function("!document.querySelector('#studioLightbox')&&document.querySelector('#modal').open")
    await page.click('[data-studio="tab"][data-tab="prompt"]')
    original_prompt=await page.locator('#studioEnglish').input_value()
    manual_prompt='Use image 1 for the car scene.\nReplace the product with image 2.\nKeep its exact cap and label; output 1080 x 1920.'
    await page.locator('#studioEnglish').fill(manual_prompt)
    await page.click('[data-studio="save-prompt"]')
    assert await page.locator('#studioEnglish').input_value()==manual_prompt
    await page.locator('#studioEnglish').fill(manual_prompt)
    await page.click('[data-studio="simple-prompt"]')
    assert await page.locator('#studioEnglish').input_value()==original_prompt
    await page.click('[data-studio="restore-prompt"]')
    assert await page.locator('#studioEnglish').input_value()==manual_prompt
    await page.click('[data-studio="simple-prompt"]')
    await page.evaluate("""async()=>{const s=project.scenes[0],count=project.cloudJobs.length;s.framePromptOverride='Edit [SCENE_DESCRIPTION] and return [OUTPUT_RESOLUTION].';s.frameManualInput=SFPromptPipeline.snapshot(s,'image');let blocked=false;try{await SFFrameImages.create([s],{regenerate:true});}catch(e){blocked=e.message.includes('chưa điền');}if(!blocked||project.cloudJobs.length!==count)throw Error('Unfilled placeholder dispatched');delete s.framePromptOverride;delete s.frameManualInput;await SFFrameImages.prepare(s);}""")
    await page.locator('.sfStudioOutputDetails summary').click()
    await page.select_option('#studioOutputPreset','landscape')
    await page.wait_for_function("project.scenes[0].frameOutput?.width===1920&&!SFFrameImages.isRunning()")
    assert await page.evaluate("SFFrameImages.prompt(project.scenes[0]).includes('1920 x 1080')")
    await page.locator('.sfStudioOutputDetails summary').click()
    await page.select_option('#studioOutputPreset','shared')
    await page.wait_for_function("!project.scenes[0].frameOutput&&!SFFrameImages.isRunning()")
    await page.click('#modal [data-action="close-modal"]')
    await page.evaluate("project.refs.product.images[0].id='legacy-red';project.scenes[0].referenceImages={product:['legacy-red']};project.refs.product.images.push({id:'primary-blue',name:'Blue product primary',image:'data:image/png;base64,"+image+"'});render();")
    await page.click('[data-studio="common"]')
    await page.select_option('#studioCommonPreset','landscape')
    await page.fill('#studioCommonRequest','Replace visible hands with natural feminine hands and short nude nails; keep the grip.')
    await page.check('#studioCommonPerson')
    await page.select_option('#studioProductPrimary','primary-blue')
    await page.click('[data-studio="common-none"]')
    await page.locator('[data-studio-scope]').first.check()
    await page.click('[data-studio="save-common"]')
    await page.wait_for_function("project.frameStudioDefaults?.sceneIds?.length===1")
    assert await page.evaluate("project.cloudJobs.filter(j=>j.frameStudioVersion===164).length===1")
    await page.evaluate("""async()=>{const [s,other]=project.scenes;await SFFrameImages.prepare(s);if(SFFrameSettings.output(other).ratio!=='9:16'||SFFrameSettings.output(s).ratio!=='16:9')throw Error('Scope leaked');if(!SFFrameImages.prompt(s).includes('short nude nails')||!SFFrameImages.prompt(s).includes('Do not retain conflicting features from the original product.'))throw Error('Missing edit instructions');if(SFFrameImages.prompt(other).includes('short nude nails'))throw Error('Shared request leaked');if(s.frameReferenceChoices?.person?.mode==='keep')throw Error('Explicit bulk person edit did not clear keep');const count=project.cloudJobs.length;window.runResult=SFFrameImages.create([s],{regenerate:true});window.runResult.catch(e=>window.runError=e.message);if(project.cloudJobs.length>count+1)throw Error('Duplicate dispatch');}""")
    for _ in range(140):
     if extension_task.done():await extension_task
     if await page.evaluate('project.scenes[0].frames.length===2||window.runError'):break
     await asyncio.sleep(.25)
    assert not await page.evaluate('window.runError'),await page.evaluate('window.runError')
    assert await page.evaluate("SFPromptContract.orderedImages(sceneReference(project.scenes[0],'product').images)[0].id==='primary-blue'&&project.cloudJobs.at(-1).referenceManifest.find(r=>r.role==='product').id==='primary-blue'&&project.scenes[0].frames.at(-1).referenceManifest.find(r=>r.role==='product').id==='primary-blue'")
    assert await page.evaluate("project.scenes[0].frames.length===2&&project.cloudJobs.at(-1).requestedOutput.ratio==='16:9'")
    await page.evaluate("SFMediaNodes.open('frame',project.scenes[0].id)")
    await page.wait_for_function("document.querySelector('#studioOutputNotice')?.textContent.includes('1920 × 1080')")
    await page.locator('#modalContent').evaluate('(el)=>el.scrollTop=0')
    await page.screenshot(path='/tmp/frame-studio166-editor.png')
    assert await page.evaluate("sceneReference(project.scenes[0],'product').images.length===1")
    await page.evaluate("""()=>{const sc=project.scenes[0];const saved=sc.frameOutput;sc.frameOutput={width:1080,height:1080};if(SFFrameSettings.output(sc).ratio!=='1:1')throw Error('Scene output did not win');sc.frameOutput=saved;const request=sc.frameUseCommon;sc.frameUseCommon=false;if(SFFrameSettings.input(sc).request)throw Error('Common optout ignored');sc.frameUseCommon=request;}""")
    await page.evaluate("""()=>{const sc=project.scenes[0],c=project.frameStudioDefaults,key=c.productPrimary;c.productPrimary='missing-product';let blocked=false;try{SFFrameRefs.validate(sc);}catch(e){blocked=e.message.includes('Ảnh sản phẩm chính');}if(!blocked||sceneReference(sc,'product').images.length)throw Error('Missing primary silently fell back');c.productPrimary=key;const previous=sc.frameReferenceChoices?.product;sc.frameReferenceChoices??={};sc.frameReferenceChoices.product={mode:'custom',images:[{id:'custom-red',name:'Explicit per-scene red',image:project.source.poster}]};if(sceneReference(sc,'product').images[0].id!=='custom-red')throw Error('Common primary overrode explicit custom image');if(previous)sc.frameReferenceChoices.product=previous;else delete sc.frameReferenceChoices.product;}""")
    # Migration does not invalidate an old, already submitted image when no settings changed.
    await page.evaluate("""async()=>{const sc=project.scenes[1];delete sc.frameEditPolicy;delete sc.framePromptVersion;delete sc.frameProductFactsVersion;project.promptPipeline.records[sc.id+':image:']={input:SFPromptPipeline.snapshot(sc,'image'),applied:true,localRecipe:true,template:SFPromptContract.version,namePolicy:'reference-only-v1',result:{promptFrame:{en:'OLD SAVED FRAME PROMPT',vi:'Old'}}};project.cloudJobs.push({id:'old-pending',sceneId:sc.id,kind:'image',frameStudioVersion:164,state:'submitted'});const before=await directSignature(sc,'','image');await SFFrameImages.prepare(sc);if(sc.frameEditPolicy||await directSignature(sc,'','image')!==before)throw Error('Pending signature changed on update');project.cloudJobs.pop();}""")
    await page.evaluate("project.scenes[0].frameOutput={width:1080,height:1080};closeModal();render();fit(false);")
    await page.select_option('#studioNodeOutputPreset','landscape')
    await page.click('[data-studio="save-node-output"]')
    await page.wait_for_function("project.frameOutputDefault?.width===1920")
    assert await page.evaluate("SFFrameSettings.output(project.scenes[0]).ratio==='1:1'&&SFFrameSettings.output(project.scenes[1]).ratio==='16:9'&&project.frameStudioDefaults.request.includes('nude nails')&&project.cloudJobs.filter(j=>j.frameStudioVersion===164).length===2")
    extension_task.cancel();await asyncio.gather(extension_task,return_exceptions=True);await browser.close()
    print('PASS V5.1 replaces managed V2 without concatenation; exact block order and all six filled slots reach original sender; unfilled manual slots blocked before job creation; unchanged attachments/API/UI, exact supplied template regression, manual prompts and reset/restore. .168 physical script facts reach actual sender without offers or invented dimensions; exact primary survives legacy filter, missing primary blocks, custom product retained and reference manifest saved. .166 output settings (portrait/landscape through actual sender), scoped shared edits, primary product order and single-image default, legacy pending signature, actual result-size notice. E2E: no-code discovery -> production account/pool -> existing frame node -> production submit/ledger -> two refs in actual injected DOM -> PNG committed/imported to same scene; no SDK installed or automatic approval. Extension/network and Gemini site are fixtures; installed extension blocked by environment policy.')
  finally:
   if extension_task:extension_task.cancel();await asyncio.gather(extension_task,return_exceptions=True)
   await bridge.close();await service.close();server.should_exit=True;await server_task
asyncio.run(main())
