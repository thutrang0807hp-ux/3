"""Actual rebuilt account dashboard + workflow, shared real API and fixture login."""
import os,tempfile,time,socket,urllib.request,base64,io,json
from threading import Thread
from pathlib import Path
from unittest.mock import AsyncMock,patch
import uvicorn
from PIL import Image
from playwright.sync_api import sync_playwright,expect

def main():
 with tempfile.TemporaryDirectory()as tmp:
  os.environ['SCENEFORGE_LOCAL_DATA']=tmp
  from . import server
  if os.environ.get('SCENEFORGE_TEST_FRONTEND'):
   from fastapi.staticfiles import StaticFiles
   for route in server.app.routes:
    if getattr(route,'name',None)=='frontend':route.app=StaticFiles(directory=os.environ['SCENEFORGE_TEST_FRONTEND'],html=True)
  for key in ('one','two'):
   aid='flow-web-'+key
   server.VAULT.put('accounts',{'id':aid,'service':'flow','name':key+'@invalid','enabled':True,'session_verified':True,'state':'ready','active':False,'priority':0 if key=='one'else 1,'login_transport':'web_ui'})
  server.VAULT.set_secret('flow-managed-profiles',{('flow-web-'+key):{'account_id':'flow-web-'+key,'email':key+'@invalid','profile_key':key}for key in ('one','two')})
  server.FLOW_ACCOUNTS.pool.select({'mode':'selected','account_id':'flow-web-one'})
  with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  host=uvicorn.Server(uvicorn.Config(server.app,host='127.0.0.1',port=port,log_level='error'));thread=Thread(target=host.run,daemon=True);thread.start();base='http://127.0.0.1:'+str(port)
  errors=[];posted=[];forbidden=[]
  try:
   for _ in range(100):
    try:urllib.request.urlopen(base+'/local-api/health',timeout=.3);break
    except OSError:time.sleep(.05)
   with patch.object(server.FLOW_WEB_LOGIN,'start',new_callable=AsyncMock,return_value={'opened':True,'state':'waiting','message':'Fixture web login'})as login,sync_playwright()as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1500,'height':1050})
    def trap(r):forbidden.append(r.request.url);r.fulfill(status=409,json={'detail':'No separate login'})
    ctx.route('**/local-api/flow/simple/connect',trap)
    page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base)
    page.wait_for_function('appBootReady&&SceneForgeStorage.state.active')
    page.evaluate('async()=>{prefs.package5WelcomeDone=true;await savePrefs();document.querySelector("#shellDialog").close();await accountScreen("flow")}')
    expect(page.locator('.acctTopGrid')).to_be_visible();expect(page.locator('.acctGraph')).to_be_visible();expect(page.locator('.acctAccounts')).to_be_visible()
    expect(page.locator('#sharedFlowAccount')).to_have_count(0)
    expect(page.locator('.acctAccounts')).to_contain_text('one@invalid');expect(page.locator('.acctAccounts')).to_contain_text('two@invalid')
    expect(page.locator('#connectAccount')).to_have_text('Đăng nhập Flow trên web')
    page.screenshot(path='/workspace/veo-v45-accounts.png')
    page.locator('#connectAccount').click();expect(page.locator('#flowWebStatus')).to_have_text('Fixture web login');assert login.await_count==1
    assert not page.locator('[data-sf-connect]').count();page.locator('#flowWebClose').click()
    workflow=ctx.new_page();workflow.on('pageerror',lambda e:errors.append(str(e)));workflow.on('dialog',lambda d:d.accept())
    workflow.goto(base+'/workflow.html?mode=reference');workflow.wait_for_function('!!window.SFVeoNode')
    expect(workflow.locator('#node-videos [data-vn=connect]')).to_have_count(0)
    image=io.BytesIO();Image.new('RGB',(90,160),'green').save(image,format='PNG');data='data:image/png;base64,'+base64.b64encode(image.getvalue()).decode()
    workflow.evaluate('''async image=>{project=blankProject();project.id='shared-account-room';project.source={poster:image,asset:'source'};project.analysis.frameQualityRequired=false;assets.set('frame',new File([await(await fetch(image)).blob()],'frame.png',{type:'image/png'}));project.scenes=[sceneRecord(0,8,0,[image])];const s=project.scenes[0];s.id='scene';s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',asset:'frame',image};s.approvedFrame='source';s.frameSelectionId='source';await storeProject();render();}''',data)
    node=workflow.locator('#node-videos');expect(node.locator('[data-veo-build="45"]')).to_be_visible();expect(node.locator('.vnConnection')).to_contain_text('one@invalid')
    node.locator('[data-vn-prompt]').fill('Smile and wave.');expect(node.locator('[data-vn=create]')).to_be_enabled()
    # A central selection update broadcasts from account dashboard to the node.
    page.evaluate("async()=>{await engineRequest('flow/selection',{mode:'selected',account_id:'flow-web-two'});await accountScreen('flow',false)}")
    expect(node.locator('.vnConnection')).to_contain_text('two@invalid')
    assert node.locator('[data-vn=connect]').count()==0 and login.await_count==1 and not forbidden
    token=server.FLOW_ACCOUNTS.pool.status()['token']
    def submit(r):
     body=r.request.post_data_json;posted.append(body);r.fulfill(json={'state':'submitted','request_id':body['request_id'],'store_id':'fixture-store'})
    workflow.route('**/local-api/flow/simple/jobs',submit)
    workflow.route('**/local-api/flow/simple/jobs/*',lambda r:r.fulfill(json={'state':'submitted','request_id':r.request.url.rsplit('/',1)[-1],'store_id':'fixture-store'}))
    node.locator('[data-vn=create]').click();workflow.wait_for_function('project.cloudJobs?.some(j=>j.state==="submitted")')
    assert len(posted)==1 and posted[0]['selection_token']==token and posted[0]['scene_id']=='scene'
    assert workflow.evaluate('project.cloudJobs.at(-1).accountId')=='flow-web-two'
    assert not forbidden and login.await_count==1
    workflow.screenshot(path='/workspace/veo-v45-node.png')
    assert not errors,errors;browser.close()
   print('PASS v45 UI: original dashboard graph/table restored, existing account-tab web-login route, no node connection button even empty, selected account automatically updates across windows and is used in the next job token; no separate login. Real local status API, intercepted login/job execution only.')
  finally:
   host.should_exit=True;thread.join(timeout=8)
   for handler in list(server.RUNTIME_LOG.handlers):handler.close();server.RUNTIME_LOG.removeHandler(handler)
   server.LIBRARY._root_guard.instance.close()
if __name__=='__main__':main()
