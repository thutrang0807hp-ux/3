"""Real shell tab navigation with 200 local fixture rooms; no external calls. Run from repo root."""
import asyncio,sys
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 html=Path(sys.argv[1] if len(sys.argv)>1 else 'index.html').read_text()
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  errors=[]
  page=await b.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  async def route(r):
   if r.request.resource_type=='document' and '/shell' in r.request.url:await r.fulfill(body=html,content_type='text/html')
   else:await r.fulfill(body='{}',content_type='application/json')
  await page.route('**/*',route)
  await page.goto('https://sceneforge.test/shell')
  await page.wait_for_function('window.SceneForgeApp?.getReadiness().rooms')
  print(await page.evaluate('''async()=>{
const refs=Object.fromEntries(['person','outfit','product','background'].map(k=>[k,{images:[],description:''}]));
products=[{id:'p',name:'Fixture',refs}];prefs.product='p';prefs.lastRoom='r0';
rooms=Array.from({length:200},(_,i)=>({id:'r'+i,name:'Fixture '+i,productId:'p',mode:'reference',stage:'review',createdAt:Date.now(),updatedAt:Date.now(),refs,sceneStates:Array(30).fill('review'),sceneCount:30}));currentRoom=rooms[0];frameRoom=currentRoom.id;
importPendingVersions=async()=>{};let reads=0,flushes=0;const state={analysis:{status:'idle'},scenes:Array.from({length:60},()=>({image:'x'.repeat(200000)}))};
for(const id of ['workflowFrame','standaloneEditorDemo']){const f=document.createElement('iframe');f.id=id;document.querySelector('#roomFrames').append(f);f.contentWindow.SceneForgeWorkflow={getState:()=>{reads++;return structuredClone(state)},isScanning:()=>false,flushRoom:async()=>{flushes++}};f.contentWindow.SceneForgeEditor={flushRoom:async()=>{},isExporting:()=>false};}
let renders=0;const old=render;render=function(){renders++;return old();};
await showView('analysis');const samples=[];renders=0;
for(let i=0;i<8;i++){const t=performance.now();await showView(i%2?'analysis':'editor');samples.push(performance.now()-t);}
const workspaceRenders=renders;await showView('overview');
const initialRoom=currentRoom.id,wf=document.querySelector('#workflowFrame'),ed=document.querySelector('#standaloneEditorDemo');
{
 if(workspaceRenders!==0||reads!==0||flushes!==1)throw Error('Navigation rendered hidden board, cloned state, or skipped flush');
 await showView('analysis');wf.contentWindow.SceneForgeWorkflow.isScanning=()=>true;
 let blocked=false;try{await showView('overview')}catch{blocked=true}if(!blocked||currentView!=='analysis')throw Error('Scanning must block leaving');
 wf.contentWindow.SceneForgeWorkflow.isScanning=()=>false;
 wf.contentWindow.SceneForgeWorkflow.flushRoom=async()=>{throw Error('fixture save failed')};
 blocked=false;try{await showView('overview')}catch{blocked=true}if(!blocked||currentView!=='analysis')throw Error('Failed save must keep current view');
 wf.contentWindow.SceneForgeWorkflow.flushRoom=async()=>{};ed.contentWindow.SceneForgeEditor.isExporting=()=>true;
 blocked=false;try{await showView('overview')}catch{blocked=true}if(!blocked||currentView!=='analysis')throw Error('Export must block leaving');
 ed.contentWindow.SceneForgeEditor.isExporting=()=>false;await showView('editor');await showView('analysis');
 if(document.querySelector('#workflowFrame')!==wf||document.querySelector('#standaloneEditorDemo')!==ed||currentRoom.id!==initialRoom)throw Error('Tab switching replaced frame or room');
 if(wf.hidden||!ed.hidden||ed.inert!==true)throw Error('Active frame visibility/inert incorrect');
 const api=wf.contentWindow.SceneForgeWorkflow;delete api.isScanning;api.getState=()=>({analysis:{status:'scanning'}});
 blocked=false;try{await showView('overview')}catch{blocked=true}if(!blocked)throw Error('Older API fallback lost scanning guard');
}
return {switchMs:samples,workspaceRenders,fullStateReads:reads,flushes,iframeCount:document.querySelectorAll('#roomFrames iframe').length};}'''))
  await b.close()
  assert not errors, errors
asyncio.run(main())
