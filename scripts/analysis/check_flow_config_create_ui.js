// Actual create + receive functions: configured request snapshot and landscape import.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('workflow.html','utf8');
const settings=html.slice(html.indexOf('function generationSettings(){'),html.indexOf('function replacementView('));
const create=html.slice(html.indexOf('async function create(row,confirmed=false){'),html.indexOf('async function uploadOnly(row)'));
const receive=html.slice(html.indexOf('async function receive(job,record,room){'),html.indexOf('async function create(row,confirmed=false){'));
const stateValue={flowSettings:{kind:'video',mode:'ingredients',ratio:'16:9',model:'fast',outputs:1}},row={s:{id:'scene',index:0,approvedFrame:'frame',clips:[]},p:{id:'a',start:0,end:8}};
const posts=[];let confirmed='';
class Reader{readAsDataURL(){this.result='data:image/png;base64,aW1hZ2U=';queueMicrotask(()=>this.onload());}}
const ctx={$:()=>null,key:()=> 'slot',project:{id:'room',scenes:[row.s],cloudJobs:[]},state:()=>stateValue,flowSettings:()=>stateValue.flowSettings,settingsSyncPending:null,settingsSyncStarting:false,remote:{native_pipeline:true},busy:false,active:()=>false,pairReady:()=>false,legacyUnresolved:()=>[],frame:()=>({image:'fixture'}),draft:()=>({text:'prompt',binding:'stable'}),binding:()=> 'stable',latestJob:()=>null,needsResolution:()=>false,assertRoom:id=>assert.equal(id,'room'),writeDraft:()=>{},confirm:text=>{confirmed=text;return true},uid:()=> 'fixture-id',directSignature:async()=> 'signature',clipContinuityFrom:()=>null,MODEL:'veo-3.1-lite-i2v-8s-portrait',VERSION:43,
workflowLocalRequest:async(path,body)=>{if(!body)return {enabled:true,native_pipeline:true,selection:{available:true,token:'token',account_id:'account'},unresolved:[]};posts.push(body);return {state:'submitted'};},
fetch:async()=>({ok:true,blob:async()=>new Blob(['fixture'],{type:'image/png'})}),FileReader:Reader,Blob,File,URL,queueMicrotask,
SFProviderReceipts:{persistIntent:async()=>{}},parent:{SceneForgeStorage:{}},storeProject:async()=>{},refresh:async()=>{},render:()=>{},jobReadRecord:(job,record)=>{job.state=record.state},jobPostFailure:()=>{},
clipParts:()=>[row.p],useVideo:async(url,fn)=>fn({videoWidth:160,videoHeight:90,duration:8}),seekFrame:async()=>{},capture:()=> 'tail',putAsset:()=> 'asset'};
vm.createContext(ctx);vm.runInContext(settings+create+receive,ctx);
(async()=>{
await ctx.create(row);assert.equal(posts.length,1);assert.equal(posts[0].settings.ratio,'16:9');assert.equal(posts[0].settings.model,'fast');assert.equal(posts[0].model,'veo-3.1-fast-i2v-8s-landscape');assert(confirmed.includes('fast')&&confirmed.includes('16:9'));
const job=ctx.project.cloudJobs[0];stateValue.flowSettings={kind:'video',mode:'frames',ratio:'9:16',model:'quality',outputs:1};
const result={room_id:'room',scene_id:'scene',part:'a',model:posts[0].model,settings:posts[0].settings,mime_type:'video/mp4'};
await ctx.receive(job,{request_id:job.id,result},'room');assert.equal(job.state,'imported');assert.equal(row.s.clips[0].model,'veo-3.1-fast-i2v-8s-landscape');assert.equal(row.s.clips[0].width,160);assert.equal(row.s.clips[0].settings.ratio,'16:9');
console.log('PASS actual UI create posts selected settings/model, and imports landscape using pinned result after dropdown changes');
job.state='submitted';ctx.polling=false;ctx.jobs=()=>[job];ctx.shouldPoll=()=>true;ctx.schedule=()=>{};ctx.pendingStates=['submitted','running','downloading'];ctx.clip=()=>null;ctx.latestJob=()=>job;ctx.savedVideoAcknowledged=()=>false;ctx.escape=String;ctx.button=(action,text)=>'<button>'+text+'</button>';
ctx.workflowLocalRequest=async()=>({request_id:job.id,state:'submitted',message:'Flow đang tạo video',progress:null,provider_task:{media_id:'22222222-2222-4222-8222-222222222222',association_confirmed:true,state:'generating'}});
vm.runInContext(html.slice(html.indexOf('async function sync(only=null){'),html.indexOf('async function receive(job,record,room){'))+html.slice(html.indexOf('function stageProgress(job){'),html.indexOf('function prepareView(row,blocked){')),ctx);
await ctx.sync(job.id);const markup=ctx.videoProgressView(row);assert(markup.includes('22222222-2222-4222-8222-222222222222'));assert(markup.includes('Flow đang tạo video'));assert(markup.includes('value=\"60\"'));assert(markup.includes('Ước tính theo bước'));assert(!markup.includes('value=\"100\"'));assert(row.s.clips[0].autoReceivedAt);assert(!row.s.clips[0].reviewDecision);
console.log('PASS actual UI sync exposes early video ID and real stage with a clearly labelled stage estimate');
})().catch(e=>{console.error(e);process.exitCode=1});
