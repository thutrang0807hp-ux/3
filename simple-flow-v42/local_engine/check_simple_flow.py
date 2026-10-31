"""Intercepted Chromium: explicit checkpoints, one clip, download -> durable result."""
import asyncio,base64,hashlib,io,tempfile,subprocess,uuid
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright
from fastapi import HTTPException
from .vault import Vault
from .request_ledger import RequestLedger
from .flow_provider import FlowProvider
from .simple_flow import SimpleFlow,MODEL

async def pending(service,kind):
 for _ in range(300):
  if service.pending and service.pending['kind']==kind:return service.pending['id']
  if service.task and service.task.done():raise AssertionError((kind,service.state,service.message))
  await asyncio.sleep(.02)
 raise AssertionError(('timeout',kind,service.state,service.message))
async def advance(s,kind):await s.respond({'id':await pending(s,kind),'accept':True})
async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);vault=Vault(root);ledger=RequestLedger(root)
  from .library import Library
  from .storage_jobs import StorageJobs
  library=Library(root);ledger.storage=StorageJobs(library,ledger,root)
  def forbidden(*a,**k):raise AssertionError('No engine or relay permitted')
  provider=FlowProvider(vault,root,ledger,forbidden);s=SimpleFlow(root,vault,ledger);provider.simple=s
  assert s.status()['selection']['available']is False and s.context is None and s.pw is None
  movie=root/'fixture.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=90x160:d=8','-c:v','libx264','-pix_fmt','yuv420p','-y',str(movie)],check=True)
  encoded=base64.b64encode(movie.read_bytes()).decode()
  html='''<script>window.WIZ_global_data={oPEP7c:'fixture@invalid'};window.sent=0;</script><input type=file accept="image/*" hidden><textarea></textarea><button onclick="window.sent++">Generate</button><a id=download download=clip.mp4 href="data:video/mp4;base64,MP4">Download</a>'''.replace('MP4',encoded)
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=await browser.new_context(accept_downloads=True)
   await context.route('**/*',lambda r:r.fulfill(status=200,content_type='text/html; charset=utf-8',body=html))
   page=await context.new_page();await page.goto('https://flow.google.com/project/fixture')
   s.context=context;s.page=page;s.email='fixture@invalid';s.connected=True;s.project=s.project_url()
   image=io.BytesIO();Image.new('RGB',(90,160),'green').save(image,format='PNG')
   body={'request_id':'flow-'+str(uuid.uuid4()),'kind':'video','model':MODEL,'prompt':'She waves.','references':[{'mime_type':'image/png','data':base64.b64encode(image.getvalue()).decode()}],'room_id':'room','scene_id':'scene-1','confirm_send':True,'selection_token':s.token}
   assert provider.status()['connection_method']=='simple_flow'
   await provider.submit(body);original=s.task
   await pending(s,'project');await provider.submit(body);assert s.task is original
   try:await s.respond({'id':'stale','accept':True})
   except HTTPException:pass
   else:raise AssertionError('Stale confirmation admitted')
   await advance(s,'project');await pending(s,'image')
   assert await page.locator('input').evaluate('(e)=>e.files[0].name.endsWith(".png")')
   assert await page.locator('textarea').input_value()==''and await page.evaluate('window.sent')==0
   await advance(s,'image');await pending(s,'submit')
   assert await page.locator('textarea').input_value()=='She waves.'and await page.evaluate('window.sent')==0
   other={**body,'request_id':'flow-'+str(uuid.uuid4())}
   try:await provider.submit(other)
   except HTTPException as exc:assert exc.status_code==409
   else:raise AssertionError('Second active clip admitted')
   await advance(s,'submit')
   for _ in range(100):
    if s.state=='waiting_download':break
    await asyncio.sleep(.02)
   assert await page.evaluate('window.sent')==1
   await page.locator('#download').click();await pending(s,'result')
   assert provider.lookup(body['request_id'])['state']!='done'
   await advance(s,'result');await s.task
   result=provider.lookup(body['request_id']);assert result['state']=='done',result
   assert result['result']['scene_id']=='scene-1'and Path(provider.file(body['request_id']).path).read_bytes()==movie.read_bytes()
   assert result['result']['sha256']==hashlib.sha256(movie.read_bytes()).hexdigest()
   await provider.submit(body);assert await page.evaluate('window.sent')==1
   # Cancel before click: terminal failure and zero extra click.
   cancel={**body,'request_id':'flow-'+str(uuid.uuid4())};await provider.submit(cancel);await pending(s,'project');await s.stop()
   assert provider.lookup(cancel['request_id'])['state']=='failed'and await page.evaluate('window.sent')==1
   # Cancel after dispatch: unknown remains blocked until an explicit review.
   uncertain={**body,'request_id':'flow-'+str(uuid.uuid4())};await provider.submit(uncertain)
   for kind in ('project','image','submit'):await advance(s,kind)
   for _ in range(100):
    if s.state=='waiting_download':break
    await asyncio.sleep(.02)
   await s.stop();assert provider.lookup(uncertain['request_id'])['state']=='unknown'
   assert s.unresolved()[0]['id']==uncertain['request_id']
   try:await provider.submit({**body,'request_id':'flow-'+str(uuid.uuid4())})
   except HTTPException:pass
   else:raise AssertionError('Unresolved request resubmitted')
   try:await s.review(uncertain['request_id'],{})
   except HTTPException:pass
   else:raise AssertionError('Review needs explicit user acknowledgement')
   await s.review(uncertain['request_id'],{'confirm_no_result':True});assert not s.unresolved()
   # A wrong-duration file must never become an accepted node result.
   short=root/'short.mp4';subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-t','1','-c','copy','-y',str(short)],check=True)
   class Download:
    suggested_filename='../../old-video.mp4'
    async def save_as(self,path):Path(path).write_bytes(short.read_bytes())
   s.active='flow-'+str(uuid.uuid4());s.download_waiter=asyncio.get_running_loop().create_future()
   await s.save_download(Download())
   try:await s.download_waiter
   except RuntimeError:pass
   else:raise AssertionError('Wrong-duration video accepted')
   s.active=None;s.download_waiter=None
   # Project/account switches stop before creating a new task.
   await page.evaluate("window.WIZ_global_data.oPEP7c='other@invalid'")
   try:await provider.submit({**body,'request_id':'flow-'+str(uuid.uuid4())})
   except HTTPException:pass
   else:raise AssertionError('Account switch accepted')
   await provider.close();await browser.close()
  library._root_guard.instance.close()
 print('PASS SimpleFlow: no eager browser, image+prompt checkpoints, one active clip, exact confirmation token, one click, verified download/hash/scene result, duplicate ID, before/after-send cancellation, explicit review, account switch. Local fixture; no Google calls.')
if __name__=='__main__':asyncio.run(main())
