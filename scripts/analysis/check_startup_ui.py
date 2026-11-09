"""Delayed startup loading, queued navigation and repeated home click checks."""
import asyncio,sys
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 async with async_playwright()as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for source in sys.argv[1:]or ['index.html','studio.html']:
   page=await b.new_page(viewport={'width':1280,'height':800});gate=asyncio.Event();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   async def route(r):
    if r.request.resource_type=='document':await r.fulfill(body=Path(source).read_text(),content_type='text/html');return
    if r.request.url.endswith('/library/status'):await gate.wait()
    await r.fulfill(json={})
   await page.route('**/*',route);await page.goto('http://127.0.0.1:43892/',wait_until='domcontentloaded')
   await page.wait_for_selector('#appBootStatus .bootCard');assert await page.locator('#bootHeading').inner_text()=='Mở không gian sáng tạo'
   assert await page.locator('#bootDetail').inner_text()=='Đang kết nối kho dữ liệu trên máy…'
   if source.endswith('index.html'):await page.screenshot(path='/tmp/sceneforge-startup100.png')
   # The existing startup guard queues the latest intent without executing it early.
   await page.locator('.rail .logo').click();assert not await page.evaluate('appBootReady')
   gate.set();await page.wait_for_function('appBootReady');await page.wait_for_selector('#appBootStatus',state='detached');await page.wait_for_timeout(200)
   result=await page.evaluate("""async()=>{await showView('overview');let renders=0;const old=render;render=function(...args){renders++;return old(...args)};document.querySelector('.rail .logo').click();document.querySelector('.rail .logo').click();await new Promise(r=>setTimeout(r,50));render=old;return renders}""")
   assert result==0,result;assert not errors,errors
   print('PASS',source,'static loading card, delayed readiness, queued navigation, repeated home clicks avoid rendering')
   await page.close()
  await b.close()
asyncio.run(main())
