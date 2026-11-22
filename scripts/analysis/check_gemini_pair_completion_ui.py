"""Pairing completion updates actual account settings despite transient polling/log errors."""
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
 page.evaluate("""()=>{document.querySelector('#shellDialog').close();prefs.package5WelcomeDone=true;window.pairReads=0;window.visibleAccounts=[];window.nativeLoginPosts=0;engineRequest=async(path,body)=>{if(path==='browser-bridge/setup')return{folder:'extension',download:'/local-api/browser-bridge/extension.zip'};if(path==='browser-bridge/pairs')return{id:'fixture',code:'12345678',state:'issued',message:'Nhập mã'};if(path==='browser-bridge/pairs/fixture'){pairReads++;if(pairReads===1)throw Error('Transient status failure');if(pairReads===2)return{id:'fixture',state:'checking',message:'Đang kiểm tra'};visibleAccounts=[{id:'a',name:'Paired Gemini',service:'gemini_chat',state:'ready',enabled:true,active:true,session_verified:true}];return{id:'fixture',state:'done',message:'Đã lưu tài khoản',account_id:'a'};}if(path==='status')return{accounts:visibleAccounts,logs:[],engines:{gemini_chat:{installed:true,adapter:true,configured:true}},rotation:{}};if(path==='logs')throw Error('Logs unavailable');if(path==='gemini-chat/login'){nativeLoginPosts++;throw Error('Native login forbidden');}return{};};}""")
 page.evaluate('async()=>{await connectGeminiChat();}')
 page.locator('#bridgeCreate').click()
 page.wait_for_function('pairReads>=3',timeout=15000)
 page.wait_for_function('!!document.querySelector("#settingsAccounts")?.textContent.includes("Paired Gemini")',timeout=10000)
 assert page.evaluate('visibleAccounts.length===1&&nativeLoginPosts===0')
 assert 'Paired Gemini'in page.locator('#settingsAccounts').text_content()
 browser.close()
print('PASS actual shell: pairing survives transient read failure, checking completes, verified account appears even when logs fail; no native login request')
