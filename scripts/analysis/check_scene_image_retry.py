"""Actual scene retry UI: cancel is free; confirmed retry is scoped and preserves history."""
import functools,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/workflow.html');page.wait_for_function('window.SFPromptPipeline&&window.SFMediaNodes')
  page.evaluate('''()=>{storeProject=async()=>{};SFProviderReceipts.persistIntent=async()=>{};const c=document.createElement('canvas');c.width=c.height=16;const img=c.toDataURL();project=blankProject();project.id='retry-project';project.source={poster:img};project.scenes=[sceneRecord(0,4,0,[img]),sceneRecord(4,8,1,[img])];project.scenes.forEach(s=>{s.refsUsed=[];s.frames=[{id:'kept-'+s.id,image:img,version:1}];});project.cloudJobs=project.scenes.map((s,i)=>({id:'old-'+i,sceneId:s.id,kind:'image',provider:'gemini-chat',state:'unknown'}));window.posts=[];workflowLocalRequest=async(path,body)=>{if(path.endsWith('/status'))return{installed:true,selection:{available:true,token:'same'}};if(path.endsWith('/receive'))return{state:'done',result:{mime_type:'image/png'}};if(body){posts.push(structuredClone(body));return {state:'done',result:{mime_type:'image/png'}};}return {state:'done',result:{mime_type:'image/png'}};};directRecover=async()=>{for(const j of project.cloudJobs)if(j.state==='done')j.state='imported';};render();SFMediaNodes.open('frame',project.scenes[0].id);}''')
  assert page.locator('[data-frame-main]').get_attribute('data-mn')=='frame-inspector-refresh'
  page.locator('#frameInspectorAdvanced > summary').click()
  page.once('dialog',lambda d:d.dismiss());page.locator('[data-mn=retry-scene-image]').click()
  page.wait_for_timeout(80);assert page.evaluate('posts.length')==0
  assert page.evaluate("project.cloudJobs[0].state")=='unknown'
  page.once('dialog',lambda d:d.accept());page.locator('[data-mn=retry-scene-image]').click()
  page.wait_for_function('posts.length===1&&!SFPromptPipeline.isRunning()')
  result=page.evaluate('''()=>({posts,old:project.cloudJobs[0],other:project.cloudJobs[1],scope:project.scenes[0].imageConversationScope,otherScope:project.scenes[1].imageConversationScope,frames:project.scenes.map(s=>s.frames[0].id),room:project.id})''')
  assert result['old']['state']=='abandoned'and result['old']['previousState']=='unknown'
  assert result['other']['state']=='unknown'and not result.get('otherScope')
  assert len(result['posts'])==1 and result['posts'][0]['kind']=='image'
  assert result['posts'][0]['room_id']==result['room']and result['posts'][0]['conversation_scope']==result['scope']
  assert result['posts'][0]['scene_id']==result['old']['sceneId']
  assert all(x.startswith('kept-')for x in result['frames'])
  assert page.locator('#modal').is_visible()
  page.evaluate('''()=>{project.cloudJobs.at(-1).state='done';directRecover=async options=>{window.receiveOptions=options;project.cloudJobs.at(-1).state='imported';};SFMediaNodes.open('frame',project.scenes[0].id);}''')
  page.locator('[data-frame-main]').click();page.wait_for_function('window.receiveOptions')
  assert page.evaluate('receiveOptions.sceneId===project.scenes[0].id&&posts.length===1&&project.cloudJobs[1].state==="unknown"')
  assert not errors,errors;browser.close()
 print('PASS cancel sends zero; confirmed retry sends one scoped image for selected scene; old receipt, other scene, frame versions retained')
finally:server.shutdown()
