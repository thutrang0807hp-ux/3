"""Actual account dialog: native sign-in/close/save instructions and retry ordering."""
import asyncio,re
from pathlib import Path
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
async def main():
 source=(ROOT/'index.html').read_text();start=source.index('async function openAccountWebLogin(');end=source.index('const accountMuseOTP=',start);module=source[start:end]
 fixture='''<meta charset="utf-8"><dialog id="shellDialog"><div id="dialogBody"></div><footer id="footer"></footer></dialog><script>
 const $=s=>document.querySelector(s);const esc=s=>String(s).replaceAll('<','&lt;');const accountName=()=> 'Gemini Chat';const accountRows=()=>[];
 window.calls=[];window.nativeClosed=false;window.saved=false;const toast=()=>{};
 function modal(title,body,footer){$('#dialogBody').innerHTML=body;$('#footer').innerHTML=footer;$('#shellDialog').showModal()}
 const accountScreen=async()=>{window.saved=true};
 async function engineRequest(path,body){calls.push(path);if(path==='gemini-chat/login')return {id:'pending'};if(path==='gemini-chat/confirm'){if(!nativeClosed)throw Error('Đóng cửa sổ Chrome/Edge vừa mở rồi bấm Lưu phiên.');return {id:'account'}}return {};}
 </script><script>'''+module+'</script>'
 async with async_playwright()as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.route('**/*',lambda route:route.fulfill(status=200,body=fixture,content_type='text/html'))
  await page.goto('http://127.0.0.1/account-test');await page.evaluate("openAccountWebLogin('gemini_chat')")
  await expect(page.locator('#accountWebStatus')).to_contain_text('đóng cửa sổ')
  assert await page.evaluate('calls')==['gemini-chat/login']
  await page.locator('#accountWebSave').click();await expect(page.locator('#accountWebStatus')).to_contain_text('Đóng cửa sổ')
  await expect(page.locator('#accountWebSave')).to_be_enabled();assert not await page.evaluate('saved')
  await page.evaluate('nativeClosed=true');await page.locator('#accountWebSave').click();await page.wait_for_function('saved')
  assert await page.evaluate('calls')==['gemini-chat/login','gemini-chat/confirm','gemini-chat/confirm','accounts/update']
  assert not errors,errors;await browser.close()
 print('PASS actual Gemini settings dialog: explicit close/save guidance, no auto-confirm, retry same pending login and save only after confirmation')
asyncio.run(main())
