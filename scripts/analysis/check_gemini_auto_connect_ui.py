"""Automatic Gemini account recognition; existing account UI, no code flow."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
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
 page.evaluate('''async()=>{document.querySelector('#shellDialog').close();prefs.package5WelcomeDone=true;window.ready=false;window.calls=[];engineRequest=async(path,body)=>{calls.push({path,body});if(path==='browser-bridge/setup')return{download:'/local-api/browser-bridge/extension.zip'};if(path==='gemini-chat/browser-status')return{ready,extension_seen:ready,extension_version:ready?'1.7.1':'',account_ids:ready?['auto-account']:[],message:ready?'Đã tự kết nối':'Đang chờ tiện ích'};if(path==='status')return{accounts:ready?[{id:'auto-account',name:'Automatic Gemini',service:'gemini_chat',transport:'browser',state:'ready',active:true,enabled:true,session_verified:true}]:[],logs:[],rotation:{},engines:{gemini_chat:{installed:true,adapter:true,configured:ready}}};if(path==='logs')return[];if(path.includes('pairs')||path==='gemini-chat/login')throw Error('Pair code / SDK forbidden');return{};};await accountScreen('gemini_chat');}''')
 assert page.locator('#connectAccount').inner_text()=='Gemini tự kết nối'
 # No user click: the account list updates when extension discovery completes.
 page.evaluate('()=>{ready=true;}');page.wait_for_function('document.querySelector("#settingsAccounts")?.textContent.includes("Automatic Gemini")',timeout=8000)
 page.evaluate('()=>{ready=false;}');page.evaluate('async()=>{await connectGeminiChat();}')
 assert page.locator('#geminiAutoConnect').count()==1 and page.locator('#bridgeCode').count()==0 and page.locator('#bridgeCreate').count()==0
 assert 'không nhập mã'in page.locator('#geminiAutoConnect').inner_text()
 page.evaluate('()=>{ready=true;}');page.wait_for_function('document.querySelector("#settingsAccounts")?.textContent.includes("Automatic Gemini")',timeout=8000)
 assert page.evaluate('!calls.some(c=>c.path.includes("pairs")||c.path==="gemini-chat/login")')
 browser.close()
print('PASS actual shell: extension discovery auto-populates account list without clicks; Gemini help has no code controls and never calls pairing/SDK login')
