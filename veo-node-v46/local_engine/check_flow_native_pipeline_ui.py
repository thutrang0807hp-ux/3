"""Actual workflow HTML with mocked local API. No Google or paid generation."""
import base64
import io
import json
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread

from PIL import Image
from playwright.sync_api import sync_playwright, expect


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def main():
    root=Path(__file__).resolve().parents[2]
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)))
    Thread(target=server.serve_forever,daemon=True).start()
    posts=[];errors=[];job_state='running'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            def api(route):
                path=route.request.url.split('/local-api/')[1]
                if path=='flow/simple/status':
                    return route.fulfill(json={'enabled':True,'native_pipeline':True,'unresolved':[],
                        'selection':{'available':True,'account_id':'account','account_name':'Fixture','token':'fixture'}})
                if path=='flow/simple/pair-trial':
                    raise AssertionError('UI must not run a separate upload preparation action')
                if path=='flow/simple/jobs':
                    body=route.request.post_data_json;posts.append(body)
                    return route.fulfill(json={'request_id':body['request_id'],'state':'running','submitted':None,
                        'store_id':'fixture','phase':'native_upload','message':'Đang upload ảnh; chưa gửi tạo.'})
                if path.startswith('flow/simple/jobs/'):
                    return route.fulfill(json={'request_id':path.split('/')[-1],'state':job_state,'submitted':None,
                        'store_id':'fixture','phase':'native_upload','message':'Đang upload ảnh; chưa gửi tạo.'})
                if path.startswith('flow/simple/diagnostics/'):
                    return route.fulfill(json={'request_id':posts[0]['request_id'],'can_retry':False,
                        'record':{'state':job_state,'native_inputs':{'native_stage':'upload_dispatching','generation_ready':False}}})
                if path.startswith('flow/simple/tracking-diagnostics/'):
                    raise AssertionError('Native report download must not reopen or inspect a browser')
                return route.fulfill(json={})
            page.route('**/local-api/**',api)
            page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference')
            page.wait_for_function('!!window.SFVeoNode')
            image=io.BytesIO();Image.new('RGB',(90,160),'green').save(image,format='PNG')
            url='data:image/png;base64,'+base64.b64encode(image.getvalue()).decode()
            page.evaluate('''async image=>{
                project=blankProject();project.id='room';project.source={poster:image,asset:'source'};
                project.analysis.frameQualityRequired=false;
                assets.set('frame',new File([await(await fetch(image)).blob()],'frame.png',{type:'image/png'}));
                project.scenes=[sceneRecord(0,8,0,[image])];const s=project.scenes[0];s.id='scene';
                s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',asset:'frame',image};
                s.approvedFrame='source';s.frameSelectionId='source';
                await storeProject();render();await SFVeoNode.refresh();
            }''',url)
            node=page.locator('#node-videos')
            node.locator('[data-vn-prompt]').fill('Wave once.')
            expect(node.locator('[data-vn=create]')).to_have_count(1)
            expect(node.locator('[data-vn=pair-trial]')).to_have_count(0)
            expect(node.locator('[data-vn=create]')).to_be_enabled()
            page.once('dialog',lambda d:d.dismiss())
            node.locator('[data-vn=create]').click()
            expect(node.locator('[data-vn=create]')).to_be_enabled()
            assert not posts
            page.once('dialog',lambda d:d.accept())
            node.locator('[data-vn=create]').click()
            page.wait_for_function('project.cloudJobs?.length===1')
            page.evaluate('()=>SFVeoNode.sync()')
            expect(node.locator('[data-vn=create]')).to_be_disabled()
            assert len(posts)==1 and posts[0]['native_pipeline'] is True
            assert 'prepared_request_id' not in posts[0]
            assert posts[0]['prompt']=='Wave once.' and posts[0]['confirm_send'] is True
            assert posts[0]['room_id']=='room' and posts[0]['scene_id']=='scene'
            job_state='failed'
            page.evaluate('()=>SFVeoNode.sync()')
            with page.expect_download() as downloaded:
                node.locator('[data-vn=tracking-report]').click()
            report=json.loads(Path(downloaded.value.path()).read_text())['report']
            assert report['record']['state']=='failed'
            assert report['record']['native_inputs']['native_stage']=='upload_dispatching'
            assert len(posts)==1
            assert not errors,errors
            browser.close()
        print('PASS native UI: one Create action, cancel posts nothing, confirm claims one job; failed-upload report downloads without browser inspection or resubmission; no JavaScript errors.')
    finally:
        server.shutdown();server.server_close()


if __name__=='__main__':main()
