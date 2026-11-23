"""Production adapter/broker/ledger + actual frame node/DOM; extension wire and Gemini website are fixtures."""
import asyncio,base64,io,json,os,shutil,sys,tempfile,threading,zipfile
from pathlib import Path
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from playwright.async_api import async_playwright
from PIL import Image
import uvicorn
ROOT=Path(__file__).resolve().parents[2]
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
  server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=8840,log_level='error'));server_task=asyncio.create_task(server.serve());extension_task=None
  try:
   for _ in range(100):
    if server.started:break
    await asyncio.sleep(.05)
   async with async_playwright()as pw:
    browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);context=await browser.new_context()
    import httpx
    async def extension():
     async with httpx.AsyncClient(base_url='http://127.0.0.1:8840',headers={'Origin':bridge.origin,'X-SceneForge-Bridge':'1'},timeout=30)as client:
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
        assert ' '.join(job['request']['prompt'].split())in ' '.join((await tab.evaluate('sentText')).split())
        assert await tab.evaluate('sends')==1
        assert await tab.evaluate('refCount')==2
       reply=await client.post('/local-api/browser-bridge/gemini-result',json={**auth,'job_id':job['id'],'result':result});assert reply.status_code==200,reply.text
       await tab.close()
    extension_task=asyncio.create_task(extension())
    for _ in range(100):
     if bridge.gemini_browser.auto_status()['ready']:break
     if extension_task.done():await extension_task
     await asyncio.sleep(.05)
    assert bridge.gemini_browser.auto_status()['ready']
    assert len(service.accounts())==1 and service.selection()['available']and not service.engine().exists()
    page=await context.new_page();await page.goto('http://127.0.0.1:8840/workflow.html?demo=1');await page.wait_for_function('window.SFFrameImages&&window.SFMediaNodes')
    await page.evaluate('''async()=>{storeProject=async()=>{};SFProviderReceipts.persistIntent=async()=>{};const c=document.createElement('canvas');c.width=180;c.height=320;c.getContext('2d').fillRect(0,0,180,320);const source=c.toDataURL();project=blankProject();project.id='auto-e2e';project.source={poster:source};project.scenes=[sceneRecord(0,4,0,[source])];project.refs.product.images=[{image:source,name:'Product'}];const s=project.scenes[0];s.refsUsed=['product'];await SFFrameImages.prepare(s);render();await SFMediaNodes.open('frame',s.id);project.cloudJobs=[{id:'gchat-'+crypto.randomUUID(),kind:'image',provider:'gemini-chat',sceneId:s.id,state:'unknown',error:'LEGACY_NODE_ERROR'}];window.confirm=()=>false;await SFFrameImages.create([s]);if(project.cloudJobs.length!==1||project.cloudJobs[0].state!=='unknown')throw Error('Cancelled migration changed old receipt');window.confirm=()=>true;window.runResult=SFFrameImages.create([s]);runResult.catch(e=>window.runError=e.message);SFFrameImages.create([s]).catch(e=>window.duplicateBlocked=!!e.message);}''')
    for _ in range(140):
     if extension_task.done():await extension_task
     if await page.evaluate('project.scenes[0].frames.length===1||window.runError'):break
     await asyncio.sleep(.25)
    assert not await page.evaluate('window.runError'),await page.evaluate('window.runError')
    if extension_task.done():await extension_task
    assert await page.evaluate('project.cloudJobs.filter(j=>j.frameStudioVersion===164).length===1&&!project.scenes[0].approvedFrame')
    jobs=await page.evaluate('project.cloudJobs.filter(j=>j.frameStudioVersion===164).map(j=>j.id)');result=service.lookup(jobs[0]);assert result['state']=='done'and result['result']['scene_id']==await page.evaluate('project.scenes[0].id')
    assert Path(service.file(jobs[0]).path).read_bytes()==png and result['result']['download_variant']=='browser-authenticated'
    assert await page.evaluate('project.cloudJobs.at(-1).frameStudioVersion===164&&window.duplicateBlocked&&project.cloudJobs[0].state==="abandoned"&&project.cloudJobs[0].previousState==="unknown"')
    assert await page.locator('#node-frames [data-mn]').count()==0
    assert await page.locator('#frameStudioEditor').count()==1
    assert await page.locator('#modal [data-mn]').count()==0
    await page.screenshot(path='/tmp/frame-studio164.png')
    extension_task.cancel();await asyncio.gather(extension_task,return_exceptions=True);await browser.close()
    print('PASS E2E: no-code discovery -> production account/pool -> existing frame node -> production submit/ledger -> two refs in actual injected DOM -> PNG committed/imported to same scene; no SDK installed or automatic approval. Extension/network and Gemini site are fixtures; installed extension blocked by environment policy.')
  finally:
   if extension_task:extension_task.cancel();await asyncio.gather(extension_task,return_exceptions=True)
   await bridge.close();await service.close();server.should_exit=True;await server_task
asyncio.run(main())
