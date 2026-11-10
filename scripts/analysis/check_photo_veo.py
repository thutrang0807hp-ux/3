"""Flow lifecycle parity in real photo UI, with fake receipts and a real decoded MP4."""
import threading,http.server,functools,tempfile,subprocess,base64
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with tempfile.TemporaryDirectory() as tmp:
  video=Path(tmp)/'fixture.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=green:s=180x320:r=30','-t','7.933333','-c:v','libx264','-pix_fmt','yuv420p','-an',str(video)],check=True)
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1500,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.route('**/local-api/flow/simple/files/*',lambda route:route.fulfill(body=video.read_bytes(),content_type='video/mp4'))
   page.goto(f'http://127.0.0.1:{server.server_port}/photos.html');page.wait_for_function('!!window.SFPhotoVeo')
   result=page.evaluate('''async()=>{
    const check=(v,m)=>{if(!v)throw Error(m)};window.posts=[];window.records={};window.saved=[];window.files=new Map();window.dropReply=false;window.account='token';
    const canvas=document.createElement('canvas');canvas.width=90;canvas.height=160;canvas.getContext('2d').fillRect(0,0,90,160);const png=new File([await new Promise(r=>canvas.toBlob(r))],'start.png',{type:'image/png'}),url=canvas.toDataURL();files.set('frame',png);
    window.SceneForgeApp={photoBridge:{engine:async(path,body)=>{
     if(path==='flow/simple/status')return{enabled:true,configured:true,native_pipeline:true,generation_engine:'gflow-cli-direct',selection:{available:true,token:account,account_id:'account',account_name:'Fixture'},models:['veo-3.1-lite-i2v-8s-portrait'],active_request:null,unresolved:[]};
     if(path==='flow/simple/jobs'&&body){check(saved.some(d=>d.flowJobs?.some(j=>j.id===body.request_id&&j.state==='prepared')),'intent not saved before POST');posts.push(structuredClone(body));const record={request_id:body.request_id,store_id:'fixture-store',state:'running',submitted:true};records[body.request_id]=record;if(dropReply)throw Error('Lost response');return record;}
     if(path.startsWith('flow/simple/jobs/'))return records[path.split('/').at(-1)];
     if(path==='flow/status')throw Error('Legacy status called');
     return{};
    },saveDraft:async(id,d)=>{saved.push(structuredClone(d));},listRecipes:async()=>[],getFile:async key=>files.get(key)||null,putFile:async(key,file)=>{files.set(key,file);}}};
    const refs=Object.fromEntries(['person','outfit','product','background'].map(k=>[k,{images:k==='product'?[{id:'prod',key:'frame',image:url,name:'product.png'}]:[],description:''}]));
    const d=newDraft();d.refs=refs;d.beats=[{id:'b1',name:'Giới thiệu',type:'wide',seconds:8,text:'Đây là sản phẩm.',visualPrompt:'Medium shot.',motionPrompt:'Hold up the product.',approvedFrame:'f1',frames:[{id:'f1',key:'frame',preview:url,version:1}],clips:[],clipPlanning:{mode:'legacy',continuity:false}}];
    await SceneForgeWorkflow.openRoom({id:'photo-veo-test',name:'Photo Veo',refs,product:{id:'product',name:'Product',sceneBank:[]},photoDraft:d});
    check(posts.length===0,'opening dispatched generation');check(!!document.querySelector('[data-pv=run]'),'new board not rendered');
    let row=SFPhotoVeo.rows()[0];check(!SFPhotoVeo.reason(row),'unexpected create blocker '+SFPhotoVeo.reason(row));const job=await SFPhotoVeo.run({beatId:'b1',part:'a'},{automatic:true});
    check(posts.length===1&&posts[0].native_pipeline===true&&posts[0].references.length===1,'wrong Flow transport');check(posts[0].room_id==='photo-veo-test'&&posts[0].scene_id==='b1'&&posts[0].part==='a','wrong binding');
    let blocked=false;try{await SFPhotoVeo.run({beatId:'b1',part:'a'},{automatic:true});}catch{blocked=true;}check(blocked&&posts.length===1,'duplicate generation');
    records[job.id]={request_id:job.id,store_id:'fixture-store',state:'done',submitted:true,result:{room_id:'photo-veo-test',scene_id:'b1',part:'a',mime_type:'video/mp4',account_id:'account',model:job.model,settings:job.settings}};
    await SFPhotoVeo.sync();check(job.state==='imported','clip not imported: '+job.error+' '+job.importError);check(draft.beats[0].clips.length===1,'clip not attached');check(photoDraftCounts().ready===1,'import not handed to draft: '+JSON.stringify(draft.beats[0].clips[0]));
    await SFPhotoVeo.sync();check(draft.beats[0].clips.length===1,'duplicate import');const c=draft.beats[0].clips[0];check(c.width===180&&c.height===320&&c.duration<8&&c.tail,'real video metadata missing');
    const payload=await photoBuildDraftPayload({preview:true});check(payload.payload.clips[0].file&&payload.payload.clips[0].sourceDuration===c.duration,'draft source duration not preserved');
    const second=await SFPhotoVeo.run({beatId:'b1',part:'a',regenerate:true},{automatic:true});records[second.id]={...records[job.id],request_id:second.id};await SFPhotoVeo.sync();check(draft.beats[0].clips.length===2,'regeneration lost previous version');const newer=photoLatest(draft.beats[0],'a');check(newer.requestId===second.id,'new result not current');
    await photoSlotDialog('b1','a');const choose=document.querySelector('[data-pv=version][data-id="'+c.id+'"]');check(choose,'version control missing');choose.click();await new Promise(r=>setTimeout(r,80));check(photoLatest(draft.beats[0],'a').id===c.id,'older version selection not applied');document.querySelector('#photoDialog').close();
    dropReply=true;const before=posts.length;try{await SFPhotoVeo.run({beatId:'b1',part:'a',regenerate:true},{automatic:true});}catch{}check(posts.length===before+1,'lost response fixture did not submit');const uncertain=draft.flowJobs.at(-1);check(uncertain.state==='unknown','lost response not retained');let again=false;try{await SFPhotoVeo.run({beatId:'b1',part:'a',regenerate:true},{automatic:true});}catch{again=true;}check(again&&posts.length===before+1,'lost response automatically replayed');
    records[uncertain.id]={...records[job.id],request_id:uncertain.id,result:{...records[job.id].result,room_id:'wrong-room'}};await SFPhotoVeo.sync();check(draft.beats[0].clips.length===2,'wrong-room clip imported');
    records[uncertain.id]={...records[job.id],request_id:uncertain.id};draft.beats[0].motionPrompt='A changed action';await SFPhotoVeo.sync();check(draft.beats[0].clips.length===2&&draft.beats[0].staleClips.length===1,'stale result replaced current');check(uncertain.state==='imported'&&uncertain.stale,'stale job not retained');draft.beats[0].motionPrompt='Hold up the product.';
    const postsBeforeSettings=posts.length;await SFPhotoVeo.settingsDialog();document.querySelector('[data-pv-setting=model]').value='fast';document.querySelector('#pvSaveSettings').click();await new Promise(r=>setTimeout(r,80));check(SFPhotoVeo.settings().model==='fast'&&posts.length===postsBeforeSettings,'settings change generated a clip');
    draft.storyboardPlan={mode:'frames',slots:{'b1:a':{selected:true,applied:{start:'start',end:'end'},images:{start:[],end:[]},chosen:{}}}};check(!!SFPhotoVeo.reason(SFPhotoVeo.rows()[0]),'unsupported pair not blocked');
    
    return{posts:posts.length,clips:draft.beats[0].clips.length,duration:c.duration,sourceDuration:payload.payload.clips[0].sourceDuration,lostResponseBlocked:true,wrongRoomBlocked:true,sharedSettings:SFVeoLifecycle.valid(SFPhotoVeo.settings())};
   }''')
   batch_result=page.evaluate('''async()=>{
    const check=(v,m)=>{if(!v)throw Error(m)};window.dropReply=false;const old=SceneForgeApp.photoBridge.engine;window.batchPosts=0;
    SceneForgeApp.photoBridge.engine=async(path,body)=>{if(path==='flow/simple/jobs'&&body){if(draft.flowJobs.some(j=>j.id!==body.request_id&&j.photoVeoVersion===1&&j.state!=='imported'))throw Error('overlapping batch send');const initial=await old(path,body);records[body.request_id]={request_id:body.request_id,store_id:'fixture-store',state:'done',result:{room_id:body.room_id,scene_id:body.scene_id,part:body.part,mime_type:'video/mp4',account_id:'account',model:body.model,settings:body.settings}};batchPosts++;return initial;}return old(path,body);};
    const oldDraft=structuredClone(draft);oldDraft.flowJobs=[];oldDraft.storyboardPlan={mode:'overall',slots:{}};oldDraft.photoVeo={version:1,settings:{kind:'video',mode:'frames',ratio:'9:16',model:'lite',outputs:1}};oldDraft.beats=[0,1].map((n)=>({...structuredClone(oldDraft.beats[0]),id:'batch-'+n,name:'Batch '+n,clips:[],staleClips:[],chosenClip:null,chosenParts:{},motionPrompt:'Hold up the product.'}));oldDraft.mergeView={order:[],hidden:[],versions:{}};
    await SceneForgeWorkflow.openRoom({id:'batch-room',name:'Batch',refs:oldDraft.refs,product:{id:'product',name:'Product',sceneBank:[]},photoDraft:oldDraft});await SFPhotoVeo.run();document.querySelector('#photoVeoConfirm').click();return true;
   }''')
   page.wait_for_function("draft.photoVeo?.batch?.state==='done'||draft.photoVeo?.batch?.state==='attention'",timeout=30000)
   batch_result=page.evaluate("({state:draft.photoVeo.batch.state,error:draft.photoVeo.batch.error,posts:batchPosts,ready:photoDraftCounts().ready,imported:draft.flowJobs.filter(j=>j.state==='imported').length})")
   assert batch_result['state']=='done' and batch_result['posts']==2 and batch_result['ready']==2 and batch_result['imported']==2,batch_result
   page.evaluate('''async()=>{const d=structuredClone(draft);d.flowJobs=[];d.photoVeo.batch=null;d.beats.forEach(b=>{b.clips=[];b.staleClips=[];b.chosenParts={};delete b.chosenClip;});batchPosts=0;await SceneForgeWorkflow.openRoom({id:'cancel-room',name:'Cancel',refs:d.refs,product:{id:'product',name:'Product',sceneBank:[]},photoDraft:d});await SFPhotoVeo.run();document.querySelector('#photoVeoConfirm').click();}''')
   page.wait_for_function("batchPosts===1&&!!document.querySelector('[data-pv=pause]')",timeout=10000)
   page.evaluate("document.querySelector('[data-pv=pause]').click()")
   page.wait_for_function("draft.photoVeo?.batch?.state==='paused'||draft.photoVeo?.batch?.state==='attention'",timeout=30000)
   cancel_result=page.evaluate("({state:draft.photoVeo.batch.state,posts:batchPosts,ready:photoDraftCounts().ready})")
   assert cancel_result['state']=='paused' and cancel_result['posts']==1 and cancel_result['ready']==1,cancel_result
   assert not errors,errors
   print('PASS',result,'batch',batch_result,'cancel',cancel_result);browser.close()
finally:server.shutdown()
