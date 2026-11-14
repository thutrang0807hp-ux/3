"""Exercise the real shell's branch handoff, camera restore and failure recovery."""
import functools,http.server,threading,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1920,'height':1080});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/index.html');page.wait_for_function('window.SceneForgeApp?.openMotionStudio&&typeof appBootReady!=="undefined"&&appBootReady')
  page.evaluate('SceneForgeApp.switchWorkflow("reference")');page.wait_for_function('document.querySelector("#workflowFrame")?.contentWindow.SceneForgeWorkflow?.getViewport')
  first=page.evaluate('currentRoom.id')
  page.evaluate('''()=>{const w=document.querySelector('#workflowFrame').contentWindow;w.eval("project.script.push({id:'keep-script',start:0,end:2,newText:'Nội dung cần giữ'})");w.SceneForgeWorkflow.setViewport({x:-125,y:73,z:.62});window.flushCount=0;const f=flushFrames;flushFrames=async(...a)=>{flushCount++;return f(...a);};window.oldFrame=document.querySelector('#workflowFrame');const ready=readyRoomFrame;readyRoomFrame=async(...a)=>{await new Promise(r=>setTimeout(r,500));return ready(...a);};window.photoStatusWaiters=[];const engine=SceneForgeApp.photoBridge.engine;SceneForgeApp.photoBridge.engine=(path,...a)=>path==='status'?new Promise(resolve=>photoStatusWaiters.push(resolve)):path==='flow/simple/status'?Promise.resolve({generation_engine:'gflow-cli-direct',selection:{available:false}}):engine(path,...a);window.handoff=SceneForgeApp.switchWorkflow('photos');}''')
  page.wait_for_function('document.querySelector("[data-branch-departure]")&&currentRoom.mode==="photos"')
  visible=page.evaluate('''()=>{const f=document.querySelector('[data-branch-departure]');return {same:f===oldFrame,visible:!f.hidden&&getComputedStyle(f).display!=='none',inert:f.inert,room:f.contentWindow.SceneForgeWorkflow.getState().id};}''')
  assert visible['same']and visible['visible']and visible['inert']and visible['room']==first,visible
  page.evaluate('handoff');assert page.evaluate('flushCount')==1
  page.wait_for_function('document.querySelector("#workflowFrame")?.contentWindow.SceneForgeWorkflow?.getViewport')
  assert page.locator('[data-branch-departure]').count()==0
  assert page.locator('#roomFrames iframe').count()==1
  assert page.evaluate('photoStatusWaiters.length')>0
  assert page.frame_locator('#workflowFrame').locator('#photoNodes .photoNode').count()>0
  page.evaluate('photoStatusWaiters.forEach(resolve=>resolve({}))')
  initial=page.evaluate('document.querySelector("#workflowFrame").contentWindow.SceneForgeWorkflow.getViewport()')
  assert .25<=initial['z']<=1.8,initial
  photo=page.evaluate('currentRoom.id')
  page.evaluate('document.querySelector("#workflowFrame").contentWindow.SceneForgeWorkflow.setViewport({x:41,y:-95,z:.77})')
  boxes=[]
  for mode in ['motion','reference','photos']:
   page.evaluate('mode=>SceneForgeApp.switchWorkflow(mode)',mode)
   page.wait_for_function('document.querySelector("#workflowFrame")?.contentWindow.SceneForgeWorkflow?.getViewport')
   boxes.append(page.locator('#workflowModes').bounding_box())
   assert page.locator('#roomFrames iframe').count()==1
   if mode=='reference':
    assert page.evaluate('currentRoom.id')==first
    camera=page.evaluate('document.querySelector("#workflowFrame").contentWindow.SceneForgeWorkflow.getViewport()')
    assert camera=={'x':-125,'y':73,'z':.62},camera
    assert page.evaluate('document.querySelector("#workflowFrame").contentWindow.SceneForgeWorkflow.getState().script.some(x=>x.id==="keep-script"&&x.newText==="Nội dung cần giữ")')
   if mode=='photos':
    assert page.evaluate('currentRoom.id')==photo
    camera=page.evaluate('document.querySelector("#workflowFrame").contentWindow.SceneForgeWorkflow.getViewport()')
    assert camera=={'x':41,'y':-95,'z':.77},camera
  assert max(b['x']for b in boxes)-min(b['x']for b in boxes)<2,boxes
  page.locator('#branchVideoSettings').click()
  page.frame_locator('#workflowFrame').locator('#pvCancelSettings').wait_for()
  page.frame_locator('#workflowFrame').locator('#pvCancelSettings').click()
  page.set_viewport_size({'width':1366,'height':900})
  auto=page.locator('#workspaceAuto').bounding_box()
  assert auto and auto['x']+auto['width']<=1366,auto
  page.set_viewport_size({'width':1920,'height':1080})
  # A failed target initialization restores the previous saved room and active canvas.
  page.evaluate('''()=>{const f=readyRoomFrame;readyRoomFrame=async(...a)=>{if(a[2].workflowVariant==='motion')throw Error('fixture target failed');return f(...a);};}''')
  page.evaluate('SceneForgeApp.switchWorkflow("motion")')
  assert page.evaluate('currentRoom.id')==photo
  assert page.evaluate('document.querySelector("#workflowFrame").contentWindow.SceneForgeWorkflow.getState().id')==photo
  assert page.locator('#roomFrames iframe').count()==1
  assert not page.evaluate('switching||changingWorkflow||document.body.classList.contains("branchSwitching")')
  page.evaluate('''()=>{window.keptAfterFailure=document.querySelector('#workflowFrame');flushFrames=async()=>{throw Error('fixture save failed');};}''')
  page.evaluate('SceneForgeApp.switchWorkflow("reference")')
  assert page.evaluate('document.querySelector("#workflowFrame")===keptAfterFailure')
  assert page.evaluate('currentRoom.id')==photo
  page.screenshot(path='/tmp/branch-switch-v130.png')
  assert not errors,errors
  print('PASS one departure flush; old canvas stays until ready; per-room cameras/content restored; stable header; failed target recovers; one live frame after handoff')
  browser.close()
finally:server.shutdown()
