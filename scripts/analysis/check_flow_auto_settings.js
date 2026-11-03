// Actual UI change handler + settings functions, controlled local API/timers only.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('workflow.html','utf8');
const code=html.slice(html.indexOf('function changeFlowSetting(event){'),html.indexOf('function preparedContext(row)'));
const handler=html.slice(html.indexOf("document.addEventListener('change',event=>{if(event.target.matches('#node-videos [data-vn-setting]'))"),html.indexOf("document.addEventListener('change',event=>{if(!event.target.matches('#node-videos [data-vn-select]'))"));
function fixture(){
 let next=0;const timers=new Map(),states={},posts=[];let listener;
 const selection={available:true,account_id:'account',token:'token'};
 const ctx={project:{id:'room'},remote:{selection},busy:false,settingsSyncTimer:null,settingsSyncPending:null,settingsSyncStarting:false,error:'',PAIR_TRIAL_ONLY:false,
 state:()=>states[ctx.project.id]??={},active:()=>false,paint:()=>{},storeProject:async()=>{},assertRoom:id=>assert.equal(id,ctx.project.id),
 setTimeout:(fn,ms)=>{const id=++next;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id),
 document:{addEventListener:(event,fn)=>listener=fn},escape:String,button:(action,text)=>text,
 workflowLocalRequest:async(path,body)=>{
  if(path==='flow/simple/status')return {selection:ctx.remote.selection,active_request:null};
  if(body){posts.push(body);return {request_id:'setting-1',room_id:'room',account_id:'account',requested:body.settings,state:'running',message:'Applying'};}
  return {request_id:'setting-1',room_id:'room',account_id:'account',requested:posts.at(-1).settings,state:'verified',message:'Verified'};
 }};
 vm.createContext(ctx);vm.runInContext(code+handler+html.slice(html.indexOf('function createReason(row){'),html.indexOf('function unresolvedTrackingTargets(){')),ctx);
 return {ctx,posts,timers,change:(key,value)=>listener({target:{matches:()=>true,dataset:{vnSetting:key},value}}),flush:async ms=>{for(const[id,t]of [...timers])if(t.ms===ms){timers.delete(id);await t.fn();}}};
}
(async()=>{
 let f=fixture();f.change('model','fast');f.change('ratio','16:9');f.change('outputs','2');
 assert(f.ctx.createReason({}).includes('Đang đồng bộ'));
 assert.equal(f.posts.length,0);assert.equal([...f.timers.values()].filter(t=>t.ms===500).length,1);
 await f.flush(500);assert.equal(f.posts.length,1);assert.equal(f.posts[0].settings.model,'fast');assert.equal(f.posts[0].settings.ratio,'16:9');assert.strictEqual(f.posts[0].settings.outputs,2);
 assert.equal(f.ctx.state().settingsTrial.state,'running');await f.flush(1000);assert.equal(f.ctx.state().settingsTrial.state,'verified');assert(!f.ctx.settingsView().includes('Áp dụng lên Flow'));
 console.log('PASS changing selectors auto-posts once with latest settings, polls verified, no Apply step');
 f=fixture();f.change('ratio','16:9');f.ctx.project.id='another-room';await f.flush(500);assert.equal(f.posts.length,0);assert.equal(f.ctx.settingsSyncPending,null);
 console.log('PASS queued sync canceled on room change');
 f=fixture();f.change('model','fast');f.ctx.remote.selection={available:true,account_id:'other',token:'other-token'};await f.flush(500);assert.equal(f.posts.length,0);assert.equal(f.ctx.state().settingsTrial.state,'failed');
 console.log('PASS changed account cannot receive stale queued settings');
 f=fixture();f.ctx.busy=true;f.change('model','fast');await f.flush(500);assert.equal(f.posts.length,0);
 console.log('PASS setting changes during an active operation never post');
 f=fixture();f.ctx.workflowLocalRequest=async()=>{throw Error('fixture unavailable')};f.change('model','fast');await f.flush(500);assert.equal(f.ctx.state().settingsTrial.state,'failed');assert(!f.ctx.settingsView().includes('Thử đồng bộ lại'));assert(f.ctx.settingsView().includes('fixture unavailable'));assert.equal(f.ctx.settingsSyncPending,null);
 console.log('PASS sync errors shown truthfully without report/retry buttons');
 f=fixture();f.ctx.epoch=0;f.ctx.schedule=()=>{};f.ctx.state().settingsTrial={state:'running',request_id:'restored'};
 f.ctx.workflowLocalRequest=async path=>path==='flow/simple/status'?{selection:{available:true,account_id:'account'}}:{request_id:'restored',state:'verified'};
 const begin=html.indexOf('async function refresh(){const room=project.id,own=epoch;');
 vm.runInContext(html.slice(begin,html.indexOf('function paint(){',begin)),f.ctx);
 await f.ctx.refresh();assert.equal(f.ctx.state().settingsTrial.state,'verified');
 console.log('PASS pending settings status resumes after returning/reloading');
})().catch(e=>{console.error(e);process.exitCode=1;});
