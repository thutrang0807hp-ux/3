"""Actual shell routing: Motion Studio is a separate persisted room."""
import functools,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1500,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/index.html');page.wait_for_function('window.SceneForgeApp?.openMotionStudio&&typeof appBootReady!=="undefined"&&appBootReady',timeout=15000)
  before=page.evaluate('SceneForgeApp.getState()');product=before['products'][0]['id']
  page.evaluate('async id=>{await SceneForgeApp.openMotionStudio(id,{fresh:true});}',product)
  page.wait_for_function('document.querySelector("#workflowFrame")?.contentWindow.SFMotionStudio?.isMotion()',timeout=15000)
  result=page.evaluate('''async()=>{const r=currentRoom;const stored=await io('rooms','readonly',r.id);const api=document.querySelector('#workflowFrame').contentWindow;return {id:r.id,variant:r.workflowVariant,stored:stored.workflowVariant,mode:r.mode,active:document.querySelector('[data-workflow-mode="motion"]').classList.contains('selected'),nodes:!!api.document.querySelector('#node-motion-kit'),count:rooms.length};}''')
  assert result['variant']==result['stored']=='motion'and result['active']and result['nodes'],result
  page.evaluate('async()=>{await SceneForgeApp.switchWorkflow("reference");}')
  page.wait_for_function('currentRoom&&currentRoom.workflowVariant!=="motion"',timeout=10000)
  assert page.evaluate('currentRoom.id')!=result['id']
  assert page.evaluate('id=>roomFor(id).workflowVariant',result['id'])=='motion'
  # Returning to Motion reuses its room and does not convert the regular one.
  page.evaluate('async()=>{await SceneForgeApp.switchWorkflow("motion");}')
  page.wait_for_function('currentRoom?.workflowVariant==="motion"',timeout=10000)
  assert page.evaluate('currentRoom.id')==result['id']
  child=page.frame_locator('#workflowFrame')
  assert child.locator('.branchbar [data-branch="motion"]').count()==1
  assert child.locator('.branchbar [data-branch="motion"]').get_attribute('aria-pressed')=='true'
  assert child.locator('.branchbar [data-branch="reference"]').get_attribute('aria-pressed')=='false'
  page.screenshot(path='/tmp/motion-studio-shell.png')
  standalone=browser.new_page()
  standalone.goto(f'http://127.0.0.1:{server.server_port}/workflow.html')
  standalone.wait_for_function('window.SFMotionStudio&&window.SceneForgeWorkflow')
  standalone.locator('[data-mode-open="motion"]').click()
  standalone.wait_for_function('SFMotionStudio.isMotion()')
  motion_id=standalone.evaluate('project.id')
  assert standalone.locator('.branchbar [data-branch="motion"]').get_attribute('aria-pressed')=='true'
  standalone.locator('.branchbar [data-branch="reference"]').click()
  standalone.wait_for_function('!SFMotionStudio.isMotion()')
  assert standalone.evaluate('project.id')!=motion_id
  standalone.locator('.branchbar [data-branch="motion"]').click()
  standalone.wait_for_function('SFMotionStudio.isMotion()')
  assert standalone.evaluate('project.id')==motion_id
  standalone.screenshot(path='/tmp/motion-studio-three-branches.png')
  standalone.close()
  assert not errors,errors
  print('PASS Motion shell persistence and separate branch navigation',result)
  browser.close()
finally:server.shutdown()
