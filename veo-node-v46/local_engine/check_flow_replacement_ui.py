"""The user must review two previews and approve before replacing a chip."""
import base64,io
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
from PIL import Image
from playwright.sync_api import sync_playwright,expect
from .check_flow_prepare_ui import Quiet

def main():
 root=Path(__file__).resolve().parents[2];server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));Thread(target=server.serve_forever,daemon=True).start();posted=[];errors=[]
 buf=io.BytesIO();Image.new('RGB',(90,160),'green').save(buf,format='PNG');raw=buf.getvalue();url='data:image/png;base64,'+base64.b64encode(raw).decode();selection={'available':True,'account_id':'account','account_name':'Fixture','token':'fixture'}
 try:
  with sync_playwright()as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
   def report(state):return {'request_id':'ready'if state=='ready'else'preview','state':state,'message':state,'room_id':'room','scene_id':'scene','part':posted[-1]['part'],'settings':posted[-1]['settings'],'account_id':'account','has_attachment_preview':True,'has_source_preview':True,'replacement':{'approval_token':'approval'}}
   def api(route):
    path=route.request.url.split('/local-api/')[1]
    if path=='flow/simple/status':return route.fulfill(json={'enabled':True,'selection':selection,'unresolved':[]})
    if path=='flow/simple/prepare':
     posted.append(route.request.post_data_json);return route.fulfill(json=report('ready'if posted[-1].get('replace_attachment')else'awaiting_replacement'))
    if path.endswith('/attached-image')or path.endswith('/source-image'):return route.fulfill(body=raw,content_type='image/png')
    if path=='flow/simple/prepare/preview':return route.fulfill(json=report('awaiting_replacement'))
    if path=='flow/simple/prepare/ready':return route.fulfill(json=report('ready'))
    return route.fulfill(json={})
   page.route('**/local-api/**',api);page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');page.wait_for_function('!!window.SFVeoNode')
   page.evaluate('''async image=>{project=blankProject();project.id='room';project.source={poster:image,asset:'source'};project.analysis.frameQualityRequired=false;assets.set('frame',new File([await(await fetch(image)).blob()],'frame.png',{type:'image/png'}));project.scenes=[sceneRecord(0,8,0,[image])];const s=project.scenes[0];s.id='scene';s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',asset:'frame',image};s.approvedFrame='source';s.frameSelectionId='source';await storeProject();render();await SFVeoNode.refresh();}''',url)
   node=page.locator('#node-videos');node.locator('[data-vn-prompt]').fill('Wave once.');node.locator('[data-vn=prepare]').click();expect(node.locator('[data-vn-replacement]')).to_be_visible()
   expect(node.locator('[data-vn-replacement] img')).to_have_count(2);expect(node.locator('[data-vn=create]')).to_be_disabled()
   page.once('dialog',lambda d:d.dismiss());node.locator('[data-vn=replace-attachment]').click();assert len(posted)==1
   expect(node.locator('[data-vn=replace-attachment]')).to_be_enabled()
   page.once('dialog',lambda d:d.accept());node.locator('[data-vn=replace-attachment]').click();expect(node.locator('[data-vn=create]')).to_be_enabled()
   assert len(posted)==2 and posted[-1]['replace_attachment']=={'request_id':'preview','approval_token':'approval'},posted
   assert not errors,errors;browser.close()
  print('PASS replacement UI: two previews, Generate locked, cancel sends nothing, confirm sends bound approval, ready enables Generate; no JS errors.')
 finally:server.shutdown()
if __name__=='__main__':main()
