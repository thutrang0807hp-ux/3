"""Actual rebuilt panel and node, intercepted endpoints; no real Flow/browser login."""
import os,socket,tempfile,time,json,urllib.request,base64,io
from pathlib import Path
from threading import Thread
import uvicorn
from PIL import Image
from playwright.sync_api import sync_playwright,expect
from .simple_flow import MODEL

def main():
 with tempfile.TemporaryDirectory()as tmp:
  os.environ['SCENEFORGE_LOCAL_DATA']=tmp
  from . import server
  if os.environ.get('SCENEFORGE_TEST_FRONTEND'):
   from fastapi.staticfiles import StaticFiles
   for route in server.app.routes:
    if getattr(route,'name',None)=='frontend':route.app=StaticFiles(directory=os.environ['SCENEFORGE_TEST_FRONTEND'],html=True)
  with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  host=uvicorn.Server(uvicorn.Config(server.app,host='127.0.0.1',port=port,log_level='error'));thread=Thread(target=host.run,daemon=True);thread.start();base='http://127.0.0.1:'+str(port)
  state={'state':'idle','message':'Chưa kết nối','enabled':True,'connection_method':'simple_flow','transport':'web_ui','models':[MODEL],'model_details':[{'id':MODEL,'accepts_images':True,'video_type':'i2v'}],'selection':{'mode':'selected','available':False,'token':'initial'},'interaction':None,'unresolved':[]};posts=[];errors=[]
  try:
   for _ in range(100):
    try:urllib.request.urlopen(base+'/local-api/health',timeout=.3);break
    except OSError:time.sleep(.05)
   with sync_playwright()as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1600,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
    def route(r):
     path=r.request.url.split('/local-api/',1)[1]
     if r.request.method=='POST':
      body=r.request.post_data_json;posts.append((path,body))
      if path.endswith('/connect'):state.update(state='awaiting_user',message='Đăng nhập rồi đóng cửa sổ',interaction={'id':'login-token','kind':'login','message':'Đăng nhập rồi đóng cửa sổ'})
      if path.endswith('/respond'):
       assert body=={'id':'login-token','accept':True},body
       state.update(state='ready',message='Đã nhận phiên',interaction=None,account_binding=True,selection={'mode':'selected','available':True,'account_name':'Fixture','token':'connected'})
     r.fulfill(json=state)
    page.route('**/local-api/flow/simple/**',route);page.route('**/local-api/flow/status',route);page.route('**/local-api/flow/models',route)
    page.goto(base);page.wait_for_function('appBootReady&&SceneForgeStorage.state.active')
    page.evaluate('async()=>{prefs.package5WelcomeDone=true;await savePrefs();document.querySelector("#shellDialog").close();await accountScreen("flow")}')
    page.locator('#connectAccount').click();panel=page.locator('dialog').filter(has_text='Flow đơn giản · một clip mỗi lần');expect(panel).to_be_visible()
    panel.locator('[data-sf-browser]').select_option('chrome');panel.locator('[data-sf-connect]').click();expect(panel.locator('[data-sf-yes]')).to_be_visible()
    panel.locator('[data-sf-yes]').click();expect(panel.locator('[data-sf-status]')).to_have_text('Đã nhận phiên')
    assert posts[0]==('flow/simple/connect',{'browser':'chrome'})and len(posts)==2,posts
    panel.locator('[data-sf-close]').click();expect(panel).to_have_count(0)
    page.goto(base+'/workflow.html?mode=reference');page.wait_for_function('!!window.SFMediaNodes&&!!window.SFSimpleFlow')
    image=io.BytesIO();Image.new('RGB',(90,160),'green').save(image,format='PNG');data='data:image/png;base64,'+base64.b64encode(image.getvalue()).decode()
    page.evaluate('''async image=>{project=blankProject();project.id='simple-node';project.source={poster:image,asset:'source'};project.analysis.frameQualityRequired=false;assets.set('frame',new File([await(await fetch(image)).blob()],'frame.png',{type:'image/png'}));project.scenes=Array.from({length:2},(_,i)=>sceneRecord(i*8,(i+1)*8,i,[image]));for(const s of project.scenes){s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',asset:'frame',image};s.approvedFrame='source';s.frameSelectionId='source';}await storeProject();render();}''',data)
    page.wait_for_function('project.mediaNodes?.flowModel==="'+MODEL+'"')
    run=page.locator('#node-videos header [data-mn=run-clips]');expect(run).to_have_text('▶ Chạy 1 clip')
    page.evaluate('()=>{directDialog=async(scenes,options)=>{window.captured={count:scenes.length,options};};}')
    run.click();page.wait_for_function('!!window.captured');assert page.evaluate('captured.options.slots.length')==1
    assert len(posts)==2,'Node attempted extra connection or generation'
    assert not errors,errors;browser.close()
   print('PASS actual SimpleFlow panel: browser selection, explicit step token, close; Veo v42 submits one slot even with two scenes; no legacy or provider calls. Intercepted UI only.')
  finally:
   host.should_exit=True;thread.join(timeout=8)
   for handler in list(server.RUNTIME_LOG.handlers):handler.close();server.RUNTIME_LOG.removeHandler(handler)
   server.LIBRARY._root_guard.instance.close()
if __name__=='__main__':main()
