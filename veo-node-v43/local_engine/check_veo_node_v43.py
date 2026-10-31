"""Existing workflow node -> explicit SimpleFlow route -> canonical clip -> Sang Dung."""
import base64,io,json,os,socket,subprocess,tempfile,time,urllib.request
from pathlib import Path
from threading import Thread
import uvicorn
from PIL import Image
from playwright.sync_api import sync_playwright,expect
from .simple_flow import MODEL

def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);os.environ['SCENEFORGE_LOCAL_DATA']=tmp
  from . import server
  if os.environ.get('SCENEFORGE_TEST_FRONTEND'):
   from fastapi.staticfiles import StaticFiles
   for mounted in server.app.routes:
    if getattr(mounted,'name',None)=='frontend':mounted.app=StaticFiles(directory=os.environ['SCENEFORGE_TEST_FRONTEND'],html=True)
  with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  host=uvicorn.Server(uvicorn.Config(server.app,host='127.0.0.1',port=port,log_level='error'));thread=Thread(target=host.run,daemon=True);thread.start();base='http://127.0.0.1:'+str(port)
  movie=root/'clip.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=green:s=90x160:d=8','-c:v','libx264','-pix_fmt','yuv420p','-y',str(movie)],check=True)
  image=io.BytesIO();Image.new('RGB',(90,160),'green').save(image,format='PNG');data='data:image/png;base64,'+base64.b64encode(image.getvalue()).decode()
  flow={'enabled':True,'state':'ready','message':'Fixture ready','selection':{'available':True,'token':'fixture','account_name':'fixture'},'interaction':None,'active_request':None}
  posted=[];legacy_posts=[];records={};errors=[];reads=[];writers=[];mode={'switch_room':False}
  try:
   for _ in range(100):
    try:urllib.request.urlopen(base+'/local-api/health',timeout=.3);break
    except OSError:time.sleep(.05)
   with sync_playwright()as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1600,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
    def route(r):
     path=r.request.url.split('/local-api/',1)[1]
     if path=='flow/simple/status':
      if mode['switch_room']:
       mode['switch_room']=False;page.evaluate("project.id='another-room'")
      return r.fulfill(json=flow)
     if path=='flow/simple/jobs':
      body=r.request.post_data_json;posted.append(body);records[body['request_id']]={'state':'submitted','store_id':'fixture-store','request_id':body['request_id']}
      return r.fulfill(json=records[body['request_id']])
     if path.startswith('flow/simple/jobs/'):
      rid=path.rsplit('/',1)[-1];reads.append(rid);return r.fulfill(json=records[rid])
     if path.startswith('flow/simple/files/'):return r.fulfill(body=movie.read_bytes(),content_type='video/mp4')
     if path.startswith('gemini-chat/'):
      if r.request.method=='POST':writers.append(r.request.post_data_json)
      return r.fulfill(json={'selection':{'available':True,'token':'writer'}})
     if path.startswith('flow/'):
      if r.request.method=='POST':legacy_posts.append(path)
      return r.fulfill(json={'models':[MODEL],'model_details':[{'id':MODEL,'accepts_images':True,'video_type':'i2v'}],'transport':'web_ui','selection':{'available':True,'token':'fixture'}})
     r.continue_()
    page.route('**/local-api/flow/**',route);page.route('**/local-api/gemini-chat/**',route)
    page.goto(base);page.wait_for_function('appBootReady&&SceneForgeStorage.state.active')
    page.goto(base+'/workflow.html?mode=reference');page.wait_for_function('!!window.SFVeoNode')
    page.evaluate("""async image=>{
     project=blankProject();project.id='workflow-v43';project.source={poster:image,asset:'source'};project.analysis.frameQualityRequired=false;
     assets.set('frame',new File([await(await fetch(image)).blob()],'frame.png',{type:'image/png'}));
     project.scenes=Array.from({length:2},(_,i)=>sceneRecord(i*8,(i+1)*8,i,[image]));
     for(const s of project.scenes){s.id='scene-'+s.index;s.hasPerson=false;s.refsUsed=[];s.sourceFrame={id:'source',asset:'frame',image};s.approvedFrame='source';s.frameSelectionId='source';}
     project.script=[{id:'line-1',start:1,end:3,original:'Original line',newText:'Caption stays linked',faceTalking:false}];project.voiceOver={...project.voiceOver,text:'Voice stays linked'};project.merge.captions=true;
     project.cloudJobs=Array.from({length:6},(_,i)=>({id:'legacy-'+i,provider:'flow',kind:'video',sceneId:project.scenes[0].id,part:'a',state:'failed',error:'Legacy model failure'}));
     project.cloudJobs.push({id:'legacy-unknown',provider:'flow',kind:'video',sceneId:project.scenes[1].id,part:'a',state:'unknown'});
     project.workflowNodePositions??={};project.workflowNodePositions['node-videos']={x:1500,y:900};
     await storeProject();render();
    }""",data)
    node=page.locator('#node-videos');expect(node).to_have_count(1);expect(node.locator('[data-veo-build="43"]')).to_be_visible()
    assert node.locator(':scope > .port').count()==2
    assert node.locator('[data-mn-model],[data-mn=run-clips],[data-mn=refresh-models]').count()==0
    assert node.locator('.g5GroupRows').count()==0
    expect(node.locator('header')).not_to_contain_text('lỗi')
    assert page.evaluate('project.cloudJobs.filter(j=>j.state==="failed").length')==6
    assert page.locator('#node-frames').count()==1 and page.locator('#node-merge').count()==1
    page.evaluate('drawWires()')
    assert page.locator('#wires path[data-from=node-frames][data-to=node-videos]').count()==1
    assert page.locator('#wires path[data-from=node-videos][data-to=node-merge]').count()==1
    before_edges=page.locator('#wires path').evaluate_all('(els)=>els.map(e=>[e.dataset.from,e.dataset.to])')
    node.locator('[data-vn-prompt]').fill('Smile and wave.')
    expect(node.locator('[data-vn=create]')).to_be_enabled()
    # Double click must produce only one SimpleFlow job and never call the old send dialog.
    page.evaluate("""()=>{const b=document.querySelector('[data-vn=create]');b.click();b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));}""")
    page.wait_for_function('project.cloudJobs.some(j=>j.veoNodeVersion===43&&j.state==="submitted")')
    assert len(posted)==1 and not legacy_posts and not writers,(posted,legacy_posts,writers)
    body=posted[0];assert body['scene_id']=='scene-0'and body['room_id']=='workflow-v43'and body['prompt']=='Smile and wave.'
    assert len(body['references'])==1 and base64.b64decode(body['references'][0]['data'])==image.getvalue()
    rid=body['request_id'];records[rid]={'state':'done','store_id':'fixture-store','request_id':rid,'result':{'mime_type':'video/mp4','room_id':'workflow-v43','scene_id':'scene-0','part':'a'}}
    page.evaluate('()=>SFVeoNode.sync()')
    page.wait_for_function('project.scenes[0].clips.length===1')
    assert page.evaluate('project.scenes[1].clips.length')==0
    assert page.evaluate('project.scenes[0].clips[0].requestId')==rid
    expect(node.locator('[data-vn=accept]')).to_be_enabled()
    assert page.evaluate('readyCount()')==0
    node.locator('[data-vn=accept]').click();page.wait_for_function('readyCount()===1')
    assert page.evaluate('project.scenes[0].receivedClipIds.includes(project.scenes[0].clips[0].id)')
    assert page.evaluate('chosenClip(project.scenes[0],"a").requestId')==rid
    # Shared output feeds the existing merge/captions/voice workflow; no extra video node.
    expect(page.locator('#node-merge')).to_contain_text('1/2')
    assert page.evaluate('project.script[0].id')=='line-1'
    assert page.evaluate('project.voiceOver.text')=='Voice stays linked'
    assert page.evaluate('package5Captions()[0].text')=='Caption stays linked'
    assert page.locator('#node-videos').count()==1
    page.evaluate('drawWires()');assert page.locator('#wires path').evaluate_all('(els)=>els.map(e=>[e.dataset.from,e.dataset.to])')==before_edges
    await_count=page.evaluate('project.scenes[0].clips.length');page.evaluate('()=>SFVeoNode.sync()');assert page.evaluate('project.scenes[0].clips.length')==await_count
    # An unknown old request stays blocked until the user explicitly reviews it.
    page.locator('[data-vn-select]').select_option(json.dumps(['scene-1','a'],separators=(',',':')))
    page.locator('[data-vn-prompt]').fill('Turn slightly.')
    expect(page.locator('[data-vn=create]')).to_be_disabled()
    page.locator('[data-vn=review-legacy]').click();expect(page.locator('[data-vn=create]')).to_be_enabled()
    assert page.evaluate('project.cloudJobs.find(j=>j.id==="legacy-unknown").state')=='unknown'
    # Replacing the approved frame keeps the draft but requires an explicit rebind.
    page.evaluate("()=>{const s=project.scenes[1];assets.set('frame-new',assets.get('frame'));s.sourceFrame.asset='frame-new';render();}")
    expect(page.locator('[data-vn=create]')).to_be_disabled()
    expect(page.locator('[data-vn=bind]')).to_be_visible()
    page.locator('[data-vn=bind]').click();expect(page.locator('[data-vn=create]')).to_be_enabled()
    # Record the rendered replacement node for visual inspection.
    if os.environ.get('SCENEFORGE_TEST_SCREENSHOT'):
     node.screenshot(path=os.environ['SCENEFORGE_TEST_SCREENSHOT'])
    # Switching rooms while fetching the session must not send into the new room.
    mode['switch_room']=True;page.locator('[data-vn=create]').click()
    page.wait_for_function('project.id==="another-room"');time.sleep(.2)
    assert len(posted)==1
    assert not errors,errors
    print('PASS v43: same node/ports/wires, no inherited error summary, exact approved image+manual prompt -> only SimpleFlow endpoint, one send, canonical clip -> explicit accept -> readyCount and Sang Dung, no duplicate import, old unknown retained/reviewed, room change stops dispatch. Fixture only.')
    browser.close()
  finally:
   host.should_exit=True;thread.join(timeout=8)
   for handler in list(server.RUNTIME_LOG.handlers):handler.close();server.RUNTIME_LOG.removeHandler(handler)
   server.LIBRARY._root_guard.instance.close()
if __name__=='__main__':main()
