"""Real extension MAIN-world probe and same-origin fetch; synthetic Flow only."""
import base64,hashlib,json,os,re,tempfile
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
from playwright.sync_api import sync_playwright,expect


def main(folder=None):
    folder=Path(folder or Path(__file__).resolve().parents[1]/'scripts/browser-extension').resolve()
    manifest=json.loads((folder/'manifest.json').read_text());digest=hashlib.sha256(base64.b64decode(manifest['key'])).hexdigest()[:32]
    extension_id=''.join(chr(97+int(v,16))for v in digest)
    state={'case':'ok'};requests=[];secret='private-probe-token-do-not-return'
    with tempfile.TemporaryDirectory()as tmp,sync_playwright()as pw:
        context=pw.chromium.launch_persistent_context(tmp,executable_path=os.environ['SCENEFORGE_BRIDGE_TEST_BROWSER'],headless=True,args=['--no-sandbox','--disable-extensions-except='+str(folder),'--load-extension='+str(folder)],ignore_default_args=['--disable-extensions'])
        def flow_route(route):
            request=route.request;url=urlsplit(request.url)
            if request.method=='GET':
                wiz={'FdrFJe':'123','SNlM0e':secret,'oPEP7c':'fixture@invalid','cfb2h':'boq_labs-ai-sandbox-frontend_20261007.14_p0'}
                if state['case']=='missing':wiz={}
                html='<html><body>Flow fixture<script>window.WIZ_global_data='+json.dumps(wiz)+'</script></body></html>'
                if state['case']=='fallback':html=html.replace('window.WIZ_global_data=','window.fixtureFallback=')
                route.fulfill(status=200,content_type='text/html',body=html);return
            assert url.path=='/_/AiSandboxAngularFrontend/data/batchexecute' and request.method=='POST','Only read-only credit RPC permitted'
            assert parse_qs(url.query)['rpcids']==['nzlxg']
            data=parse_qs(request.post_data or '');assert data['at']==[secret]
            assert json.loads(data['f.req'][0])==[[['nzlxg','[]',None,'generic']]]
            assert 'OSID=fixture-flow-cookie' in request.all_headers().get('cookie','')
            requests.append(state['case'])
            status=403 if state['case']=='http'else 200
            payload=[["er",None,None,None,None,401]]if state['case']=='rpc'else[["wrb.fr","nzlxg","[0]"]]
            route.fulfill(status=status,content_type='application/json',body=")]}'\n123\n"+json.dumps(payload)+'\n')
        context.route('https://flow.google.com/**',flow_route)
        context.add_cookies([{'url':'https://flow.google.com/','name':'OSID','value':'fixture-flow-cookie','secure':True,'httpOnly':True}])
        flow=context.new_page();popup=context.new_page();popup.goto('chrome-extension://'+extension_id+'/popup.html')
        errors=[];popup.on('pageerror',lambda e:errors.append(str(e)))
        for case,code in [('ok','FLOW_BROWSER_CREDIT_OK'),('rpc','FLOW_BROWSER_RPC_AUTH_REJECTED'),('http','FLOW_BROWSER_HTTP_REJECTED'),('fallback','FLOW_BROWSER_CREDIT_OK'),('missing','FLOW_BROWSER_METADATA_MISSING')]:
            state['case']=case;flow.goto('https://flow.google.com/?authuser=1');popup.bring_to_front()
            if not popup.locator('#probeFlow').is_visible():popup.locator('#probeBox summary').click()
            popup.locator('#probeFlow').click()
            expect(popup.locator('#copyProbe')).to_be_visible(timeout=30000)
            popup.wait_for_function("!document.querySelector('#probeFlow').disabled")
            text=popup.locator('#probeReport').input_value();result=json.loads(text)
            assert result['code']==code,(case,result)
            assert result['generated_content']is False
            assert secret not in text and 'fixture@invalid'not in text and 'fixture-flow-cookie'not in text
            assert not errors,errors
        assert requests==['ok','rpc','http','fallback'],requests
        context.close()
    print('PASS actual extension MAIN-world injection + actual same-origin Chromium fetch: credit zero accepted, RPC401/HTTP403 distinguished, HTML fallback, missing metadata makes no request, no generation/secret/email in report. Fixture Google page only; live Google session not verified.')

if __name__=='__main__':main()
