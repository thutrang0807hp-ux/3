"""Run the actual intake script and download its sanitized failure report."""
import asyncio,json,re,tempfile
from pathlib import Path
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
async def main():
 source=(ROOT/'index.html').read_text();module=re.search(r'<script id="video-intake-js">([\s\S]*?)</script>',source).group(1)
 fixture='''<dialog id="shellDialog"></dialog><script>
 const rooms=[],prefs={product:'p'};const esc=s=>String(s).replaceAll('<','&lt;');
 const g6ActiveProducts=()=>[{id:'p',name:'Test'}];const productFor=()=>({id:'p',name:'Test'});
 const toast=()=>{};const fail=e=>{throw e};window.SceneForgeApp={};window.calls=[];
 function modal(title,body,footer){let d=document.querySelector('#shellDialog');d.innerHTML=body+footer;if(!d.open)d.showModal();}
 async function engineRequest(path,body){calls.push({path,method:body?'POST':'GET'});if(!body)return {jobs:[]};return {id:'failed-source',state:'error',error:'Unsupported source formats',url:'PRIVATE_URL',http_headers:{Cookie:'PRIVATE_COOKIE'},source_diagnostics:{extractor:'TikTok',format_count:1,formats:[{protocol:'m3u8_native',has_url:true}]}};}
 </script><script>'''+module+'</script>'
 async with async_playwright()as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(accept_downloads=True)
  await page.route('**/*',lambda route:route.fulfill(status=200,body=fixture,content_type='text/html'))
  await page.goto('http://127.0.0.1/intake');await page.evaluate('SceneForgeApp.videoIntake.open()')
  await page.locator('#viURL').fill('https://vt.tiktok.com/test');await page.locator('#viDownload').click()
  await expect(page.locator('#viStatus')).to_contain_text('Unsupported source formats')
  await expect(page.locator('#viSourceReport')).to_be_enabled()
  async with page.expect_download()as pending:await page.locator('#viSourceReport').click()
  download=await pending.value;raw=Path(await download.path()).read_text();report=json.loads(raw)
  assert report['source_diagnostics']['extractor']=='TikTok'and 'PRIVATE'not in raw
  calls=await page.evaluate('calls');assert len(calls)==2 and all(c['path']=='video-import/jobs'for c in calls),calls
  await browser.close()
 print('PASS actual intake UI displays error, exports source diagnostics, strips unrelated URL/cookies and never calls generation')
asyncio.run(main())
