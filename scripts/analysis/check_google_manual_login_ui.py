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
 const accountScreen=async()=>{window.saved=true};let paintAccounts=()=>{};
 async function engineRequest(path,body){calls.push(path);if(path==='gemini-chat/login')return {id:'pending'};if(path==='gemini-chat/login/pending/status')return {state:nativeClosed?(window.rejectCapture?'failed':'done'):'waiting',message:window.rejectCapture?'Chưa kiểm chứng':'Đang chờ'};if(path==='gemini-chat/confirm'){if(window.rejectCapture)throw Error('Chưa kiểm chứng được phiên Gemini');if(!nativeClosed)throw Error('Đóng cửa sổ Chrome/Edge vừa mở rồi bấm Lưu phiên.');return {id:'account'}}return {};}
 </script><script>'''+module+'</script>'
 async with async_playwright()as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.route('**/*',lambda route:route.fulfill(status=200,body=fixture,content_type='text/html'))
  await page.goto('http://127.0.0.1/account-test');await page.evaluate("openAccountWebLogin('gemini_chat')")
  await expect(page.locator('#accountWebStatus')).to_contain_text('đóng cửa sổ')
  assert await page.evaluate('calls')==['gemini-chat/login']
  await expect(page.locator('#accountWebSave')).to_be_hidden()
  await page.wait_for_timeout(1200);assert 'gemini-chat/confirm'not in await page.evaluate('calls');assert not await page.evaluate('saved')
  await page.evaluate('nativeClosed=true');await page.wait_for_function('saved')
  calls=await page.evaluate('calls');assert 'gemini-chat/confirm'not in calls,calls
  await page.reload();await page.evaluate("rejectCapture=true;openAccountWebLogin('gemini_chat')");await page.evaluate('nativeClosed=true')
  await expect(page.locator('#accountWebSave')).to_be_visible(timeout=5000)
  await expect(page.locator('#accountWebStatus')).to_contain_text('Chưa kiểm chứng')
  assert not await page.evaluate('saved');await page.wait_for_timeout(1200)
  assert (await page.evaluate('calls')).count('gemini-chat/confirm')==0
  await page.evaluate('rejectCapture=false');await page.locator('#accountWebSave').click();await page.wait_for_function('saved')
  await page.reload();await page.evaluate("openAccountWebLogin('gemini_chat')");await page.locator('#accountWebBack').click();await page.wait_for_timeout(1200)
  assert 'gemini-chat/confirm'not in await page.evaluate('calls');assert 'gemini-chat/login/pending/cancel'not in await page.evaluate('calls')
  assert not errors,errors;await browser.close()
 print('PASS actual Gemini settings dialog: no Save step, no capture before close, automatic confirmation once after close')
asyncio.run(main())
