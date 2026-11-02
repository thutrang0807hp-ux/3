"""Browser UI with mocked API; no real Flow submission."""
import base64,io,json
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
from PIL import Image
from playwright.sync_api import sync_playwright,expect
from .check_flow_prepare_ui import Quiet

def main():
 root=Path(__file__).resolve().parents[2]
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));Thread(target=server.serve_forever,daemon=True).start()
 posts=[];pairs=[];errors=[];unresolved=[];selection={'available':True,'account_id':'account','account_name':'Fixture','token':'fixture'}
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   def api(route):
    path=route.request.url.split('/local-api/')[1]
    if path=='flow/simple/status':return route.fulfill(json={'enabled':True,'selection':selection,'unresolved':unresolved})
    if path=='flow/simple/pair-trial':
     body=route.request.post_data_json;pairs.append(body)
     return route.fulfill(json={'request_id':'flow-pair-ready','state':'inputs_sent','message':'Ready',
      'room_id':body['room_id'],'scene_id':body['scene_id'],'part':body['part'],'account_id':'account',
      'settings':body['settings'],'generation_ready':True,'delivered':True,'image_attached':True,'prompt_filled':True,'prompt_verified':True,'settings_verified':True})
    if path=='flow/simple/jobs':
     posts.append(route.request.post_data_json)
     return route.fulfill(json={'request_id':posts[-1]['request_id'],'state':'running','submitted':True,'store_id':'fixture'})
    if path.startswith('flow/simple/tracking-diagnostics/'):
     return route.fulfill(json={'request_id':path.split('/')[-1],'message':'Đã đọc cấu trúc kết quả Flow; không tạo lại.','can_retry':False,'result_tracking':{'read_only':True,'cards':[{'rejected_because':['full_prompt_not_in_card']}]}})
    if path.startswith('flow/simple/diagnostics/'):
     return route.fulfill(json={'request_id':posts[0]['request_id'],'can_retry':False,'record':{'state':'unknown'},'result_tracking':{'read_only':True}})
    if path.startswith('flow/simple/jobs/'):
     return route.fulfill(json={'request_id':path.split('/')[-1],'state':'running','submitted':True,'store_id':'fixture','progress':37,'progress_source':'flow_ui','message':'Flow đang tạo video · 37%'})
    return route.fulfill(json={})
   page.route('**/local-api/**',api);page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('!!window.SFVeoNode')
   buffer=io.BytesIO();Image.new('RGB',(90,160),'green').save(buffer,format='PNG');url='data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()
   page.evaluate('''async image=>{project=blankProject();project.id='room';project.source={poster:image,asset:'source'};project.analysis.frameQualityRequired=false;assets.set('frame',new File([await(await fetch(image)).blob()],'frame.png',{type:'image/png'}));project.scenes=[sceneRecord(0,8,0,[image])];const s=project.scenes[0];s.id='scene';s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',asset:'frame',image};s.approvedFrame='source';s.frameSelectionId='source';await storeProject();render();await SFVeoNode.refresh();}''',url)
   node=page.locator('#node-videos');node.locator('[data-vn-prompt]').fill('Wave once.')
   expect(node.locator('[data-vn=create]')).to_have_count(1);expect(node.locator('[data-vn=create]')).to_be_disabled()
   node.locator('[data-vn=pair-trial]').click();expect(node.locator('[data-vn=create]')).to_be_enabled()
   node.locator('[data-vn-prompt]').fill('Different prompt.');expect(node.locator('[data-vn=create]')).to_be_disabled()
   node.locator('[data-vn-prompt]').fill('Wave once.');expect(node.locator('[data-vn=create]')).to_be_enabled()
   with page.expect_event('dialog') as cancelled:node.locator('[data-vn=create]').click()
   cancelled.value.dismiss()
   expect(node.locator('[data-vn=create]')).to_be_enabled();assert not posts
   with page.expect_event('dialog') as approved:node.locator('[data-vn=create]').click()
   approved.value.accept()
   page.wait_for_function('(project.cloudJobs||[]).some(j=>j.provider==="flow")')
   page.evaluate('()=>SFVeoNode.sync()')
   expect(node.locator('[data-vn-generation] progress')).to_have_attribute('value','37')
   expect(node.locator('[data-vn-generation]')).to_contain_text('37% từ Flow')
   expect(node.locator('[data-vn=create]')).to_be_disabled()
   assert len(posts)==1 and posts[0]['prepared_request_id']=='flow-pair-ready' and posts[0]['confirm_send'] is True,posts
   # If Flow omits progress, show indeterminate; never manufacture a percentage.
   page.route('**/local-api/flow/simple/jobs/*',lambda r:r.fulfill(json={'request_id':posts[0]['request_id'],'state':'running','submitted':True,'store_id':'fixture','progress':None,'progress_source':None,'message':'Đang chờ Flow'}))
   page.evaluate('()=>SFVeoNode.sync()')
   expect(node.locator('[data-vn-generation] progress')).not_to_have_attribute('value','37')
   assert node.locator('[data-vn-generation] progress').get_attribute('value') is None
   # Report is downloadable while generation remains active, without Stop.
   expect(node.locator('[data-vn=tracking-report]')).to_be_enabled()
   with page.expect_download() as downloaded:
    node.locator('[data-vn=tracking-report]').click()
   payload=json.loads(Path(downloaded.value.path()).read_text())
   assert payload['report']['result_tracking']['read_only'] and payload['report']['can_retry'] is False
   assert len(posts)==1
   assert page.evaluate('project.cloudJobs[0].state')=='running'
   # Failed live inspection still downloads the cached receipt and failure reason.
   page.route('**/local-api/flow/simple/tracking-diagnostics/*',lambda r:r.fulfill(status=409,json={'detail':'Phiên Flow chưa sẵn sàng.'}))
   with page.expect_download() as fallback:
    node.locator('[data-vn=tracking-report]').click()
   payload=json.loads(Path(fallback.value.path()).read_text())
   assert 'tracking_capture_error' in payload['report'] and payload['report']['can_retry'] is False
   assert len(posts)==1
   # An older unknown from another scene/schema must override the latest failed job.
   old='flow-91d22109-84b3-4515-bbeb-f176580f176c';other='flow-older-second'
   unresolved.extend([
    {'id':old,'room_id':'room','account_id':'account','scene_id':'older-scene'},
    {'id':'flow-foreign-room','room_id':'elsewhere','account_id':'account'},
    {'id':'flow-foreign-account','room_id':'room','account_id':'another'},
   ])
   page.evaluate("""old=>{
    for(const job of project.cloudJobs)job.state='failed';
    project.cloudJobs.push({id:old,provider:'flow',kind:'video',sceneId:'older-scene',part:'a',prompt:'Original old prompt',state:'unknown',veoNodeVersion:42});
   }""",old)
   page.route('**/local-api/flow/simple/jobs/*',lambda r:r.fulfill(json={'request_id':r.request.url.split('/')[-1],'state':'unknown','store_id':'fixture','result':None}))
   captured=[]
   def tracking(route):
    captured.append((route.request.url.split('/')[-1],route.request.post_data_json))
    route.fulfill(json={'request_id':captured[-1][0],'can_retry':False,'result_tracking':{'read_only':True}})
   page.route('**/local-api/flow/simple/tracking-diagnostics/*',tracking)
   page.evaluate('()=>SFVeoNode.refresh()')
   panel=node.locator('[data-vn-unresolved-tracking]');expect(panel).to_be_visible()
   expect(panel).to_contain_text('Có 1 lượt')
   expect(node.locator('[data-vn=pair-trial]')).to_be_disabled()
   with page.expect_download() as automatic:panel.locator('[data-vn=tracking-report]').click()
   payload=json.loads(Path(automatic.value.path()).read_text())
   assert payload['report']['request_id']==old and captured[-1][1]['prompt']=='Original old prompt',captured
   assert len(posts)==1
   # Multiple unknowns are collected, rather than forcing a code/scene selection.
   unresolved.append({'id':other,'room_id':'room','account_id':'account','scene_id':'third-scene'})
   page.evaluate('()=>SFVeoNode.refresh()');expect(panel).to_contain_text('Có 2 lượt')
   with page.expect_download() as batch:panel.locator('[data-vn=tracking-report]').click()
   payload=json.loads(Path(batch.value.path()).read_text())
   assert payload['report']['request_ids']==[old,other] and len(payload['report']['reports'])==2
   assert payload['report']['can_retry'] is False
   assert all(item[0] not in ('flow-foreign-room','flow-foreign-account') for item in captured)
   assert len(posts)==1
   # A missing GET receipt must still produce a fallback report, not a JS error.
   unresolved[:]=[unresolved[0]]
   page.route('**/local-api/flow/simple/jobs/*',lambda r:r.fulfill(status=503,json={'detail':'Receipt unavailable'}))
   page.route('**/local-api/flow/simple/diagnostics/*',lambda r:r.fulfill(json={'request_id':old,'can_retry':False}))
   page.evaluate('()=>SFVeoNode.refresh()')
   with page.expect_download() as no_record:panel.locator('[data-vn=tracking-report]').click()
   payload=json.loads(Path(no_record.value.path()).read_text())
   assert payload['report']['request_id']==old and 'tracking_capture_error' in payload['report']
   assert len(posts)==1
   assert not errors,errors
   browser.close()
  print('PASS UI: one visible Create button, ready receipt required, changed prompt locks, cancel sends nothing, confirm posts once, 37% rendered, missing percent indeterminate; automatic older-schema unknown selection, original prompt, batch reports, room/account filtering, missing receipt fallback without any new generation.')
 finally:server.shutdown()
if __name__=='__main__':main()
