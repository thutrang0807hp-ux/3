"""Web login UI dispatch, retries and cleanup; mocked services, no Google login claimed."""
import asyncio,ast,copy,time
from pathlib import Path
from types import SimpleNamespace
from fastapi import HTTPException
from playwright.async_api import async_playwright,expect
ROOT=Path('/workspace/3')

def source(name):
 p=Path('local_engine')/name
 return p if p.exists()else ROOT/'veo-node-v46/local_engine'/name

async def backend_checks():
 tree=ast.parse(source('server.py').read_text());nodes=[copy.deepcopy(n)for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))and n.name in ['save_login','cancel_account_login']]
 for n in nodes:n.decorator_list=[]
 class Vault:
  def __init__(self):self.accounts={};self.secrets={}
  def set_secret(self,k,v):self.secrets[k]=v
  def delete_secret(self,k):self.secrets.pop(k,None)
  def delete(self,table,k):self.accounts.pop(k,None)
  def put(self,table,row):self.accounts[row['id']]=dict(row)
 vault=Vault();logins={};ns={'asyncio':asyncio,'time':time,'HTTPException':HTTPException,'VAULT':vault,'LOGINS':logins,'account':lambda k:dict(vault.accounts[k])};exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'actual-server-login','exec'),ns)
 class Browser:
  def __init__(self):self.closed=0
  async def close(self):self.closed+=1
  async def stop(self):pass
 browser=Browser();gate=asyncio.Event();entered=asyncio.Event()
 async def cookies():entered.set();await gate.wait();return [{'domain':'.muse.ai','name':'session','value':'PRIVATE','expires':-1},{'domain':'.other.invalid','name':'other','value':'DO_NOT_SAVE'}]
 vault.accounts['A']={'id':'A','service':'muse','state':'awaiting_login'};logins['A']={'browser':browser,'playwright':browser,'context':SimpleNamespace(cookies=cookies)}
 save=asyncio.create_task(ns['save_login']({'id':'A'}));await entered.wait();cancel=asyncio.create_task(ns['cancel_account_login']({'id':'A'}));await asyncio.sleep(.02);assert not cancel.done();gate.set();await save;result=await cancel;assert not result['cancelled'];assert vault.accounts['A']['state']=='unverified'and len(vault.secrets['account:A']['cookies'])==1 and browser.closed==1
 async def empty():return []
 vault.accounts['B']={'id':'B','service':'muse','state':'awaiting_login'};b=Browser();logins['B']={'browser':b,'playwright':b,'context':SimpleNamespace(cookies=empty)}
 try:await ns['save_login']({'id':'B'});assert False
 except HTTPException as e:assert e.status_code==400
 assert 'B'in logins and b.closed==0;await ns['cancel_account_login']({'id':'B'});assert 'B'not in vault.accounts and 'A'in vault.accounts
 tree=ast.parse(source('gemini_chat.py').read_text());klass=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='GeminiChat');method=copy.deepcopy(next(n for n in klass.body if isinstance(n,ast.AsyncFunctionDef)and n.name=='confirm'));ns={'HTTPException':HTTPException};exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'actual-gemini-confirm','exec'),ns);attempt=0;closed=[]
 async def imported(name,cookies):
  nonlocal attempt
  attempt+=1
  if attempt==1:raise HTTPException(409,'Finish signing in')
  return {'id':'saved'}
 async def gcookies():return [{'name':'test','value':'PRIVATE'}]
 async def cancel(id):closed.append(id);obj.logins.pop(id,None)
 obj=SimpleNamespace(logins={'pending':{'name':'Gemini','context':SimpleNamespace(cookies=gcookies)}},import_session=imported,cancel_login=cancel)
 try:await ns['confirm'](obj,{'id':'pending'});assert False
 except HTTPException:pass
 assert 'pending'in obj.logins and not closed;assert(await ns['confirm'](obj,{'id':'pending'}))['id']=='saved'and closed==['pending']

async def main():
 await backend_checks();html=(Path('index.html')if Path('index.html').exists()else ROOT/'index.html').read_text();posts=[];accounts=[];fail=True;delay=False;opening=asyncio.Event();release=asyncio.Event()
 services=['flow','muse','gemini_chat','grok','chatgpt','meta']
 async with async_playwright()as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':1440,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  async def route(r):
   nonlocal fail
   if '/local-api/'not in r.request.url:
    await r.fulfill(body=html,content_type='text/html')if r.request.resource_type=='document'else await r.fulfill(status=404,body='');return
   path=r.request.url.split('/local-api/')[1];body=r.request.post_data_json if r.request.method=='POST'else{}
   if r.request.method=='POST':posts.append((path,body))
   if path=='status':await r.fulfill(json={'accounts':accounts,'logs':[],'engines':{s:{'installed':True,'adapter':True,'selection':{'mode':'selected','available':False}}for s in services},'rotation':{}})
   elif path=='logs':await r.fulfill(json=[])
   elif path=='system':await r.fulfill(json={'engines':[]})
   elif path=='browser-bridge/google-status':await r.fulfill(json={'shared':False,'services':{s:{'ready':False,'mode':'selected'}for s in ['flow','gemini_chat']}})
   elif path=='gemini-chat/login':
    opening.set()
    if delay:await release.wait()
    await r.fulfill(json={'id':'pending-gemini','awaiting_login':True})
   elif path=='gemini-chat/confirm':
    if fail:fail=False;await r.fulfill(status=409,json={'detail':'Hoàn tất đăng nhập trước'})
    else:accounts.append({'id':'saved-gemini','service':'gemini_chat','name':'Gemini Chat','state':'ready','enabled':True,'active':True});await r.fulfill(json={'id':'saved-gemini'})
   elif path.startswith('accounts/fingerprint/'):
    await r.fulfill(json={'enabled':body.get('enabled',False),'cores':body.get('cores',8),'memory':body.get('memory',8),'width':body.get('width',1280),'height':body.get('height',800),'id':'fixture-fingerprint'})
   elif path=='accounts/connect':await r.fulfill(json={'id':'pending-muse'})
   elif path=='accounts/save-login':accounts.append({'id':'pending-muse','service':'muse','name':'Muse','state':'unverified','enabled':True});await r.fulfill(json={'saved':True})
   elif path=='accounts/check':await r.fulfill(status=409,json={'detail':'SDK not ready'})
   elif path.startswith('web-images/')and path.endswith('/login'):await r.fulfill(json={'login_id':'pending-'+path.split('/')[1]})
   elif path.startswith('web-images/login/')and path.endswith('/save'):await r.fulfill(json={'id':'saved-image'})
   elif path=='flow/web-login':await r.fulfill(json={'state':'waiting','message':'Đăng nhập Flow'})
   else:await r.fulfill(json={})
  await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/');await page.wait_for_function('appBootReady');await page.evaluate('async()=>{prefs.package5WelcomeDone=true;await savePrefs();document.querySelector("#shellDialog").close();await accountScreen("gemini_chat")}')
  await expect(page.locator('#connectAccount')).to_have_text('Đăng nhập trên web');await page.locator('#connectAccount').click();await expect(page.locator('#accountWebSave')).to_be_enabled();assert not any('pairs'in path for path,_ in posts)
  await page.locator('#accountWebSave').click();await expect(page.locator('#accountWebStatus')).to_contain_text('Hoàn tất đăng nhập');await expect(page.locator('#accountWebSave')).to_be_enabled();assert not any(path.endswith('/cancel')for path,_ in posts)
  await page.locator('#accountWebSave').click();await expect(page.locator('#connectAccount')).to_be_visible();assert sum(path=='gemini-chat/login'for path,_ in posts)==1 and sum(path=='gemini-chat/confirm'for path,_ in posts)==2
  await page.evaluate('accountScreen("gemini_chat")');await expect(page.locator('.acctAccounts')).to_contain_text('Gemini Chat');assert sum(path=='gemini-chat/login'for path,_ in posts)==1
  for service in ['grok','chatgpt','meta','muse']:
   await page.evaluate('(s)=>accountScreen(s)',service)
   await page.locator('#connectAccount').click();await expect(page.locator('#accountWebSave')).to_be_enabled();await page.screenshot(path='/tmp/sceneforge-account-web-'+service+'-v90.png')
   if service=='muse':await page.locator('#accountWebSave').click();await expect(page.locator('#connectAccount')).to_be_visible();assert not any(path=='accounts/cancel-login'for path,_ in posts)
   else:await page.locator('#accountWebBack').click();await expect(page.locator('#connectAccount')).to_be_visible();assert any(path=='web-images/login/pending-'+service+'/close'for path,_ in posts)
  await page.evaluate('accountScreen("flow")');await page.locator('#connectAccount').click();await expect(page.locator('#flowWebStatus')).to_contain_text('Đăng nhập Flow');assert any(path=='flow/web-login'for path,_ in posts)
  # Reopen passes the existing logical account id rather than creating a new profile.
  accounts.append({'id':'meta-profile','service':'meta','name':'Meta saved','state':'ready','enabled':True});await page.evaluate('accountScreen("meta")');await page.locator('[data-account-profile="meta-profile"]').click();await expect(page.locator('#accountWebSave')).to_be_enabled();assert any(path=='web-images/meta/login'and body.get('account_id')=='meta-profile'for path,body in posts);await page.locator('#accountWebBack').click()
  await page.locator('[data-account-fingerprint="meta-profile"]').click();await expect(page.locator('#fpEnabled')).not_to_be_checked();await page.locator('#fpEnabled').check();await page.locator('#fpCores').select_option('12');await page.locator('#fpSave').click();await expect(page.locator('#fpStatus')).to_contain_text('Đã bật');assert any(path=='accounts/fingerprint/meta-profile'and body.get('cores')==12 and body.get('enabled')is True for path,body in posts);await page.locator('#fpBack').click()
  # Closing while browser launch is pending cleans up the late login, never shows it in the next tab.
  delay=True;opening.clear();await page.evaluate('accountScreen("gemini_chat")');await page.locator('#connectAccount').click();await opening.wait();await page.locator('#accountWebBack').click();release.set();await page.wait_for_timeout(200);assert any(path=='gemini-chat/login/pending-gemini/cancel'for path,_ in posts)
  assert not any('/jobs'in path or path.endswith('/generate')or 'pairs'in path for path,_ in posts);assert not errors,errors;await b.close()
 print('PASS six-service web-login dispatch without pairing codes; Gemini retry keeps window; saved sessions reused; pending/late login cleanup; Muse save/cancel serialization preserves saved account; no generation; mocked provider verification only')
if __name__=='__main__':asyncio.run(main())
