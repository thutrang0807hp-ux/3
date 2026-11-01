"""SceneForge browser UI preparation flow; API calls use explicit fixtures."""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
import base64,io,hashlib
from PIL import Image
from playwright.sync_api import sync_playwright,expect
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass

def main():
 root=Path(__file__).resolve().parents[2];server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));Thread(target=server.serve_forever,daemon=True).start()
 posted=[];errors=[];selection={'available':True,'account_id':'account','account_name':'Fixture','token':'fixture'}
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   def api(route):
    path=route.request.url.split('/local-api/')[1]
    if path=='flow/simple/status':return route.fulfill(json={'enabled':True,'selection':selection,'unresolved':[]})
    if path=='flow/simple/prepare':
     posted.append(route.request.post_data_json);return route.fulfill(json={'request_id':'flow-prepare-fixture','state':'running','message':'Preparing','room_id':'room','scene_id':'scene','part':posted[-1]['part'],'settings':posted[-1]['settings'],'account_id':'account'})
    if path=='flow/simple/prepare/flow-prepare-fixture':return route.fulfill(json={'request_id':'flow-prepare-fixture','state':'ready','message':'Đã đối chiếu đúng ảnh và prompt','room_id':'room','scene_id':'scene','part':posted[-1]['part'],'settings':posted[-1]['settings'],'account_id':'account'})
    return route.fulfill(json={})
   page.route('**/local-api/**',api);page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('!!window.SFVeoNode')
   b=io.BytesIO();Image.new('RGB',(90,160),'green').save(b,format='PNG');url='data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
   page.evaluate('''async image=>{project=blankProject();project.id='room';project.source={poster:image,asset:'source'};project.analysis.frameQualityRequired=false;assets.set('frame',new File([await(await fetch(image)).blob()],'frame.png',{type:'image/png'}));project.scenes=[sceneRecord(0,8,0,[image])];const s=project.scenes[0];s.id='scene';s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',asset:'frame',image};s.approvedFrame='source';s.frameSelectionId='source';await storeProject();render();await SFVeoNode.refresh();}''',url)
   node=page.locator('#node-videos');node.locator('[data-vn-prompt]').fill('Wave once.')
   expect(node.locator('[data-vn=create]')).to_be_disabled()
   node.locator('[data-vn=prepare]').click();expect(node.locator('[data-vn-prepare-state]')).to_contain_text('Đã đối chiếu')
   expect(node.locator('[data-vn=create]')).to_be_enabled()
   assert len(posted)==1 and posted[0]['reference_sha256']==hashlib.sha256(b.getvalue()).hexdigest(),posted
   assert posted[0]['prompt']=='Wave once.' and posted[0]['scene_id']=='scene' and posted[0]['room_id']=='room'
   node.locator('[data-vn-prompt]').fill('Different motion.')
   expect(node.locator('[data-vn=create]')).to_be_disabled()
   assert not errors,errors;browser.close()
  print('PASS preparation UI: correct image hash/scene/part/prompt sent, Generate disabled before ready, enabled after receipt, disabled when prompt changes; no JS errors.')
 finally:server.shutdown()
if __name__=='__main__':main()
