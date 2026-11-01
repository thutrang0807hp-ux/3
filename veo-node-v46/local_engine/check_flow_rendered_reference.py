"""Reproduce 670x1200 → 50x50 with CORS-tainted canvas and CSS cropping."""
import asyncio,io,tempfile
from functools import partial
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from unittest.mock import AsyncMock,patch
from PIL import Image
from playwright.async_api import async_playwright
from .check_flow_prepare import SETTINGS
from .flow_prepare import attached_reference,prepare_composer,image_error,allowed_reference_url
from .flow_settings import DEFAULTS

async def main():
 source=Image.new('RGB',(670,1200));source.putdata([(int(255*x/669),int(255*y/1199),150) for y in range(1200)for x in range(670)])
 buf=io.BytesIO();source.save(buf,format='PNG');state={'image':buf.getvalue(),'html':''}
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   is_image=self.path.startswith('/image');data=state['image'] if is_image else state['html'].encode()
   self.send_response(200);self.send_header('Content-Type','image/png' if is_image else 'text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 images=ThreadingHTTPServer(('127.0.0.1',0),Handler);host=ThreadingHTTPServer(('127.0.0.1',0),Handler)
 for server in (images,host):Thread(target=server.serve_forever,daemon=True).start()
 url=f'http://127.0.0.1:{images.server_port}/image.png'
 state['html']=SETTINGS+'<form onsubmit="return false"><img id=chip src="'+url+'" style="width:50px;height:50px;object-fit:cover;object-position:50% 0%;border-radius:8px"><textarea></textarea><button type=button onclick="window.sent=true">Generate</button></form>'+"<script>document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelector('#settings').hidden=true})</script>"
 try:
  with tempfile.TemporaryDirectory()as tmp:
   reference=Path(tmp)/'reference.png';reference.write_bytes(buf.getvalue())
   async with async_playwright()as pw:
    browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page();await page.goto(f'http://127.0.0.1:{host.server_port}/');await page.wait_for_function('document.querySelector("#chip").complete&&document.querySelector("#chip").naturalWidth===670')
    raw=await page.locator('#chip').screenshot();old=image_error(raw,source,crop=True,small=True);assert old>4,old
    errors={}
    for fit,position in [('cover','50% 0%'),('cover','50% 50%'),('fill','50% 50%'),('contain','50% 50%')]:
     await page.locator('#chip').evaluate('(e,v)=>{e.style.objectFit=v[0];e.style.objectPosition=v[1]}',[fit,position])
     report={};assert await attached_reference(page,source,report=report),report
     candidate=report['attachment_probe']['image_candidates'][0];assert candidate['capture_method']=='screenshot',candidate
     assert candidate['error']<=4 and candidate['natural_width']==670 and candidate['natural_height']==1200 and candidate['width']==50,candidate
     errors[fit+' '+position]=candidate['error']
    assert not allowed_reference_url(url)
    assert allowed_reference_url('https://lh3.googleusercontent.com/example')
    assert not allowed_reference_url('https://googleusercontent.com.evil.invalid/example')
    # Production allows only known HTTPS image hosts. Override only this test
    # origin to exercise the browser-context API without reaching Google.
    with patch('local_engine.flow_prepare.allowed_reference_url',lambda value:value.startswith(url)):
     report={};assert await attached_reference(page,source,report=report),report
     candidate=report['attachment_probe']['image_candidates'][0]
     assert candidate['capture_method']=='context_request' and candidate['original_read']=='ok',candidate
    await prepare_composer(page,reference,'Wave once.',DEFAULTS,AsyncMock(),{})
    assert await page.locator('textarea').input_value()=='Wave once.' and not await page.evaluate('!!window.sent')
    wrong=io.BytesIO();Image.new('RGB',(670,1200),'blue').save(wrong,format='PNG');state['image']=wrong.getvalue();await page.locator('#chip').evaluate('(e,url)=>e.src=url',url+'?v=wrong');await page.wait_for_function('document.querySelector("#chip").complete')
    report={};assert not await attached_reference(page,source,report=report),report
    await browser.close()
  print('PASS cross-origin 670x1200 image rendered 50x50: old center-fit error=',round(old,3),'new CSS-aware errors=',errors,'; wrong image rejected; prompt filled without Generate. Threshold remains 4.')
 finally:
  for server in (images,host):server.shutdown()

if __name__=='__main__':asyncio.run(main())
