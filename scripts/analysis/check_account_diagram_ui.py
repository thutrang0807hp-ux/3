"""Connected account diagram with bounded labels and direct row removal."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright,expect
ROOT=Path('/workspace/3')
async def main():
 html=(Path('index.html')if Path('index.html').exists()else ROOT/'index.html').read_text();services=['flow','muse','gemini_chat','grok','chatgpt','meta'];accounts=[{'id':s+'-'+str(i),'service':s,'name':('very.long.account.name.'*8)+str(i)+'@example.invalid · trình duyệt riêng','enabled':True,'state':'ready','session_verified':True,'active':i==0,'priority':i,'credit':1006,'successes':4,'failures':2,'note':'Một ghi chú rất dài '*20}for s in services for i in range(4)];posts=[];deny=False;accept=True
 async with async_playwright()as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':1440,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  async def route(r):
   nonlocal accounts
   if '/local-api/'not in r.request.url:
    await r.fulfill(body=html,content_type='text/html')if r.request.resource_type=='document'else await r.fulfill(status=404,body='');return
   path=r.request.url.split('/local-api/')[1];body=r.request.post_data_json if r.request.method=='POST'else{}
   if r.request.method=='POST':posts.append((path,body))
   if path=='status':await r.fulfill(json={'accounts':accounts,'logs':[],'engines':{s:{'installed':True,'adapter':True,'selection':{'mode':'selected','available':True,'account_id':s+'-0'}}for s in services},'rotation':{}})
   elif path=='system':await r.fulfill(json={'engines':[]})
   elif path=='logs':await r.fulfill(json=[])
   elif path=='browser-bridge/google-status':await r.fulfill(json={'shared':False,'services':{s:{'ready':True,'mode':'selected'}for s in ['flow','gemini_chat']}})
   elif path=='accounts/remove':
    if deny:await r.fulfill(status=409,json={'detail':'Tài khoản đang chạy; chưa thể gỡ.'})
    else:accounts=[a for a in accounts if a['id']!=body['id']];await r.fulfill(json={'ok':True})
   elif path=='accounts/update':
    for a in accounts:
     if a['id']==body['id']:a.update({k:v for k,v in body.items()if k!='id'})
    await r.fulfill(json={'ok':True})
   elif path=='accounts/use':
    selected=next(a for a in accounts if a['id']==body['id'])
    for a in accounts:
     if a['service']==selected['service']:a['active']=a['id']==body['id']
    await r.fulfill(json={'ok':True})
   else:await r.fulfill(json={})
  async def on_dialog(d):await d.accept()if accept else await d.dismiss()
  page.on('dialog',on_dialog);await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/');await page.wait_for_function('appBootReady');await page.evaluate('async()=>{prefs.package5WelcomeDone=true;await savePrefs();document.querySelector("#shellDialog").close();await accountScreen("flow")}')
  await expect(page.locator('[data-account-remove-direct]')).to_have_count(4);await expect(page.locator('#flowWebLogin')).to_have_count(0);await expect(page.locator('#connectAccount')).to_have_count(1)
  await expect(page.locator('.acctCompactTable th')).to_have_count(6);await expect(page.locator('.acctGraphNode')).to_have_count(4);await expect(page.locator('.acctGraph svg path')).to_have_count(4);await expect(page.locator('.acctEngine')).to_have_count(1)
  assert await page.locator('.acctCompactTable').evaluate('e=>e.scrollWidth<=e.parentElement.clientWidth+2')
  assert await page.locator('.acctGraph').evaluate('e=>e.scrollWidth<=e.clientWidth+2')
  assert await page.locator('.acctGraphNode').first.get_attribute('title')==accounts[0]['name']
  boxes=await page.locator('.acctGraphNode,.acctEngine').evaluate_all('els=>els.map(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})')
  for i,a in enumerate(boxes):
   for b0 in boxes[i+1:]:assert min(a['x']+a['w'],b0['x']+b0['w'])-max(a['x'],b0['x'])<=1 or min(a['y']+a['h'],b0['y']+b0['h'])-max(a['y'],b0['y'])<=1,boxes
  assert await page.locator('.acctGraphNode b').first.evaluate('e=>e.scrollWidth>e.clientWidth&&getComputedStyle(e).textOverflow==="ellipsis"')
  assert await page.locator('.acctIdentity b').first.get_attribute('title')==accounts[0]['name']
  # Account details remain accessible without increasing the table width.
  await page.locator('.acctRowDetails summary').first.click();await expect(page.locator('.acFullName').first).to_have_text(accounts[0]['name']);await page.locator('.acctRowDetails summary').first.click()
  await page.locator('.acctTopGrid').scroll_into_view_if_needed();await page.screenshot(path='/tmp/sceneforge-diagram-accounts-graph-v92.png');await page.locator('.acctCompactTable').scroll_into_view_if_needed();await page.screenshot(path='/tmp/sceneforge-diagram-accounts-v92.png')
  # Cancelling the direct confirmation does not call remove or open Edit.
  accept=False;await page.locator('[data-account-remove-direct="flow-1"]').click();assert not any(path=='accounts/remove'for path,_ in posts);await expect(page.locator('#accountEditName')).to_have_count(0)
  accept=True;deny=True;await page.locator('[data-account-remove-direct="flow-1"]').click();await expect(page.locator('[data-account-remove-direct="flow-1"]')).to_be_enabled();assert len(accounts)==24
  deny=False;await page.locator('[data-account-remove-direct="flow-1"]').click();await expect(page.locator('[data-account-row="flow-1"]')).to_have_count(0);assert len(accounts)==23 and next(a for a in accounts if a['id']=='flow-0')['active'];assert any(path=='accounts/remove'and body=={'id':'flow-1'}for path,body in posts)
  await page.locator('[data-check-account="flow-2"]').click();assert any(path=='accounts/check'and body['id']=='flow-2'for path,body in posts)
  await page.locator('[data-use-account="flow-2"]').click();await expect(page.locator('[data-account-row="flow-2"]')).to_have_class('current');await page.locator('[data-account-edit="flow-2"]').click();await expect(page.locator('#accountEditName')).to_be_visible();await page.locator('#accountEditBack').click()
  await page.set_viewport_size({'width':600,'height':900});await page.locator('.acctCompactTable').scroll_into_view_if_needed();await page.screenshot(path='/tmp/sceneforge-diagram-accounts-mobile-v92.png');assert await page.locator('.g5SettingsScroll').evaluate('e=>e.scrollWidth<=e.clientWidth+2')
  for service in services[1:]:
   await page.evaluate('(s)=>accountScreen(s)',service);await expect(page.locator('[data-account-remove-direct]')).to_have_count(4);assert await page.locator('.acctGraph').evaluate('e=>e.scrollWidth<=e.clientWidth+2')
  assert not errors,errors;assert not any('/jobs'in path or '/generate'in path for path,_ in posts);await b.close()
 print('PASS connected account diagram restored, nodes do not overlap, long labels bounded with tooltips; six columns and mobile cards; direct remove confirmation cancel/error/success targets correct account; no Edit detour; check/use/edit preserved; all six services; no generation. Mocked accounts only.')
if __name__=='__main__':asyncio.run(main())
