"""Provider choice/config in the real photo canvas; status fixtures, no generation."""
import functools,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1500,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  rootpage=page;page.goto(f'http://127.0.0.1:{server.server_port}/photos.html');page.evaluate("document.body.insertAdjacentHTML('beforeend','<iframe name=provider-test src=photos.html style=position:fixed;inset:0;width:100%;height:100%;z-index:100></iframe>')");rootpage.wait_for_selector('iframe[name=provider-test]');rootpage.wait_for_function("document.querySelector('iframe[name=provider-test]').contentWindow.document.readyState!=='loading'");page=rootpage.frame(name='provider-test');page.wait_for_function('SceneForgeWorkflow?.workspaceSetSources&&window.SFPhotoVeo')
  page.evaluate('''async()=>{window.calls=[];parent.SceneForgeApp={photoBridge:{engine:async(path,body)=>{calls.push({path,body});if(path==='flow/simple/status')return{enabled:true,configured:true,generation_engine:'gflow-cli-direct',selection:{available:false},unresolved:[]};if(path==='muse/status')return{installed:false,configured:false,accounts:[],selection:{available:false}};return{};},saveDraft:async()=>{},listRecipes:async()=>[],getFile:async()=>null,putFile:async()=>{}}};const refs=Object.fromEntries(['person','outfit','product','background'].map(k=>[k,{images:[],description:''}]));await SceneForgeWorkflow.openRoom({id:'provider-choice',name:'Fixture',refs,product:{id:'p',name:'P',sceneBank:[]}});}''')
  assert page.locator('[data-video-source="flow"]').get_attribute('aria-pressed')=='true'
  page.evaluate('SFPhotoVeo.settings().ratio="16:9"')
  page.locator('[data-video-source="muse"]').click();page.wait_for_function('photoTools().video==="muse"')
  page.locator('[data-video-source-config]').click();page.wait_for_selector('#photoMuseAccount');page.evaluate('document.querySelector("#photoDialog").close()')
  page.locator('[data-video-source="flow"]').click();page.wait_for_function('photoTools().video==="flow"')
  assert page.evaluate('SFPhotoVeo.settings().ratio')=='16:9'
  page.locator('[data-video-source-config]').click();page.wait_for_selector('[data-pv-setting="model"]');assert page.locator('[data-pv-setting="ratio"]').input_value()=='16:9'
  assert not page.evaluate('calls.some(c=>c.body?.confirm_send===true||c.path.endsWith("/jobs"))')
  assert not errors,errors;rootpage.screenshot(path='/tmp/photo-video-source-v131.png');browser.close()
  print('PASS video-node Flow/Muse choice, both real configuration dialogs, preserved Flow ratio, no generation')
finally:server.shutdown()
