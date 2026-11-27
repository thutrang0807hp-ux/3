"""Actual Veo detail: local prompt + approved bytes -> Flow, no Gemini dependency."""
import asyncio,base64,io
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
async def main():
 html=(ROOT/'workflow.html').read_text().replace('<script id="frame-studio-node">','<script>if(!project)project=blankProject();</script><script id="frame-studio-node">')
 png=io.BytesIO();Image.new('RGB',(180,320),'#254a59').save(png,'PNG');data='data:image/png;base64,'+base64.b64encode(png.getvalue()).decode();posts=[];jobs={};errors=[]
 async with async_playwright()as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  async def route(r):
   url=r.request.url
   if '/local-api/'in url:
    if r.request.method=='POST':posts.append((url,r.request.post_data_json))
    if url.endswith('/gemini-chat/jobs')and r.request.method=='POST':
     body=r.request.post_data_json
     visual={lang:{k:('Keep approved composition.'if k=='composition'else'')for k in ['person','product','scale','composition','background','lighting']}for lang in ['vi','en']}
     motion={lang:{'camera':'Fixed camera','initial':'Hold the approved pose','action':'AI_OPTIMIZED_ACTION','final':'Hold still'}for lang in ['vi','en']}
     record={'request_id':body['request_id'],'state':'done','result':{'text':__import__('json').dumps({'visual':visual,'motion':motion,'used_refs':['R1'],'warnings':[]})}};jobs[body['request_id']]=record;await r.fulfill(json=record);return
    if '/gemini-chat/jobs/'in url:await r.fulfill(json=jobs[url.rsplit('/',1)[-1]]);return
    if url.endswith('/flow/simple/jobs')and r.request.method=='POST':
     body=r.request.post_data_json;jobs[body['request_id']]={'request_id':body['request_id'],'state':'submitted'};await r.fulfill(json=jobs[body['request_id']]);return
    if '/flow/simple/jobs/'in url:await r.fulfill(json=jobs.get(url.rsplit('/',1)[-1],{'state':'missing'}));return
    await r.fulfill(json={'installed':True,'enabled':True,'native_pipeline':True,'selection':{'available':True,'token':'fixture','account_id':'flow-account'},'unresolved':[],'accounts':[],'logs':[]});return
   await r.fulfill(body=html,content_type='text/html')
  await page.route('**/*',route);await page.goto('http://127.0.0.1/workflow.html?mode=reference');await page.wait_for_function('window.SFVeoNode&&window.SFFrameStudio&&project')
  await page.evaluate('''async image=>{
   storeProject=async()=>{};save=()=>{};SFProviderReceipts.persistIntent=async()=>{};
   project=blankProject();project.id='video-default-test';project.source={poster:image};project.analysis.frameQualityRequired=false;
   project.script=[{id:'line',start:0,end:2.8,original:'ORIGINAL ADVERTISING CLAIM',newText:'Sáp mới cho chiếc xe của bạn.',faceTalking:false}];
   const file=await(await fetch(image)).blob();assets.set('approved-original',file);
   const s=sceneRecord(0,2.8,0,[image]);s.hasPerson=false;s.refsUsed=[];s.motion.en={camera:'Keep the camera fixed.',initial:'The hand rests on the container.',action:'Rotate the container slightly.',final:'Hold still.'};s.visual.en.product='OLD SOURCE PRODUCT LABEL';s.frames=[{id:'approved',asset:'approved-original',image,mime:'image/png',status:'pending'}];s.frameSelectionId='approved';project.scenes=[s];window.target=s;
   await SFFrameStudio.open(s.id);
  }''',data)
  await page.locator('[data-studio=approve]').click();await page.wait_for_function("frameApproved(target)&&target.approvedFrame==='approved'")
  # No successful Gemini writer record exists.
  await page.evaluate('SFVeoNode.refresh()');await page.evaluate('(()=>{const row=SFVeoNode.slots()[0];project.veoNode.drafts[row.key]={text:"",binding:"legacy-empty"};SFVeoNode.openClipDetail(row);})()')
  box=page.locator('#vnDetail [data-vn-prompt]')
  text=await box.input_value();assert 'Rotate the container slightly.'in text and 'Sáp mới cho chiếc xe của bạn.'in text,text
  assert 'ORIGINAL ADVERTISING CLAIM'not in text and 'OLD SOURCE PRODUCT LABEL'not in text
  assert 'R1' in text and 'DURATION: 2.80'in text and 'PROMPT CHƯA CHUẨN BỊ'not in text,text
  await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled()
  # Local preparation is ready without a Gemini status/check/generation request.
  await page.evaluate('SFPromptPipeline.prepareVideo(target,clipParts(target)[0])')
  assert not any('gemini' in url for url,_ in posts)
  await page.evaluate('SFVeoNode.create(SFVeoNode.slots()[0],true)')
  flow=[body for url,body in posts if url.endswith('/flow/simple/jobs')];assert len(flow)==1,posts
  assert flow[0]['prompt']==text and len(flow[0]['references'])==1
  assert flow[0]['references'][0]['data']==base64.b64encode(png.getvalue()).decode()
  assert flow[0]['settings']['outputs']==1 and flow[0]['native_pipeline']is True
  assert not await page.evaluate('!!target.videoPromptOverrides?.[clipParts(target)[0].id]'),'auto default became manual override'
  # Default refreshes from current script; user edits remain intact and require review.
  await page.evaluate("project.cloudJobs=[];project.script[0].newText='Lời mới vừa được thay.';SFVeoNode.openClipDetail(SFVeoNode.slots()[0])")
  assert 'Lời mới vừa được thay.'in await box.input_value()
  await box.fill('USER CUSTOM MOTION');await page.wait_for_timeout(300)
  await page.evaluate("project.script[0].newText='Sửa lời lần nữa';SFVeoNode.openClipDetail(SFVeoNode.slots()[0])")
  await expect(box).to_have_value('USER CUSTOM MOTION');await expect(page.locator('#vnDetail [data-vn=create]')).to_be_disabled()
  assert not any('gemini' in url for url,_ in posts),posts
  # Explicit Gemini rewrite remains optional and uses the same approved frame.
  await page.locator('#vnDetail [data-vn=write]').click()
  await page.wait_for_timeout(300)
  await expect(box).to_have_value(__import__('re').compile(r'AI_OPTIMIZED_ACTION'))
  gemini=[body for url,body in posts if url.endswith('/gemini-chat/jobs')];assert len(gemini)==1 and gemini[0]['kind']=='text'
  assert len([body for url,body in posts if url.endswith('/flow/simple/jobs')])==1
  # A reviewed/manual full prompt stays visible even when speech timing later crosses a clip.
  manual=await box.input_value();await page.evaluate("project.script[0].end=4;SFVeoNode.openClipDetail(SFVeoNode.slots()[0])")
  await expect(box).to_have_value(manual);await expect(page.locator('#vnDetail [data-vn=create]')).to_be_disabled()
  # A sentence crossing two scenes is allocated automatically and can be sent immediately.
  await page.evaluate("""()=>{target.videoPromptOverrides={[clipParts(target)[0].id]:''};delete target.promptOwners?.video;project.veoNode.drafts={};project.script[0].end=6;project.script[0].newText='Một hai ba bốn năm sáu bảy tám chín mười.';const second=sceneRecord(2.8,6,1,[target.thumbs[0]]);second.hasPerson=false;second.refsUsed=[];second.frames=[{...target.frames[0],id:'approved-second'}];second.approvedFrame='approved-second';second.frameSelectionId='approved-second';project.scenes=[target,second];project.cloudJobs=[];SFVeoNode.openClipDetail(SFVeoNode.slots()[0]);}""")
  await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled()
  allocation=await page.evaluate('SFVeoNode.slots().map(row=>speechForPart(row.s,row.p).text)')
  assert ' '.join(allocation)=='Một hai ba bốn năm sáu bảy tám chín mười.',allocation
  text=await box.input_value()
  for fragment in ['1. VISUAL PROMPT','2. MOTION & SCRIPT','3. AUDIO GENERATED','DURATION: 2.80','Rotate the container slightly.',allocation[0]]:assert fragment in text,(fragment,text)
  assert 'DIALOGUE_REVIEW_REQUIRED'not in text
  original=await page.evaluate('JSON.stringify(project.script)')
  await page.evaluate('SFVeoNode.create(SFVeoNode.slots()[0],true)')
  flow=[body for url,body in posts if url.endswith('/flow/simple/jobs')];assert len(flow)==2
  assert allocation[0]in flow[-1]['prompt']and allocation[1]not in flow[-1]['prompt']
  await page.evaluate("project.cloudJobs.at(-1).state='not_submitted';SFVeoNode.openClipDetail(SFVeoNode.slots()[1])")
  await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled()
  await page.evaluate('SFVeoNode.create(SFVeoNode.slots()[1],true)')
  flow=[body for url,body in posts if url.endswith('/flow/simple/jobs')];assert len(flow)==3
  assert allocation[1]in flow[-1]['prompt']and allocation[0]not in flow[-1]['prompt']
  assert await page.evaluate('JSON.stringify(project.script)')==original
  # Optional speech edits, silence and return to automatic do not send or modify source.
  await page.evaluate("project.cloudJobs=[];SFVeoNode.openClipDetail(SFVeoNode.slots()[0])")
  await page.locator('#vnDetail [data-vn-dialogue] summary').click()
  await page.locator('#vnDetail [data-vn-dialogue-text]').fill('Phần riêng cho clip một.')
  await page.locator('#vnDetail [data-vn=save-dialogue]').click()
  await expect(box).to_have_value(__import__('re').compile('Phần riêng cho clip một.'))
  await page.locator('#vnDetail [data-vn-dialogue] summary').click()
  await page.locator('#vnDetail [data-vn=no-dialogue]').click()
  await expect(box).to_have_value(__import__('re').compile('No dialogue has been supplied for this clip.'))
  await page.locator('#vnDetail [data-vn-dialogue] summary').click()
  await page.locator('#vnDetail [data-vn=auto-dialogue]').click()
  await expect(box).to_have_value(__import__('re').compile(allocation[0]))
  assert len([body for url,body in posts if url.endswith('/flow/simple/jobs')])==3
  assert await page.evaluate('JSON.stringify(project.script)')==original
  assert not errors,errors;await browser.close()
 print('PASS speech automatically enters full prompts across two scenes; both Flow creates enabled and dispatch once without speech confirmation; no repeated whole line; manual edits/silence/reset preserved; source unchanged')
asyncio.run(main())
