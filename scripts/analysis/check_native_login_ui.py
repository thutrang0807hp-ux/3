"""Actual shell login entry points use native login, extension remains optional."""
import functools,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=browser.new_page();p.goto(f'http://127.0.0.1:{server.server_port}/index.html');p.wait_for_function('typeof openAccountWebLogin==="function"&&window.SFGeminiAuto')
  result=p.evaluate('''async()=>{const calls=[];engineRequest=async(path,body)=>{calls.push(path);if(path==='gemini-chat/login')return{id:'gchat-account-fixture'};if(path.endsWith('/status'))return{state:'waiting'};if(path==='gemini-chat/finish-login')return{};return{};};let screen=false;accountScreen=async()=>{screen=true;};await connectGeminiChat();await new Promise(r=>setTimeout(r,100));if(!document.querySelector('#accountWebDialog')||document.querySelector('#geminiAutoConnect'))throw Error('Wrong connection dialog');if(!calls.includes('gemini-chat/login')||calls.some(c=>c.includes('browser-bridge')))throw Error('Still requires extension');document.querySelector('#accountWebSave').click();await new Promise(r=>setTimeout(r,100));if(!calls.includes('gemini-chat/finish-login')||!screen)throw Error('Native session not accepted');return calls;}''')
  print('PASS actual shell native login -> finish-login -> accounts; no extension setup:',result);browser.close()
finally:server.shutdown()
