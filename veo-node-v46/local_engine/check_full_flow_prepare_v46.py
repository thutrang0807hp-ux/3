"""One complete fixture workflow: reuse project, preset settings, upload, attach exact image, prompt, stop."""
import asyncio,base64,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from PIL import Image
from playwright.async_api import async_playwright
from .simple_flow import SimpleFlow
from .vault import Vault
from .request_ledger import RequestLedger
from .check_flow_settings_v46 import FIXTURE
from .flow_background_session import BackgroundFlowSession

async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);reference=root/'source.png';Image.new('RGB',(90,160),'green').save(reference);raw=reference.read_bytes()
  vault=Vault(root);ledger=RequestLedger(root);service=SimpleFlow(root,vault,ledger)
  service.account_bridge=SimpleNamespace(selection=lambda:{'available':True,'token':'fixture','account_id':'account'})
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
   await page.route('https://media.fixture/**',lambda r:r.fulfill(body=raw,content_type='image/png'))
   extra='''<style>.tile .more{visibility:hidden}.tile:hover .more{visibility:visible}</style><script>window.chosen='';window.picked='old-video';window.wrong=false;settings.model='Omni 1.1 Flash';drawSettings();</script>
   <button aria-label="More options" onclick="window.wrong=true">Header menu</button>
   <article data-media-id=old><img src=https://media.fixture/old.png></article>
   <input type=file accept="image/*" hidden onchange="const card=document.createElement('article');card.className='tile';card.dataset.mediaId='new';card.innerHTML='<img src=https://media.fixture/new.png><button class=more type=button aria-label=&quot;More options&quot;>more_vert</button>';card.querySelector('button').onclick=()=>{window.chosen='new';document.querySelector('#actions').hidden=false};document.body.append(card)">
   <div id=actions role=menu hidden><button type=button role=menuitem onclick="document.querySelector('#actions').hidden=true;document.querySelector('#picker').hidden=false">Add to prompt</button></div>
   <div id=picker role=dialog hidden><input placeholder="Search assets"><button type=button data-media-id=old-video onclick="picked='old-video'"><img width=40 height=70 src=https://media.fixture/video-thumb.png>Old Video</button><button type=button data-media-id=new onclick="picked='new'"><img width=40 height=70 src=https://media.fixture/new.png>New Image</button><button type=button onclick="document.querySelector('#refs').innerHTML='<img src=https://media.fixture/'+(picked==='new'?'new':'wrong')+'.png>';document.querySelector('#picker').hidden=true;settings.ingredients='frames';drawSettings()">Add to prompt</button></div>'''
   await page.set_content(FIXTURE+extra)
   await page.wait_for_function('Array.from(document.images).every(e=>e.complete)')
   async def restore():service.page=page;service.project='https://flow.google.com/project/fixture'
   service.restore=restore;service.assert_ready=AsyncMock();service.disconnect_browser=AsyncMock()
   await service.start_upload_only({'reference':{'mime_type':'image/png','data':base64.b64encode(raw).decode()},'room_id':'workflow-room','scene_id':'scene-2','part':'b','selection_token':'fixture','prepare_prompt':True,'prompt':'Move the exact new image slowly.'})
   await asyncio.wait_for(service.task,25)
   report=service.upload_report
   assert report['state']=='prompt_ready',report
   assert report['uploaded_asset']['media_id']=='new'and report['attached_asset_key']==report['uploaded_asset']['key']
   assert await page.evaluate('chosen')=='new'and await page.evaluate('picked')=='new'and not await page.evaluate('wrong')
   state=await page.evaluate('settings')
   assert [state[k]for k in ('video','ingredients','ratio','outputs','model')]==['video','ingredients','9:16','x1','Veo 3.1 - Lite']
   assert report['verified_settings']['outputs']==1 and report['verified_settings']['duration_seconds']==8
   assert await page.locator('textarea').input_value()=='Move the exact new image slowly.'
   assert await page.evaluate('sent')==0 and ledger.recent()==[]
   assert report['picker_check']['matching_views']==1
   # Verify the existing account+workflow project binding does not create a
   # project per image. Reopen the same mapping twice, exactly one creation.
   created=[]
   project=await browser.new_page()
   await project.expose_function('createdOnce',lambda:created.append(True))
   async def flow(r):
    html='<button onclick="createdOnce();history.pushState({},\'\',\'/project/kept-project\')">New project</button>'if r.request.url=='https://flow.google.com/'else'<p>Existing project</p>'
    await r.fulfill(body=html,content_type='text/html')
   await project.route('https://flow.google.com/**',flow)
   await project.goto('https://flow.google.com/')
   session=BackgroundFlowSession(root,None,'fixture@invalid');session.page=project;session.assert_ready=AsyncMock()
   await session.ensure_project(vault,'account','workflow-room')
   first=project.url
   await session.ensure_project(vault,'account','workflow-room')
   assert project.url==first=='https://flow.google.com/project/kept-project'and len(created)==1
   await browser.close()
 print('PASS complete Flow preparation: same account/workflow reuses one project; full settings repaired and re-read; scoped More menu and exact new image picker; attachment mode reset repaired; correct prompt; zero Generate.')
if __name__=='__main__':asyncio.run(main())
