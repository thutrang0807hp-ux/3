import threading,http.server,functools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
from playwright.sync_api import sync_playwright
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':960})
 for file,selector in [('native/index.html','#timelineScroll'),('workflow.html','#viewport'),('photos.html','#photoViewport')]:
  page.goto(f'http://127.0.0.1:{server.server_port}/{file}',wait_until='domcontentloaded');page.wait_for_timeout(1800)
  result=page.evaluate('''selector=>{const el=document.querySelector(selector),box=el.getBoundingClientRect();const before=selector==='#timelineScroll'?document.querySelector('#zoom').value:document.querySelector(selector==='#viewport'?'#world':'#photoWorld').style.transform;const event=new WheelEvent('wheel',{bubbles:true,cancelable:true,ctrlKey:true,deltaY:-100,clientX:box.left+300,clientY:box.top+40});el.dispatchEvent(event);return {before,canceled:event.defaultPrevented}}''',selector)
  page.wait_for_timeout(100)
  result['after']=page.evaluate('''selector=>selector==='#timelineScroll'?document.querySelector('#zoom').value:document.querySelector(selector==='#viewport'?'#world':'#photoWorld').style.transform''',selector)
  assert result['canceled'] and result['before']!=result['after'],(file,result)
  canceled=page.evaluate('''()=>{const e=new WheelEvent('wheel',{bubbles:true,cancelable:true,ctrlKey:true,deltaY:100});document.body.dispatchEvent(e);return e.defaultPrevented}''');assert canceled
  normal=page.evaluate('''()=>{const e=new WheelEvent('wheel',{bubbles:true,cancelable:true,deltaY:100});document.body.dispatchEvent(e);return e.defaultPrevented}''');assert not normal
  print('PASS',file,result)
 browser.close()
server.shutdown()
