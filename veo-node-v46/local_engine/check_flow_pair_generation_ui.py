"""Browser UI with mocked API; no real Flow submission."""
import base64,io
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
 posts=[];pairs=[];errors=[];selection={'available':True,'account_id':'account','account_name':'Fixture','token':'fixture'}
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   def api(route):
    path=route.request.url.split('/local-api/')[1]
    if path=='flow/simple/status':return route.fulfill(json={'enabled':True,'selection':selection,'unresolved':[]})
    if path=='flow/simple/pair-trial':
     body=route.request.post_data_json;pairs.append(body)
     return route.fulfill(json={'request_id':'flow-pair-ready','state':'inputs_sent','message':'Ready',
      'room_id':body['room_id'],'scene_id':body['scene_id'],'part':body['part'],'account_id':'account',
      'settings':body['settings'],'generation_ready':True,'delivered':True,'image_attached':True,'prompt_filled':True,'prompt_verified':True,'settings_verified':True})
    if path=='flow/simple/jobs':
     posts.append(route.request.post_data_json)
     return route.fulfill(json={'request_id':posts[-1]['request_id'],'state':'running','submitted':True,'store_id':'fixture'})
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
   assert not errors,errors
   browser.close()
  print('PASS UI: one visible Create button, ready receipt required, changed prompt locks, cancel sends nothing, confirm posts once, 37% rendered, missing percent indeterminate.')
 finally:server.shutdown()
if __name__=='__main__':main()
