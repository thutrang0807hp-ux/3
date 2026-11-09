"""Browser bounds for long captions in a tiny node; original text/settings retained."""
from review_ui_helpers import ensure_review_tab
import asyncio,re
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 html=Path('workflow.html').read_text();text='Bàn chải ở nhà mà xơ xác, cùn mòn rồi, thì ghé đây sắm set mới về xài liền đi. '*12
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':1450,'height':1000})
  async def route(r):
   if '/local-api/' in r.request.url:await r.fulfill(json={});return
   await r.fulfill(body=html,content_type='text/html')
  await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFAudioNodes&&!!window.SceneForgeWorkflow')
  await page.evaluate('''async text=>{project=blankProject();project.id='caption-scale';project.scenes=[sceneRecord(0,8,0,['data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'])];project.merge.captions=true;project.merge.captionWords=0;project.merge.captionSize=37;project.merge.captionY=80;project.merge.captionDraft=[{start:0,end:8,text,manual:true}];document.body.classList.add('compactWorkspaceFrame');render();await SFAudioNodes.refresh();const n=document.querySelector('#node-captions');view.z=1;view.x=30-n.offsetLeft;view.y=50-n.offsetTop;applyView();}''',text)
  node=page.locator('#node-captions')
  async def measure():return await node.locator('.anCaption').evaluate('''el=>{const c=getComputedStyle(el),r=el.getBoundingClientRect(),p=el.parentElement.getBoundingClientRect();return {font:parseFloat(c.fontSize),height:r.height,width:r.width,pictureWidth:p.width,pictureHeight:p.height,line:parseFloat(c.lineHeight),top:r.top-p.top,bottom:r.bottom-p.top,clamp:c.webkitLineClamp,text:el.textContent}}''')
  initial=await measure();assert initial['font']<10 and initial['clamp']=='2'
  assert abs(initial['font']-(initial['pictureWidth']-2)*37/1080)<.2,initial
  values=[]
  for size in [28,37,64,100]:
   await node.locator('[data-an-field=size]').evaluate('(el,v)=>{el.value=v;el.dispatchEvent(new Event("input",{bubbles:true}))}',size)
   m=await measure();values.append(m['font']);assert m['height']<=m['line']*2+.5 and m['height']/m['pictureHeight']<.16 and m['top']>=0 and m['bottom']<=m['pictureHeight'] and m['text']==text,m
  assert all(a<b for a,b in zip(values,values[1:])),values
  assert await page.evaluate('project.merge.captionDraft[0].text')==text
  await node.locator('[data-an-field=size]').evaluate('(el)=>{el.value=37;el.dispatchEvent(new Event("input",{bubbles:true}))}')
  assert await page.evaluate('project.merge.captionSize===37&&project.merge.captionY===80&&project.merge.captionDraft[0].manual')
  await b.close()
 for tag,id in [('script','audio-nodes-js'),('style','audio-nodes-css')]:
  pattern='<'+tag+' id="'+id+'">(.*?)</'+tag+'>';assert re.search(pattern,html,re.S)[1]==re.search(pattern,Path('photos.html').read_text(),re.S)[1]
 print('PASS long caption preview limited to 2 lines; 28/37/64/100 scale to picture width without 10px floor; stays inside frame; full manual text/timing/settings retained; workflow/photos modules match')
if __name__=='__main__':asyncio.run(main())
