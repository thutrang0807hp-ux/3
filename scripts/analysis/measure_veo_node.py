import asyncio,json,sys
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 html=Path(sys.argv[1] if len(sys.argv)>1 else 'workflow.html').read_text()
 async with async_playwright() as pw:
  b=await pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=await b.new_page(viewport={'width':1500,'height':1000})
  async def route(r):
   if '/local-api/' in r.request.url:await r.fulfill(json={'enabled':True,'native_pipeline':True,'selection':{'available':True,'token':'token','account_id':'fixture'},'unresolved':[]});return
   await r.fulfill(content_type='text/html',body=html)
  await page.route('**/*',route);await page.goto('http://127.0.0.1:43891/workflow.html?mode=reference');await page.wait_for_function('!!window.SFVeoNode')
  print(await page.evaluate('''async()=>{
project=blankProject();project.id='perf';project.analysis.frameQualityRequired=false;project.scenes=[];
for(let i=0;i<18;i++){const canvas=document.createElement('canvas');canvas.width=384;canvas.height=682;const ctx=canvas.getContext('2d'),pixels=ctx.createImageData(384,682);let seed=i+1;for(let j=0;j<pixels.data.length;j+=4){seed=(1664525*seed+1013904223)>>>0;pixels.data[j]=seed&255;pixels.data[j+1]=(seed>>>8)&255;pixels.data[j+2]=(seed>>>16)&255;pixels.data[j+3]=255;}ctx.putImageData(pixels,0,0);const image=canvas.toDataURL('image/jpeg',.9),s=sceneRecord(i*8,(i+1)*8,i,[image]);s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',image};s.approvedFrame='source';s.frameSelectionId='source';s.videoPromptOverrides={a:'A gentle movement.'};project.scenes.push(s);}
await storeProject();render();await SFVeoNode.refresh();await new Promise(r=>setTimeout(r,200));
const samples=[];for(let i=0;i<4;i++){const at=performance.now();await SFVeoNode.refresh();document.querySelector('#node-videos').getBoundingClientRect();samples.push(performance.now()-at);}
const before=document.querySelector('#node-videos .vnTile img');await SFVeoNode.refresh();const preserved=before===document.querySelector('#node-videos .vnTile img');
const button=document.querySelector('#node-videos [data-vn=filter-review]'),at=performance.now();button.click();const clickMs=performance.now()-at;await new Promise(r=>setTimeout(r,300));return {refreshMs:samples,clickMs,preserved,imageBytes:project.scenes[0].sourceFrame.image.length};}'''))
  await b.close()
asyncio.run(main())
