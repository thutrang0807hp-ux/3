"""Real workflow UI: seeded product facts, review, stale guards and persistent speech."""
import asyncio,http.server,threading,functools
from pathlib import Path
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
async def main():
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1440,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.goto('http://127.0.0.1:'+str(server.server_port)+'/workflow.html?mode=reference');await page.wait_for_function('window.SFProductScript&&window.SFPromptPipeline&&typeof project!=="undefined"&&project',timeout=5000)
   await page.evaluate('''async()=>{
    project=blankProject();project.id='product-script-ui';project.source={asset:'source',duration:8,name:'reference.mp4'};
    project.script=[{id:'line-a',start:0,end:4,original:'Sản phẩm mẫu chữa bệnh, giá 999 nghìn',translation:'Bản dịch sát mẫu',newText:'Lời tôi đang sửa',faceTalking:true},{id:'line-b',start:4,end:8,original:'Đặt ngay',translation:'Đặt ngay',newText:'Lời cuối cũ'}];
    project.scenes=[sceneRecord(0,4,0,[]),sceneRecord(4,8,1,[])];project.scenes[0].chosen={part:'old'};project.scenes[0].dialogueParts={part:'Lời chia cũ'};project.scenes[0].clips=[{id:'old-version',asset:'old-file',version:1}];
    SFProductScript.setProduct({id:'p1',name:'Áo cotton của tôi',refs:{product:{description:'Cotton, màu xanh'}}});
    window.sent=[];window.requestMode='normal';window.resolveDelayed=null;
    workflowLocalRequest=async(path,body)=>{
     if(path==='ai/script-library/status')return {store_id:'store',ai_source:'gemini_chat'};
     if(path!=='ai/script-library')return {};
     sent.push(structuredClone(body));if(requestMode==='unknown'&&!body.recovery)throw Error('Mất kết nối thử');
     if(requestMode==='delayed')await new Promise(resolve=>resolveDelayed=resolve);
     return {needs_info:false,questions:[],lines:body.reference_lines.map((l,i)=>({id:l.id,new_text:i?'Giá 150 nghìn, xem thêm nhé.':'Áo cotton màu xanh của bạn.',fact_ids:[i?'offer':'facts']})),notes:['Nghe lại nhịp nói']};
    };
    render();await storeProject();scriptDialog();
   }''')
   await expect(page.locator('#modalContent .productScriptBrief')).to_contain_text('Áo cotton của tôi')
   await page.locator('#modalContent [data-product-script=brief]').click()
   await expect(page.locator('[data-product-script-field=name]')).to_have_value('Áo cotton của tôi')
   await expect(page.locator('[data-product-script-field=facts]')).to_have_value('Cotton, màu xanh')
   await page.locator('[data-product-script-field=offer]').fill('150 nghìn')
   await page.locator('[data-product-script-field=avoid]').fill('Không nói chữa bệnh')
   await page.locator('[data-product-script=write]').last.click();await expect(page.locator('#productScriptApply')).to_be_visible()
   payload=await page.evaluate('sent[0]');assert payload['product']['offer']=='150 nghìn'and payload['product']['facts']=='Cotton, màu xanh';assert '999' in payload['reference_lines'][0]['original']
   assert await page.evaluate('project.script[0].newText')=='Lời tôi đang sửa'
   await page.locator('[data-product-script-draft="0"]').fill('Áo cotton xanh, lời tôi đã rà.')
   await page.screenshot(path='/tmp/sceneforge-product-script-review-v125.png')
   await page.locator('#productScriptApply').click()
   data=await page.evaluate('async()=>({script:project.script,scene:project.scenes[0],saved:await readProject(project.id)})')
   assert data['script'][0]['original']=='Sản phẩm mẫu chữa bệnh, giá 999 nghìn'and data['script'][0]['translation']=='Bản dịch sát mẫu'
   assert data['script'][0]['newText']=='Áo cotton xanh, lời tôi đã rà.'and data['script'][0]['start']==0 and data['script'][0]['end']==4
   assert data['scene']['chosen']=={}and data['scene']['dialogueParts']=={}and data['scene']['clips'][0]['id']=='old-version'
   assert data['saved']['productScript']['brief']['offer']=='150 nghìn'and data['saved']['script'][0]['newText']==data['script'][0]['newText']
   # Changed facts while awaiting AI do not overwrite the user's current script.
   await page.evaluate("()=>{requestMode='delayed';SFProductScript.request()}")
   await page.wait_for_function('typeof window.resolveDelayed==="function"')
   await page.evaluate("SFProductScript.brief().facts='Cotton, xanh, thông tin mới';resolveDelayed()")
   await page.wait_for_function('SFProductScript.state().request.state==="received"')
   stale=await page.evaluate('async()=>{try{await SFProductScript.apply();return false}catch(e){return e.message}}');assert 'đổi'in stale
   assert await page.evaluate('project.script[0].newText')=='Áo cotton xanh, lời tôi đã rà.'
   # A failed request can only be recovered with the original frozen payload.
   await page.evaluate("requestMode='unknown';SFProductScript.request()")
   await page.wait_for_function('SFProductScript.state().request.state==="unknown"')
   n=await page.evaluate('sent.length');await page.evaluate('SFProductScript.request()');assert await page.evaluate('sent.length')==n
   await page.evaluate('SFProductScript.request(true)');await page.wait_for_function('SFProductScript.state().request.state==="received"')
   pairs=await page.evaluate('sent.slice(-2)');assert pairs[-1]['recovery']is True and pairs[-2]['request_id']==pairs[-1]['request_id']and pairs[-2]['product']==pairs[-1]['product']
   # Moving to another selected product cannot silently keep the previous facts.
   await page.evaluate("SFProductScript.setProduct({id:'p2',name:'Bình nước',refs:{product:{description:'Dung tích 500 ml'}}});SFProductScript.form()")
   await expect(page.locator('#modalContent')).to_contain_text('sản phẩm khác')
   n=await page.evaluate('sent.length');await page.evaluate('SFProductScript.request()');assert await page.evaluate('sent.length')==n
   await page.locator('#productScriptLoad').click();await expect(page.locator('[data-product-script-field=name]')).to_have_value('Bình nước')
   await expect(page.locator('[data-product-script-field=offer]')).to_have_value('')
   await page.screenshot(path='/tmp/sceneforge-product-script-brief-v125.png')
   # The real shell bridge supplies the selected product on first open and reuse.
   bridge=await browser.new_page();bridge.on('pageerror',lambda e:errors.append(str(e)))
   await bridge.goto('http://127.0.0.1:'+str(server.server_port)+'/workflow.html?room=product-bridge&mode=reference')
   await bridge.wait_for_function('window.SceneForgeWorkflow&&window.SFProductScript&&typeof project!=="undefined"&&project')
   seeded=await bridge.evaluate('''async()=>{await SceneForgeWorkflow.openRoom({id:'product-bridge',name:'Hosted sample',product:{id:'host-product',name:'Sản phẩm từ ngăn',refs:{product:{description:'Thông số đã lưu'}}},refs:project.refs});return SFProductScript.brief()}''')
   assert seeded['name']=='Sản phẩm từ ngăn'and seeded['facts']=='Thông số đã lưu'
   updated=await bridge.evaluate('''async()=>{await SceneForgeWorkflow.openRoom({id:'product-bridge',name:'Hosted sample',reuseLoaded:true,product:{id:'host-product',name:'Sản phẩm từ ngăn',refs:{product:{description:'Thông số vừa cập nhật'}}}});return SFProductScript.brief()}''')
   assert updated['facts']=='Thông số vừa cập nhật'
   assert not errors,errors;await browser.close()
  print('PASS real workflow product prefill/edit, explicit draft review, immutable originals/timing, clip-version preservation, persistent data, stale guard, frozen recovery and changed-product guard')
 finally:server.shutdown()
asyncio.run(main())
