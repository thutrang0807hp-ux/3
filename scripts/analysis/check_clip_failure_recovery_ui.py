"""Chromium: failed-generation diagnostics and usable recovery controls. No Flow calls."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright,expect
async def main():
 html=Path('workflow.html').read_text();mode='network-error';posts=[];checks=[];download_events=[];created=[]
 rid='flow-fixture-failed';media='22222222-2222-4222-8222-222222222222';scene_id=None
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await browser.new_page(accept_downloads=True,viewport={'width':1500,'height':1100})
  page.on('download',lambda d:download_events.append(d.suggested_filename))
  def record():
   return {'request_id':rid,'store_id':'fixture-store','state':'failed' if mode=='failed' else 'unknown','submitted':True,'result':None,'message':'CLI báo Flow tạo video thất bại (MEDIA_GENERATION_STATUS_FAILED).' if mode=='failed' else 'Lượt đã gửi chưa xác định kết quả.','phase':'failed' if mode=='failed' else 'downloading','provider_task':{'media_id':media,'project_id':'11111111-1111-4111-8111-111111111111','association_confirmed':True,'state':'failed' if mode=='failed' else 'downloading'},'native_inputs':{'project_id':'11111111-1111-4111-8111-111111111111'}}
  async def route(r):
   url=r.request.url
   if '/local-api/' not in url:await r.fulfill(body=html,content_type='text/html');return
   if r.request.method=='POST':posts.append(url)
   if url.endswith('/flow/simple/jobs') and r.request.method=='POST':
    body=r.request.post_data_json;created.append(body);await r.fulfill(json={'request_id':body['request_id'],'state':'submitted','store_id':'fixture-store'});return
   if '/flow/simple/jobs/' in url and not url.endswith(rid):
    await r.fulfill(json={'request_id':url.rsplit('/',1)[-1],'state':'running','phase':'generating','store_id':'fixture-store','submitted':True});return
   if '/flow/simple/diagnostics/' in url:
    checks.append(url)
    if mode=='network-error':await r.fulfill(status=502,json={'detail':'fixture connection unavailable'});return
    await r.fulfill(json={'request_id':rid,'code':'found','record':record(),'can_retry':False});return
   if '/flow/simple/jobs/'+rid in url:await r.fulfill(json=record());return
   unresolved=[] if mode=='failed' else [{'id':rid,'room_id':'fixture-room','scene_id':scene_id,'part':'a','account_id':'fixture-account'}]
   await r.fulfill(json={'enabled':True,'native_pipeline':True,'selection':{'available':True,'token':'fixture-token','account_id':'fixture-account'},'unresolved':unresolved})
  await page.route('**/*',route)
  await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFVeoNode')
  scene_id=await page.evaluate('''async rid=>{
project=blankProject();project.id='fixture-room';project.analysis.frameQualityRequired=false;const canvas=document.createElement('canvas');canvas.width=90;canvas.height=160;canvas.getContext('2d').fillRect(0,0,90,160);const image=canvas.toDataURL();project.source={poster:image,asset:'source'};const s=sceneRecord(0,8,0,[image]);s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',image};s.approvedFrame='source';s.frameSelectionId='source';s.videoPromptOverrides={a:'A gentle movement.'};project.scenes=[s];const part=clipParts(s)[0];project.cloudJobs=[{id:rid,provider:'flow',kind:'video',sceneId:s.id,part:part.id,settings:{kind:'video',mode:'ingredients',ratio:'9:16',model:'lite',outputs:1},signature:await directSignature(s,part.id,'video'),prompt:makePrompt(s,part),state:'unknown',at:Date.now(),store_id:'fixture-store',veoNodeVersion:43}];await storeProject();render();await SFVeoNode.refresh();return s.id;}''',rid)
  await page.evaluate('SFVeoNode.refresh()');await page.locator('#node-videos .vnTile').click()
  panel=page.locator('#vnDetail [data-vn-recovery]');await expect(panel).to_be_visible()
  await expect(panel.locator('[data-vn=tracking-report]')).to_be_enabled()
  await expect(panel.locator('[data-vn=read]')).to_be_enabled()
  await expect(panel.locator('[data-vn=export-report]')).to_be_enabled()
  await expect(page.locator('#vnDetail [data-vn=create]')).to_be_disabled()
  await page.evaluate("window.recoveryImage=document.querySelector('#vnDetail .vnDetailPlayer img')")
  await panel.locator('[data-vn=tracking-report]').click()
  await expect(panel).to_contain_text('fixture connection unavailable')
  await expect(panel.locator('[data-vn=tracking-report]')).to_be_enabled()
  await expect(panel.locator('[data-vn=read]')).to_be_enabled()
  await expect(panel.locator('[data-vn=export-report]')).to_be_enabled()
  assert not download_events,'Checking a request must not masquerade as a video/JSON download'
  assert await page.evaluate("recoveryImage===document.querySelector('#vnDetail .vnDetailPlayer img')")
  assert not posts
  # Repeated failed checks must remain possible.
  before=len(checks);await panel.locator('[data-vn=tracking-report]').click();await expect(panel.locator('[data-vn=tracking-report]')).to_be_enabled();assert len(checks)>before
  mode='failed'
  await panel.locator('[data-vn=tracking-report]').click()
  await expect(panel).to_contain_text('MEDIA_GENERATION_STATUS_FAILED')
  await expect(panel.locator('[data-vn=tracking-report]')).to_be_enabled()
  await expect(panel.locator('[data-vn=read]')).to_be_enabled()
  await expect(panel.locator('[data-vn=export-report]')).to_be_enabled()
  await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled()
  assert await page.locator('#vnDetail video').count()==0
  await expect(page.locator('#vnDetail [data-vn=accept]')).to_be_disabled()
  assert await page.evaluate("project.cloudJobs[0].id==='flow-fixture-failed'&&project.cloudJobs[0].state==='failed'")
  async with page.expect_download() as info:await panel.locator('[data-vn=export-report]').click()
  download=await info.value;assert download.suggested_filename.endswith('.json');path=Path('/tmp/sceneforge-fixture-failed-report.json');await download.save_as(path)
  report=json.loads(path.read_text());assert report['report']['record']['state']=='failed';assert report['report']['request_id']==rid
  assert not posts,'No generation/retry request may be sent by checking/exporting errors'
  page.once('dialog',lambda dialog:dialog.dismiss())
  await page.locator('#vnDetail [data-vn=create]').click();await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled();assert not posts
  page.once('dialog',lambda dialog:dialog.accept())
  await page.locator('#vnDetail [data-vn=create]').click()
  await page.wait_for_function('project.cloudJobs.length===2')
  assert len(created)==1 and created[0]['request_id']!=rid
  assert await page.evaluate("project.cloudJobs[0].id==='flow-fixture-failed'&&project.cloudJobs[0].state==='failed'")
  print('PASS error controls recover; JSON export separate; no automatic generation; cancelling sends nothing; explicit confirmation creates one new ID and preserves failed history')
  await browser.close()
if __name__=='__main__':asyncio.run(main())
