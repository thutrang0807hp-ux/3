"""Live diagnostic export must not reuse stale missing-record reports or discard known CLI logs."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright,expect
async def main():
 html=Path('workflow.html').read_text();mode='found';posts=[];reads=[];scene_id=None;rid='flow-fixture-live-export'
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await browser.new_page(accept_downloads=True,viewport={'width':1500,'height':1100})
  def record(foreign=False):
   return {'request_id':'flow-foreign-record' if foreign else rid,'store_id':'foreign-store' if foreign else 'fixture-store','state':'unknown','submitted':True,'message':'CLI gốc dừng, mã thoát 7.','phase':'running','native_inputs':{'room_id':'fixture-room','scene_id':scene_id,'part':'a','account_id':'fixture-account'},'engine_diagnostics':{'exit_code':7,'stdout':'','stderr':'FOREIGN LOG DO NOT EXPORT' if foreign else 'WireFormatError: fixture original-CLI generation response detail'}}
  async def route(r):
   url=r.request.url
   if '/local-api/' not in url:await r.fulfill(body=html,content_type='text/html');return
   if r.request.method=='POST':posts.append(url)
   if '/flow/simple/jobs/'+rid in url:
    reads.append(url)
    if mode in ('missing','offline'):await r.fulfill(status=404 if mode=='missing' else 502,json={'detail':'fixture record unavailable'});return
    await r.fulfill(json=record(mode=='foreign'));return
   if '/flow/simple/diagnostics/'+rid in url:
    reads.append(url);assert 'download_existing' not in url
    if mode=='offline':await r.fulfill(status=502,json={'detail':'fixture diagnostic offline'});return
    report={'request_id':rid,'code':'found' if mode=='found' else 'different_store' if mode=='foreign' else 'unknown_store','current_store_id':'fixture-store','record':record() if mode=='found' else None,'message':'fixture live report' if mode=='found' else 'Không có bản ghi lượt này trong kho đang mở; chưa biết đã gửi hay chưa.','can_retry':False}
    await r.fulfill(json=report);return
   await r.fulfill(json={'enabled':True,'native_pipeline':True,'selection':{'available':True,'token':'fixture','account_id':'fixture-account'},'unresolved':[{'id':rid,'room_id':'fixture-room','scene_id':scene_id,'part':'a','account_id':'fixture-account'}]})
  await page.route('**/*',route)
  await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFVeoNode')
  scene_id=await page.evaluate('''async rid=>{project=blankProject();project.id='fixture-room';project.analysis.frameQualityRequired=false;const c=document.createElement('canvas');c.width=90;c.height=160;const image=c.toDataURL();project.source={poster:image,asset:'source'};const s=sceneRecord(0,8,0,[image]);s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',image};s.approvedFrame='source';s.frameSelectionId='source';s.videoPromptOverrides={a:'A gentle movement.'};project.scenes=[s];const part=clipParts(s)[0];project.cloudJobs=[{id:rid,provider:'flow',kind:'video',sceneId:s.id,part:part.id,accountId:'fixture-account',state:'unknown',veoNodeVersion:43,at:Date.now(),signature:await directSignature(s,part.id,'video'),settings:{kind:'video',mode:'ingredients',ratio:'9:16',model:'lite',outputs:1},phaseMessage:'CLI gốc dừng, mã thoát 7.',diagnostics:{request_id:rid,code:'unknown_store',record:null,message:'STALE REPORT'}}];await storeProject();render();await SFVeoNode.refresh();return s.id;}''',rid)
  await page.evaluate('SFVeoNode.refresh()');await page.locator('#node-videos .vnTile').click()
  panel=page.locator('#vnDetail [data-vn-recovery]')
  async def export(tag):
   async with page.expect_download() as info:await panel.locator('[data-vn=export-report]').click()
   download=await info.value;path=Path('/tmp/sceneforge-live-export-'+tag+'.json');await download.save_as(path);await expect(panel.locator('[data-vn=export-report]')).to_be_enabled();return json.loads(path.read_text())['report']
  mode='missing';initial=await export('initial-missing');assert initial['record'] is None and initial['cached_backend_record'] is None;assert initial['frontend_snapshot']['last_message']=='CLI gốc dừng, mã thoát 7.';assert initial['export_read_errors']
  mode='found';found=await export('found');assert found['code']=='found';assert found['record']['engine_diagnostics']['exit_code']==7
  assert 'fixture original-CLI' in found['record']['engine_diagnostics']['stderr'];assert found['frontend_snapshot']['request_id']==rid;assert found['cached_backend_record']['record']['request_id']==rid
  assert found['expected_store_id'] if 'expected_store_id' in found else await page.evaluate("project.cloudJobs[0].store_id==='fixture-store'")
  mode='missing';missing=await export('missing');assert missing['code']=='unknown_store' and missing['record'] is None and missing['live_job_record'] is None
  assert 'fixture original-CLI' in missing['cached_backend_record']['record']['engine_diagnostics']['stderr'];assert missing['export_read_errors']
  await expect(panel).to_contain_text('Không có bản ghi lượt này')
  mode='foreign';foreign=await export('foreign');assert foreign['record'] is None;assert 'FOREIGN LOG DO NOT EXPORT' not in json.dumps(foreign)
  assert foreign['cached_backend_record']['record']['store_id']=='fixture-store';assert foreign['export_read_errors']
  mode='offline';offline=await export('offline');assert offline['code']=='diagnostics_unavailable' and offline['record'] is None;assert len(offline['export_read_errors'])==2
  assert offline['cached_backend_record']['record']['engine_diagnostics']['exit_code']==7
  await expect(panel.locator('[data-vn=tracking-report]')).to_be_enabled();await expect(panel.locator('[data-vn=read]')).to_be_enabled()
  await expect(page.locator('#vnDetail [data-vn=create]')).to_be_disabled()
  assert not posts;assert all('download_existing' not in url for url in reads)
  print('PASS export refreshes stale diagnostics, includes current CLI errors, preserves labeled cached logs on missing/offline records, rejects foreign records, and never sends generation/download commands')
  await browser.close()
if __name__=='__main__':asyncio.run(main())
