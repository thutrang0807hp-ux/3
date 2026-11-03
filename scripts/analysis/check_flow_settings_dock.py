"""Real Chromium, same-origin shell/worker fixture. No backend or Google calls."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
 html=Path('workflow.html').read_text()
 code=html[html.index('let flowSettingsDock=null;'):html.index('function preparedContext(row)')]
 fixture="""let project={id:'room',mode:'reference'};let remote={selection:{available:true,account_id:'account',token:'token'}};
let busy=false,settingsSyncTimer=null,settingsSyncPending=null,settingsSyncStarting=false,error='';
let data={};window.calls=[];window.failSave=false;
const state=()=>data,active=()=>false,paint=()=>paintFlowSettingsDock(),assertRoom=id=>{if(id!==project.id)throw Error('room changed')},storeProject=async()=>{if(window.failSave)throw Error('fixture save failed')},escape=s=>String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;'),button=(action,text)=>'<button data-vn="'+action+'">'+text+'</button>';
async function workflowLocalRequest(path,body){
 window.calls.push({path,body});
 if(path==='flow/simple/status')return {selection:remote.selection,active_request:null};
 if(body){if(window.failSync)throw Error('fixture save failed');return {request_id:'settings',state:'running',message:'Applying',room_id:'room',account_id:'account',requested:body.settings};}
 return {request_id:'settings',state:'verified',message:'Verified',room_id:'room',account_id:'account',requested:{...flowSettings()}};
}
"""
 worker='<html><body><div id="node-videos"></div><script>'+fixture+code+'\npaintFlowSettingsDock();</script></body></html>'
 parent='''<html><head><style>body{margin:0;background:#101216;color:white;font:13px sans-serif}.roomBar{height:56px;display:flex;align-items:center}.roomBar nav{display:flex;align-items:center}iframe{width:100%;height:650px;border:0}</style></head><body><div id="roomWorkspace"><div class="roomBar"><nav><button>Tạo video</button><button>Dựng</button></nav></div><iframe id="workflowFrame" src="/worker"></iframe></div></body></html>'''
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=await browser.new_page(viewport={'width':1100,'height':800})
  errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  await page.route('**/*',lambda route:route.fulfill(content_type='text/html; charset=utf-8',body=worker if route.request.url.endswith('/worker') else parent))
  await page.goto('http://fixture.test/')
  dock=page.locator('#sfFlowSettingsDock');await dock.wait_for()
  assert await dock.count()==1 and not await dock.locator('.sfFlowSettingsPanel').is_visible()
  frame=page.frames[1]
  assert await frame.locator('[data-vn-settings]').count()==0
  await dock.locator('summary').click()
  assert await dock.locator('.sfFlowSettingsPanel').is_visible()
  assert await dock.locator('[data-vn-setting]').count()==1
  assert await dock.locator('[data-flow-choice=outputs][data-value="2"]').is_disabled()
  assert await dock.locator('[data-vn="apply-settings"],[data-vn="settings-report"]').count()==0
  await dock.locator('[data-flow-choice=ratio][data-value="16:9"]').click()
  await frame.wait_for_function("()=>data.settingsTrial?.state==='saved'&&data.settingsTrial.requested.ratio==='16:9'")
  calls=await frame.evaluate('window.calls')
  posts=[call for call in calls if call.get('body')]
  assert not calls,calls
  assert await dock.locator('option[value=quality]').evaluate('e=>e.disabled')
  await dock.locator('[data-flow-choice=mode][data-value=frames]').click()
  await dock.locator('[data-vn-setting=model]').select_option('quality')
  await frame.wait_for_function("()=>data.settingsTrial?.requested.model==='quality'")
  assert await dock.locator('[data-flow-choice=mode][data-value=ingredients]').is_disabled()
  await frame.evaluate('window.failSave=true')
  await dock.locator('[data-flow-choice=ratio][data-value="9:16"]').click()
  await page.wait_for_function("()=>document.querySelector('#sfFlowSettingsDock [role=status]')?.textContent.includes('fixture save failed')")
  assert await dock.get_attribute('data-sync')=='error'
  assert await dock.locator('[data-vn="apply-settings"],[data-vn="settings-report"]').count()==0
  await page.keyboard.press('Escape');assert not await dock.locator('.sfFlowSettingsPanel').is_visible()
  await dock.locator('summary').click();await page.get_by_role('button',name='Dựng',exact=True).click()
  assert not await dock.locator('.sfFlowSettingsPanel').is_visible()
  await page.evaluate("()=>{const f=document.createElement('iframe');f.id='parked-worker';f.src='/worker';f.hidden=true;document.body.append(f)}")
  await page.wait_for_function("()=>document.querySelectorAll('iframe').length===2&&document.querySelector('#parked-worker').contentDocument?.readyState==='complete'")
  assert await page.locator('#sfFlowSettingsDock').count()==1 and await dock.is_visible()
  await page.set_viewport_size({'width':600,'height':800});await dock.locator('summary').click()
  box=await dock.locator('.sfFlowSettingsPanel').bounding_box()
  assert box and box['x']>=0 and box['x']+box['width']<=600,box
  assert not errors,errors
  await browser.close()
 print('PASS actual shell/iframe dock: collapsed, selected settings saved for CLI without Settings endpoint calls, no removed buttons, errors visible, Escape/outside close, parked worker isolation, narrow viewport')

if __name__=='__main__':asyncio.run(main())
