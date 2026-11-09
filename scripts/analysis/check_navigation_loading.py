"""Chromium regressions: late navigation, shared frame initialization, targeted room reads, light scene opening.
Run from repository root; all backend endpoints are local fixtures, no generation calls.
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

async def shell(browser, source):
 page=await browser.new_page()
 html=Path(source).read_text()
 async def route(r):
  if r.request.resource_type=='document' and '/shell' in r.request.url:
   await r.fulfill(body=html,content_type='text/html')
  else:await r.fulfill(body='{}',content_type='application/json')
 await page.route('**/*',route)
 await page.goto('https://sceneforge.test/shell')
 await page.wait_for_function('window.SceneForgeApp?.getReadiness().rooms')
 result=await page.evaluate('''async()=>{
const turn=()=>new Promise(r=>setTimeout(r,10)),check=(v,m)=>{if(!v)throw Error(m)};
const refs=Object.fromEntries(['person','outfit','product','background'].map(k=>[k,{images:[],description:''}]));
products=[{id:'p',name:'Fixture',refs}];prefs.product='p';prefs.lastRoom='r';
rooms=[{id:'r',name:'Fixture',productId:'p',mode:'reference',stage:'review',createdAt:Date.now(),updatedAt:Date.now(),refs,sceneStates:[]}];currentRoom=rooms[0];frameRoom='r';
importPendingVersions=async()=>{};
for(const id of ['workflowFrame','standaloneEditorDemo']){const f=document.createElement('iframe');f.id=id;document.querySelector('#roomFrames').append(f);f.contentWindow.SceneForgeWorkflow={getState:()=>({analysis:{status:'idle'}}),isScanning:()=>false,flushRoom:async()=>{}};f.contentWindow.SceneForgeEditor={flushRoom:async()=>{},isExporting:()=>false};}
await showView('analysis');
check(document.querySelector('#workspaceHeaderControls #saveProjectNow')&&!document.querySelector('.rail #saveProjectNow'),'Save is not in the workspace toolbar');
// A recipe read completes after a different tab was selected.
const originalLibrary=recipeLibrary;let releaseLibrary;recipeLibrary=()=>new Promise(r=>releaseLibrary=r);
document.querySelector('#g6OpenRecipes').click();await turn();
document.querySelector('.rail [data-view=editor]').click();await turn();
releaseLibrary({items:[],trash:[],topics:[],usage:{},feedback:{}});await turn();await turn();
check(currentView==='editor'&&!g6RecipeOpen,'Late recipe loading stole the active tab');recipeLibrary=originalLibrary;
// A loading/uneditable retained frame must not block ordinary tab changes.
await showView('analysis');const api=document.querySelector('#workflowFrame').contentWindow.SceneForgeWorkflow;let strictCalls=0;
api.flushRoom=async()=>{strictCalls++;throw Error('fixture blocked strict flush')};
document.querySelector('.rail [data-view=overview]').click();await turn();await turn();
check(currentView==='overview'&&strictCalls===0,'View navigation waited for a retained frame flush');
check(!!document.querySelector('.deskActions #saveProjectNow'),'Home save missing');
document.querySelector('.rail [data-view=editor]').click();await turn();
check(currentView==='editor'&&strictCalls===0,'Editor navigation forced a retained-frame save');
check(document.querySelector('#projectSaveControl').parentElement.matches('.roomBar'),'Editor save hidden in analysis-only controls');api.flushRoom=async()=>{};
// Start a cold analysis frame; revisit it while its API is delayed.
document.querySelector('#workflowFrame').remove();let releaseAPI,opens=0,waits=0;
const originalWait=waitAPI,originalPayload=roomPayload;
waitAPI=()=>{waits++;return new Promise(r=>releaseAPI=r)};roomPayload=async r=>({id:r.id});
document.querySelector('.rail [data-view=analysis]').click();await turn();
const frame=document.querySelector('#workflowFrame');check(!!frame,'Cold frame missing');
document.querySelector('.rail [data-view=editor]').click();await turn();
check(document.querySelector('#roomLoading').hidden,'Old loading overlay obscures the ready tab');
document.querySelector('.rail [data-view=analysis]').click();await turn();
check(document.querySelector('#workflowFrame')===frame,'Revisit replaced a loading frame');
document.querySelector('.rail [data-view=editor]').click();await turn();
releaseAPI({openRoom:async data=>{check(data.id==='r','Wrong room payload');opens++}});await turn();await turn();await turn();
check(currentView==='editor'&&frame.hidden&&frame.inert,'Late frame completion stole visibility');
check(opens===1&&waits===1,'Concurrent tab clicks initialized the frame more than once');
waitAPI=originalWait;roomPayload=originalPayload;
return {lateRecipeIgnored:true,retainedFramesDoNotBlockNavigation:true,frameInitializationCount:opens,apiWaitCount:waits,readyTabUncovered:true};
}''')
 print('PASS shell',result)
 await page.close()

async def workflow(browser, source):
 page=await browser.new_page()
 html=Path(source).read_text()
 await page.add_init_script('''window.projectReads=[];
for(const key of ['get','getAll']){const old=IDBObjectStore.prototype[key];IDBObjectStore.prototype[key]=function(...args){if(this.name==='projects')window.projectReads.push({method:key,key:args[0]});return old.apply(this,args)};}''')
 async def route(r):
  if '/local-api/' in r.request.url:
   await r.fulfill(json={'enabled':True,'native_pipeline':True,'selection':{'available':True,'token':'fixture','account_id':'fixture'},'unresolved':[]})
  else:await r.fulfill(body=html,content_type='text/html')
 await page.route('**/*',route)
 await page.goto('http://127.0.0.1:43891/workflow.html?room=fixture-room&mode=reference')
 await page.wait_for_function('!!window.SceneForgeWorkflow&&!!window.SFVeoNode')
 result=await page.evaluate('''async()=>{
const check=(v,m)=>{if(!v)throw Error(m)};
check(projectReads.some(r=>r.method==='get'&&r.key==='fixture-room'),'Startup did not read the requested room');
check(!projectReads.some(r=>r.method==='getAll'),'Startup read all projects/media');
project=blankProject();project.id='fixture-room';project.analysis.frameQualityRequired=false;
const canvas=document.createElement('canvas');canvas.width=90;canvas.height=160;const ctx=canvas.getContext('2d');ctx.fillStyle='teal';ctx.fillRect(0,0,90,160);const image=canvas.toDataURL();
project.source={poster:image,asset:'source'};project.scenes=Array.from({length:30},(_,i)=>{const s=sceneRecord(i*8,(i+1)*8,i,[image]);s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',image};s.approvedFrame='source';s.frameSelectionId='source';s.videoPromptOverrides={a:'A gentle movement.'};return s;});render();await SFVeoNode.refresh();
const nodes=document.querySelector('#nodes'),firstImage=nodes.querySelector('img');let renders=0;const old=render;render=(...args)=>{renders++;return old(...args)};
const t=performance.now();openScene(project.scenes[0].id,'video');const openMs=performance.now()-t;
check(detailOpen&&!document.querySelector('#details').hidden,'Scene details not opened');
const input=document.querySelector('#details [data-prompt-group]');check(!!input,'Prompt editor missing');input.value='fixture edited prompt';input.dispatchEvent(new Event('input',{bubbles:true}));
check(activeScene()[input.dataset.promptGroup][language][input.dataset.promptKey]==='fixture edited prompt','Prompt edit not retained');
openScene(project.scenes[1].id,'frame');check(selected===1&&detailTab==='frame','Wrong scene/tab');closeDetails();
check(renders===0&&nodes===document.querySelector('#nodes')&&firstImage===nodes.querySelector('img'),'Opening scenes rebuilt the canvas/media');
return {targetedRoomRead:true,fullProjectScans:projectReads.filter(r=>r.method==='getAll').length,canvasRenders:renders,promptEditRetained:true,openSceneMs:openMs};
}''')
 print('PASS workflow',result)
 await page.close()

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   await shell(browser,sys.argv[1] if len(sys.argv)>1 else 'index.html')
   await workflow(browser,sys.argv[2] if len(sys.argv)>2 else 'workflow.html')
  finally:await browser.close()
if __name__=='__main__':asyncio.run(main())
