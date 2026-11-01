"""Real Chromium settings readback using the visible Flow layout supplied by the user."""
import asyncio
from playwright.async_api import async_playwright
from .simple_flow_settings import configure_flow_settings

FIXTURE=r'''<script>
window.sent=0;window.settingsActions=[];
window.settings={video:'image',ingredients:'frames',ratio:'16:9',outputs:'x2',model:'Veo 3.1 - Fast',semantic:false,unreadable:false};
function choice(k,v,label,icon=''){
 const active=settings[k]===v,bg=settings.unreadable?'rgb(30,30,30)':active?((k==='video'||k==='ingredients')?'rgb(240,240,240)':'rgb(70,70,70)'):'rgb(30,30,30)';
 return `<button type="button" style="background:${bg}" ${settings.semantic?'aria-pressed="'+active+'"':''} onclick="pick('${k}','${v}')">${icon?'<i class="material-symbols-outlined">'+icon+'</i>':''}${label}</button>`;
}
function pick(k,v){settings[k]=v;settingsActions.push(k+':'+v);drawSettings();}
function drawSettings(){
 document.querySelector('#settings').innerHTML='<div>'+choice('video','image','Image','image')+choice('video','video','Video','videocam')+'</div><div>'+choice('ingredients','frames','Frames','crop')+choice('ingredients','ingredients','Ingredients','extension')+'</div><div>'+choice('ratio','16:9','16:9','crop_16_9')+choice('ratio','9:16','9:16','crop_9_16')+'</div><button type="button" onclick="document.querySelector(\'#models\').hidden=false">'+settings.model+'<i class="material-symbols-outlined">expand_more</i></button><div>'+['x1','x2','x3','x4'].map(x=>choice('outputs',x,x)).join('')+'</div>';
 document.querySelector('#mode').innerHTML='Video · 720p · 8s <i class="material-symbols-outlined">'+(settings.ratio==='9:16'?'crop_9_16':'crop_16_9')+'</i> '+settings.outputs;
}
window.addEventListener('keydown',e=>{if(e.key==='Escape'){document.querySelector('#settings').hidden=true;document.querySelector('#models').hidden=true}});
</script>
<form onsubmit="return false"><div id=refs></div><textarea></textarea><button type=button id=mode aria-label="Settings trigger" onclick="document.querySelector('#settings').hidden=false">Video · 720p · 8s x2</button><button type=button aria-label="Start generation" onclick="sent++">arrow_forward</button></form>
<div id=settings hidden style="background:rgb(20,20,20)"></div><div id=models role=listbox hidden><button type=button role=option id=lite onclick="settings.model='Veo 3.1 - Lite';settings.ratio='16:9';settings.outputs='x2';settingsActions.push('model');document.querySelector('#models').hidden=true;drawSettings()">Veo 3.1 - Lite</button><button role=option type=button>Veo 3.1 - Quality</button></div><script>drawSettings()</script>'''

async def main():
 async def check():pass
 async with async_playwright()as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
  for semantic in (False,True):
   await page.set_content(FIXTURE)
   await page.evaluate('(value)=>{settings.semantic=value;drawSettings()}',semantic)
   report={};assert await configure_flow_settings(page,check,report),report
   state=await page.evaluate('settings')
   assert [state[k]for k in ('video','ingredients','ratio','outputs','model')]==['video','ingredients','9:16','x1','Veo 3.1 - Lite'],state
   count=await page.evaluate('settingsActions.length')
   assert await configure_flow_settings(page,check,{},verify_only=True)
   assert await page.evaluate('settingsActions.length')==count,'Readback must not toggle correct settings'
   assert await page.evaluate('sent')==0
   await page.evaluate("()=>{settings.outputs='x4';drawSettings()}")
   report={};assert not await configure_flow_settings(page,check,report,verify_only=True)
   assert await page.evaluate('settings.outputs')=='x4'and await page.evaluate('settingsActions.length')==count
  await page.set_content(FIXTURE)
  await page.evaluate('()=>{settings.unreadable=true;drawSettings()}')
  report={};assert not await configure_flow_settings(page,check,report),report
  assert 'Chưa xác nhận'in report['preparation_error']and await page.evaluate('sent')==0
  await browser.close()
 print('PASS Flow settings: Video/Ingredients/9:16/Lite/x1 configured and re-read using semantic and supplied dark UI style states; model resets repaired; correct settings not toggled; unreadable/changed state stops; no Generate.')
if __name__=='__main__':asyncio.run(main())
