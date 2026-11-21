"""Actual inspector shows live writer wait, read-only refresh, stop, and completion."""
import asyncio,http.server,threading,functools
from pathlib import Path
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
async def main():
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html?mode=reference');await page.wait_for_function('window.SFPromptPipeline&&window.SFMediaNodes')
   await page.evaluate('''async()=>{
    const c=document.createElement('canvas');c.width=c.height=16;c.getContext('2d').fillRect(0,0,16,16);const source=c.toDataURL();
    project=blankProject();project.id='inspector-progress';project.source={poster:source};project.script=[];const s=sceneRecord(0,4,0,[source]);s.refsUsed=[];s.promptFrame={vi:'Khung cũ',en:'Old composition'};project.scenes=[s];
    storeProject=async()=>{};SFProviderReceipts.persistIntent=async()=>{};window.posts=[];window.writerMode='wait';window.remoteState='running';
    window.writerReply={state:'done',result:{text:JSON.stringify({promptFrame:{vi:'Khung mới đã cập nhật',en:'Fresh composition'},used_refs:['R1'],warnings:[]})}};
    workflowLocalRequest=async(path,body)=>{if(path==='gemini-chat/status')return {installed:true,selection:{available:true,token:'same'}};if(path==='gemini-chat/jobs'){posts.push(body);return writerMode==='wait'?new Promise(r=>window.releaseWriter=r):writerReply;}if(path.startsWith('gemini-chat/jobs/'))return writerMode==='done'?writerReply:{state:remoteState};return {};};render();
   }''')
   await page.locator('#node-frames [data-mn=open]').first.click();panel=page.locator('[data-frame-inspector-progress]')
   await expect(panel).to_contain_text('Viết prompt: Chưa có lượt')
   await page.locator('[data-mn=prepare-image-prompt]').click();await page.wait_for_function('typeof releaseWriter==="function"')
   await expect(panel).to_contain_text('ĐANG HOẠT ĐỘNG',timeout=4000)
   assert await panel.locator('progress').get_attribute('value')is None
   count=await page.evaluate('posts.length')
   await page.locator('#modal > header [data-action=close-modal]').click()
   await expect(page.locator('#node-frames [data-mn=open]').first).to_be_enabled()
   await page.locator('#node-frames [data-mn=open]').first.click()
   await expect(panel).to_contain_text('ĐANG HOẠT ĐỘNG')
   assert await page.evaluate('posts.length')==count
   await panel.locator('[data-mn=frame-inspector-refresh]').click()
   await expect(panel).to_contain_text('Động cơ báo đang xử lý');assert await page.evaluate('posts.length')==count
   await panel.locator('[data-mn=pause-frames]').click();await page.wait_for_function('!SFPromptPipeline.isRunning()')
   await expect(panel).not_to_contain_text('ĐANG HOẠT ĐỘNG')
   await page.evaluate("remoteState='failed'");await panel.locator('[data-mn=frame-inspector-refresh]').click();await expect(panel).to_contain_text('Thất bại')
   await page.evaluate("writerMode='done'");await page.locator('[data-mn=prepare-image-prompt]').click();await expect(panel).to_contain_text('Đã cập nhật prompt')
   await expect(page.locator('#mnVietnamesePrompt')).to_have_value('Khung mới đã cập nhật')
   await page.evaluate('releaseWriter(writerReply)');await page.wait_for_timeout(100)
   assert await page.evaluate('posts.filter(x=>x.kind==="image").length')==0
   await page.evaluate('''()=>{writerMode='wait';const original=window.setTimeout;window.setTimeout=(fn,ms,...args)=>original(fn,ms===90000?40:ms,...args);}''')
   await page.locator('[data-mn=prepare-image-prompt]').click()
   await page.wait_for_function('!SFPromptPipeline.isRunning()')
   await expect(panel).to_contain_text('chưa rõ kết quả')
   count=await page.evaluate('posts.length')
   await page.locator('#modal > header [data-action=close-modal]').click()
   await page.locator('#node-frames [data-mn=open]').first.click()
   await expect(panel).to_contain_text('chưa rõ kết quả')
   assert await page.evaluate('posts.length')==count
   assert not errors,errors;await browser.close()
  print('PASS inspector indeterminate progress, live status, read-only refresh while waiting, stop, completed prompt and no unintended media dispatch')
 finally:server.shutdown()
asyncio.run(main())
