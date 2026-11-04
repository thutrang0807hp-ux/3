"""Real shell fixture for home/recipes/batch navigation and retained form state.
Run from repo root. Optional args: shell HTML path, --baseline (measure without new assertions).
"""
import asyncio,sys
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 source=next((a for a in sys.argv[1:] if not a.startswith('--')),'index.html')
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await browser.new_page()
  async def route(r):
   if r.request.resource_type=='document':await r.fulfill(body=Path(source).read_text(),content_type='text/html')
   else:await r.fulfill(json={})
  await page.route('**/*',route)
  await page.goto('http://sceneforge.test/shell')
  await page.wait_for_function('!!window.SceneForgeApp');await page.wait_for_timeout(500)
  result=await page.evaluate('''async baseline=>{
const check=(v,m)=>{if(!v)throw Error(m)},refs=Object.fromEntries(['person','outfit','product','background'].map(k=>[k,{images:[],description:''}]));
products=[{id:'p',name:'Fixture',refs}];prefs.product='p';prefs.lastRoom='r0';
rooms=Array.from({length:200},(_,i)=>({id:'r'+i,name:'Room '+i,productId:'p',mode:'reference',stage:'review',createdAt:Date.now(),updatedAt:Date.now(),refs,sceneStates:Array(20).fill('review'),sceneCount:20}));currentRoom=rooms[0];frameRoom='r0';currentView='overview';
let flushes=0;const frame=document.createElement('iframe');frame.id='workflowFrame';document.querySelector('#roomFrames').append(frame);frame.contentWindow.SceneForgeWorkflow={isScanning:()=>false,getState:()=>({analysis:{status:'idle'}}),flushRoom:async()=>{flushes++}};
recipeCache={version:4,items:structuredClone(SFRecipes.starters).map(r=>({...r,kind:'formula',productIds:[],status:'new'})),trash:[],topics:[],usage:{},feedback:{},topicKeywords:{}};
batchState=batchReadState(null);batchState.draft='keep this unsent prompt';batchState.paused=true;
let homeRenders=0;const homeBefore=homeDashboardPaint;homeDashboardPaint=(...args)=>{homeRenders++;return homeBefore(...args)};
if(!baseline){
 await showView('analysis');const api=frame.contentWindow.SceneForgeWorkflow;api.isScanning=()=>true;let blocked=false;
 try{await g6OpenRecipes()}catch{blocked=true}check(blocked&&currentView==='analysis'&&!g6RecipeOpen,'Recipe entry bypassed scanning guard');
 api.isScanning=()=>false;api.flushRoom=async()=>{throw Error('fixture save failure')};blocked=false;
 try{await openBatchStudio()}catch{blocked=true}check(blocked&&currentView==='analysis'&&!batchOpen,'Batch entry bypassed save failure');
 api.flushRoom=async()=>{flushes++};await showView('overview');flushes=0;
}
const times={home:[],recipes:[],batch:[],render:[],board:[]};const oldRender=render;render=(...args)=>{const t=performance.now();const r=oldRender(...args);times.render.push(performance.now()-t);return r;};const oldBoard=homeDashboardPaint;homeDashboardPaint=(...args)=>{const t=performance.now();const r=oldBoard(...args);times.board.push(performance.now()-t);return r;};
for(let i=0;i<3;i++){
 let t=performance.now();await showView('overview');times.home.push(performance.now()-t);
 const count=homeRenders;t=performance.now();await g6OpenRecipes();times.recipes.push(performance.now()-t);if(!baseline)check(homeRenders===count,'Recipes rendered the hidden home board');
 const count2=homeRenders;t=performance.now();await openBatchStudio();times.batch.push(performance.now()-t);if(!baseline)check(homeRenders===count2,'Batch rendered the hidden home board');
 if(i===0){window.batchInputFixture=document.querySelector('#batchPrompts');document.querySelector('#batchAspect').value='16:9';}
 else if(!baseline){check(document.querySelector('#batchPrompts')===window.batchInputFixture,'Batch controls remounted');check(document.querySelector('#batchAspect').value==='16:9','Batch aspect selection reset');}
}
if(!baseline){
 check(flushes===0,'Overview subpages flushed an inactive workflow');
 check(document.querySelector('#batchPrompts').value==='keep this unsent prompt','Unsent batch draft lost');
 products.push({id:'p2',name:'Added product',refs});await g6OpenRecipes();await openBatchStudio();check(document.querySelector('#batchProduct option[value=p2]'),'New products not refreshed');check(document.querySelector('#batchPrompts')===window.batchInputFixture&&document.querySelector('#batchAspect').value==='16:9','Product refresh reset batch controls');
 rooms[0].name='UPDATED ROOM';await showView('overview');check(document.querySelector('#board').textContent.includes('UPDATED ROOM'),'Home data change not visible');
 const last=document.querySelector('#board [data-room=r199]');last.scrollIntoView();await new Promise(r=>requestAnimationFrame(r));check(last.getBoundingClientRect().height>0&&last.textContent.includes('Room 199'),'Offscreen room not available on scroll');
 const host=document.createElement('div');document.body.append(host);stableHTML(host,'<b>correct</b>');const retained=host.firstChild;stableHTML(host,'<b>correct</b>');check(host.firstChild===retained,'Identical markup replaced DOM');host.firstChild.textContent='external edit';stableHTML(host,'<b>correct</b>');check(host.textContent==='correct','Cache hid an external DOM mutation');stableHTML(host,'<b>new value</b>');check(host.textContent==='new value','Changed markup not painted');host.firstChild.textContent='later mutation';await new Promise(r=>setTimeout(r,0));stableHTML(host,'<b>new value</b>');check(host.textContent==='new value','Delivered mutation records did not invalidate cache');host.remove();
}
return {times,homeRenders,flushes,batchDraft:document.querySelector('#batchPrompts').value};
}''','--baseline' in sys.argv)
  print(result)
  await browser.close()
if __name__=='__main__':asyncio.run(main())
