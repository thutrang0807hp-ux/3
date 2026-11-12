"""Actual intake module stores selection evidence and warns on a marked fallback."""
import asyncio,re
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
async def main():
 source=(ROOT/'index.html').read_text();module=re.search(r'<script id="video-intake-js">([\s\S]*?)</script>',source).group(1)
 fixture='''<dialog id="shellDialog"></dialog><script>
 const rooms=[],prefs={product:'p'};const esc=s=>String(s).replaceAll('<','&lt;');
 const g6ActiveProducts=()=>[{id:'p',name:'Test'}];const productFor=()=>({id:'p',name:'Test'});
 window.messages=[];const toast=t=>messages.push(t);const fail=e=>{throw e};window.SceneForgeApp={};window.calls=[];
 function modal(title,body,footer){let d=document.querySelector('#shellDialog');d.innerHTML=body+footer;if(!d.open)d.showModal();}
 const videoInfo=async()=>({width:160,height:90,duration:1});
 const importVideos=async()=>{const r={id:'r',stage:'review',mode:'reference',productId:'p'};rooms.push(r);return [r]};
 const persistRoom=async r=>{window.saved={...r}};const openRoom=async id=>{window.opened=id};
 async function engineRequest(path,body){calls.push(path);if(path.endsWith('/release'))return {released:true};if(!body)return {jobs:[]};return {id:'video-job',state:'done',mime:'video/mp4',name:'test.mp4',sha256:'a'.repeat(64),tiktok_source_kind:'watermarked',tiktok_source_policy:'playback-v1',source_notice:'Nguồn TikTok chỉ có bản được đánh dấu có watermark. Video đã tải giữ logo; app chưa xóa logo khỏi hình.'};}
 </script><script>'''+module+'</script>'
 async with async_playwright()as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
  async def route(r):
   if r.request.url.endswith('/file'):await r.fulfill(status=200,body=b'VIDEO FIXTURE',content_type='video/mp4')
   else:await r.fulfill(status=200,body=fixture,content_type='text/html')
  await page.route('**/*',route);await page.goto('http://127.0.0.1/intake');await page.evaluate('SceneForgeApp.videoIntake.open()')
  await page.evaluate("async()=>{const key=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode('https://vt.tiktok.com/test')))].map(v=>v.toString(16).padStart(2,'0')).join('');rooms.push({id:'old',stage:'review',mode:'reference',productId:'p',sourceURLKey:key})}")
  await page.locator('#viURL').fill('https://vt.tiktok.com/test');await page.locator('#viDownload').click()
  await page.wait_for_function('window.opened==="r"&&window.messages.length>0')
  result=await page.evaluate('({saved,messages,calls})')
  assert result['saved']['sourceTikTokKind']=='watermarked'and result['saved']['sourceTikTokPolicy']=='playback-v1'and result['saved']['sourceNotice']in result['messages'],result
  assert result['calls']==['video-import/jobs','video-import/jobs','video-import/jobs/video-job/release'],result
  await browser.close()
 print('PASS actual intake UI persists marked fallback and shows explicit notice; no extra service calls')
asyncio.run(main())
