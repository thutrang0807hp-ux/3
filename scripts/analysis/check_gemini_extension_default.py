"""Actual shell entry points: Gemini uses scoped one-time pairing, never native login."""
import json,zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
with zipfile.ZipFile(ROOT/'downloads/v46-gemini-extension-login/SceneForge-Browser-Connect.zip')as z,zipfile.ZipFile(ROOT/'downloads/v46/SceneForge-Veo-v46-Source.zip')as base:
 assert z.testzip()is None
 assert json.loads(z.read('manifest.json'))['version']=='1.6.9'
 for name in z.namelist():assert z.read(name)==base.read('scripts/browser-extension/'+name)
with sync_playwright()as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page()
 def route(r):
  from urllib.parse import urlsplit
  path=urlsplit(r.request.url).path
  if '/local-api/'in path:r.fulfill(json={});return
  p=ROOT/path.lstrip('/')if path!='/'else ROOT/'index.html'
  if p.is_file():r.fulfill(path=str(p))
  else:r.fulfill(status=404,body='')
 page.route('**/*',route);page.goto('http://127.0.0.1:43891/');page.wait_for_function('appBootReady')
 page.evaluate('''()=>{document.querySelector('#shellDialog').close();window.calls=[];engineRequest=async(path,body)=>{calls.push({path,body});if(path==='browser-bridge/setup')return{folder:'fixture-extension',download:'/local-api/browser-bridge/extension.zip'};if(path==='browser-bridge/pairs')return{id:'pair-fixture',code:'12345678',state:'waiting',message:'Nhập mã'};if(path.includes('/pairs/'))return{id:'pair-fixture',state:'waiting',message:'Chờ kết nối'};throw Error('Unexpected endpoint '+path);};}''')
 for entry in ['connectGeminiChat()',"openAccountWebLogin('gemini_chat')","openAccountWebLogin('gemini_chat',{account_id:'existing'})"]:
  page.evaluate('async()=>{await '+entry+';}');page.wait_for_selector('#bridgeCreate')
  assert not page.locator('#bridgeTogether').is_checked()
  assert page.locator('#accountWebDialog').count()==0
  page.locator('#bridgeCreate').click();page.wait_for_function("document.querySelector('#bridgeCode').value==='12345678'")
  assert page.evaluate("calls.filter(c=>c.path==='browser-bridge/pairs').every(c=>JSON.stringify(c.body.services)==='[\"gemini_chat\"]')")
  page.evaluate("document.querySelector('#shellDialog').close()")
 assert page.evaluate("!calls.some(c=>c.path==='gemini-chat/login')")
 browser.close()
print('PASS Gemini main/profile connection routes use pairing; Gemini only by default, correct code shown, zero native login requests; extension bytes match published source')
