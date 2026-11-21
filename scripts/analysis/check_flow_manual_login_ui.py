"""Actual saved-Flow UI watches auth state and stops polling on Google rejection."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
async def main():
 source=(ROOT/'index.html').read_text();a=source.index('function watchFlowWebLogin(');b=source.index('async function connectBrowserSession',a);module=source[a:b]
 fixture='''<meta charset="utf-8"><dialog id="shellDialog"><div id="body"></div></dialog><script>
 const $=s=>document.querySelector(s);const esc=s=>String(s).replaceAll('<','&lt;');window.calls=[];window.promoted=false;
 const accountScreen=async()=>{promoted=true};const toast=()=>{};
 function modal(title,body,footer){$('#body').innerHTML=body+footer;$('#shellDialog').showModal()}
 async function engineRequest(path,body){calls.push({path,body});if(path==='accounts/open-profile')return {opened:true,state:'waiting',message:'Đăng nhập Flow rồi đóng cửa sổ đó để ghi phiên.'};return {state:'failed',message:'Google đã từ chối đăng nhập trong cửa sổ này. Chưa nhận tài khoản; app đã dừng.'};}
 </script><script>'''+module+'</script>'
 async with async_playwright()as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
  await page.route('**/*',lambda r:r.fulfill(status=200,body=fixture,content_type='text/html'))
  await page.goto('http://127.0.0.1/flow');await page.evaluate("openFlowWebLogin(null,false,'old-account')")
  await expect(page.locator('#body')).to_contain_text('đóng cửa sổ đăng nhập')
  await expect(page.locator('#flowWebStatus')).to_contain_text('Google đã từ chối',timeout=5000)
  await page.wait_for_timeout(1700)
  result=await page.evaluate('({calls,promoted})');assert result['calls']==[{'path':'accounts/open-profile','body':{'id':'old-account'}},{'path':'flow/web-login','body':None}],result
  assert result['promoted']is False;await browser.close()
 print('PASS saved-account target retained, native-close guidance visible, failed login not promoted or polled repeatedly')
asyncio.run(main())
