"""Real Chromium: zoom geometry, pointer hit testing and drag remain aligned on both canvases."""
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright()as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name,world,node,viewport in [('workflow.html','world','.node','#viewport'),('photos.html','photoWorld','.photoNode','#photoViewport')]:
  p=browser.new_page(viewport={'width':1400,'height':1000});errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   path=urlsplit(r.request.url).path;f=ROOT/path.lstrip('/')
   if '/local-api/'in path:r.fulfill(json={})
   elif f.is_file():r.fulfill(path=str(f))
   else:r.fulfill(status=404,body='')
  p.route('**/*',route);p.goto('http://127.0.0.1:43891/'+name+'?demo=1');p.wait_for_function('typeof applyView==="function"');p.wait_for_timeout(1000)
  if name=='workflow.html':p.get_by_text('Xem mẫu giao diện',exact=True).first.click()
  else:p.evaluate('''async()=>{parent.SceneForgeApp={photoBridge:{engine:async()=>({}),saveDraft:async()=>{},listRecipes:async()=>[],getFile:async()=>null,putFile:async()=>{}}};const refs=Object.fromEntries(['person','outfit','product','background'].map(k=>[k,{images:[],description:''}]));await SceneForgeWorkflow.openRoom({id:'zoom-fixture',name:'Zoom',refs,product:{id:'p',name:'Product',sceneBank:[]}});}''')
  p.wait_for_selector(node);p.wait_for_timeout(500);print('Checking',name,flush=True);n=p.locator(node).first
  for z in [.5,1,1.7]:
   p.evaluate('(z)=>{view.x=20;view.y=20;view.z=z;applyView();}',z)
   geometry=n.evaluate('e=>{const a=e.getBoundingClientRect(),v=document.querySelector("#viewport,#photoViewport").getBoundingClientRect();return {left:a.left-v.left,top:a.top-v.top,x:e.offsetLeft,y:e.offsetTop,width:a.width,w:e.offsetWidth};}')
   assert abs(geometry['left']-(20+geometry['x']*z))<2,geometry
   assert abs(geometry['width']-geometry['w']*z)<2,geometry
   box=n.locator(':scope > header').bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
   assert p.evaluate('([x,y,selector])=>!!document.elementFromPoint(x,y)?.closest(selector)',[x,y,node])
  # Pointer drag must move the node by the exact screen delta at 170%.
  before=n.bounding_box();header=n.locator(':scope > header').bounding_box();p.mouse.move(header['x']+50,header['y']+20);p.mouse.down();p.mouse.move(header['x']+118,header['y']+54,steps=5);p.wait_for_timeout(100);after=n.bounding_box()
  assert abs(after['x']-before['x']-68)<3,(before,after)
  assert abs(after['y']-before['y']-34)<3,(before,after)
  p.mouse.up();p.wait_for_timeout(100)
  p.screenshot(path='/tmp/'+name+'-layout-zoom158.png')
  assert not errors,errors
  p.close()
 browser.close()
print('PASS both canvases: layout zoom 50/100/170%, screen geometry, pointer hit tests and real node drag align; screenshots captured')
