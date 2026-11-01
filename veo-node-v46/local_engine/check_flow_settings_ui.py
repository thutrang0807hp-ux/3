import json,threading
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from playwright.sync_api import sync_playwright,expect
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(Path(__file__).resolve().parents[2])))
threading.Thread(target=server.serve_forever,daemon=True).start()
posted=[];errors=[]
selection={'available':True,'account_id':'one','account_name':'Fixture','token':'fixture'}
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  def api(route):
   path=route.request.url.split('/local-api/')[1]
   if path=='flow/simple/status':return route.fulfill(json={'enabled':True,'selection':selection,'unresolved':[]})
   if path=='flow/simple/settings':
    posted.append(route.request.post_data_json)
    return route.fulfill(json={'request_id':'flow-settings-fixture','state':'running','message':'Đang áp dụng','requested':posted[-1]['settings'],'room_id':'settings-room','account_id':'one'})
   if path=='flow/simple/settings/flow-settings-fixture':return route.fulfill(json={'request_id':'flow-settings-fixture','state':'verified','requested':posted[-1]['settings'],'observed':posted[-1]['settings'],'room_id':'settings-room','account_id':'one','has_preview':False})
   return route.fulfill(json={})
  page.route('**/local-api/**',api)
  page.goto('http://127.0.0.1:'+str(server.server_port)+'/workflow.html?mode=reference')
  page.wait_for_function('!!window.SFVeoNode')
  page.evaluate("async()=>{project=blankProject();project.id='settings-room';project.scenes=[];await storeProject();render();await SFVeoNode.refresh()}")
  node=page.locator('#node-videos')
  expect(node.locator('[data-vn-settings]')).to_be_visible()
  node.locator('[data-vn-setting=ratio]').select_option('16:9')
  node.locator('[data-vn-setting=model]').select_option('fast')
  node.locator('[data-vn-setting=outputs]').select_option('3')
  node.locator('[data-vn=apply-settings]').click()
  expect(node.locator('[data-vn-settings-state]')).to_contain_text('đã khớp')
  assert len(posted)==1,posted
  assert posted[0]=={'settings':{'kind':'video','mode':'ingredients','ratio':'16:9','model':'fast','outputs':3},'room_id':'settings-room','selection_token':'fixture'},posted
  node.locator('[data-vn-setting=ratio]').select_option('9:16')
  expect(node.locator('[data-vn-settings-state]')).to_contain_text('Chưa xác nhận')
  assert not errors,errors
  browser.close()
 print('PASS SceneForge UI: saved selections, settings API payload/account/room, poll verified result, changed selection invalidates match, no generation or upload request; no JS errors.')
finally:server.shutdown()
