// Executes actual settings selectors/local-save path; no calls to the old Settings-trigger API.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('workflow.html','utf8');
const code=html.slice(html.indexOf('function changeFlowSetting(event){'),html.indexOf('function preparedContext(row)'));
const handler=html.slice(html.indexOf("document.addEventListener('change',event=>{if(event.target.matches('#node-videos [data-vn-setting]'))"),html.indexOf("document.addEventListener('change',event=>{if(!event.target.matches('#node-videos [data-vn-select]'))"));
function fixture(){let next=0,listener;const timers=new Map(),states={};
const ctx={project:{id:'room'},remote:{selection:{available:true,account_id:'account'}},busy:false,settingsSyncTimer:null,settingsSyncPending:null,settingsSyncStarting:false,error:'',state:()=>states[ctx.project.id]??={},active:()=>false,paint:()=>{},storeProject:async()=>{},assertRoom:id=>assert.equal(id,ctx.project.id),escape:String,
setTimeout:(fn,ms)=>{const id=++next;timers.set(id,{fn,ms});return id},clearTimeout:id=>timers.delete(id),document:{addEventListener:(event,fn)=>listener=fn},workflowLocalRequest:()=>{throw Error('Old settings endpoint must not be called')}};
vm.createContext(ctx);vm.runInContext(code+handler+html.slice(html.indexOf('function createReason(row){'),html.indexOf('function unresolvedTrackingTargets(){')),ctx);
return{ctx,timers,change:(key,value)=>listener({target:{matches:()=>true,dataset:{vnSetting:key},value}}),flush:async()=>{for(const[id,t]of [...timers]){timers.delete(id);await t.fn()}}};}
(async()=>{
let f=fixture();f.change('model','fast');f.change('ratio','16:9');assert(f.ctx.createReason({}).includes('Đang lưu'));assert.equal(f.timers.size,1);await f.flush();assert.equal(f.ctx.state().settingsTrial.state,'saved');assert.equal(f.ctx.state().settingsTrial.requested.model,'fast');assert.equal(f.ctx.state().settingsTrial.requested.ratio,'16:9');console.log('PASS latest choices saved once for CLI; no Settings-trigger API');
f=fixture();f.change('model','fast');f.ctx.project.id='other';await f.flush();assert.equal(f.ctx.settingsSyncPending,null);assert(!f.ctx.state().settingsTrial);console.log('PASS room switch cancels pending local save');
f=fixture();f.ctx.busy=true;f.change('model','fast');assert.equal(f.timers.size,0);console.log('PASS editing blocked while creating');
f=fixture();f.ctx.storeProject=async()=>{throw Error('fixture unavailable')};f.change('model','fast');await f.flush();assert.equal(f.ctx.state().settingsTrial.state,'failed');assert(f.ctx.settingsView().includes('fixture unavailable'));console.log('PASS save failure remains visible');
})().catch(e=>{console.error(e);process.exitCode=1});
