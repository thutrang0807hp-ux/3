// Executes the actual tracking-report function with local API/DOM doubles.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('workflow.html','utf8');
const start=html.indexOf('async function trackingReport('),end=html.indexOf('async function acknowledgeSavedVideos(){',start);
const source=html.slice(start,end),job={id:'flow-existing',state:'unknown',sceneId:'scene',part:'a',store_id:'store'};
const stateValue={},requests=[];let synced=false;
const record={state:'done',request_id:job.id,store_id:'store',result:{scene_id:'scene',part:'a',room_id:'room'}};
const context={trackingBusy:false,project:{id:'room'},selected:()=>({}),unresolvedTrackingTargets:()=>[job],latestJob:()=>job,pendingStates:[],remote:{native_pipeline:true},state:()=>stateValue,paint:()=>{},assertRoom:id=>assert.equal(id,'room'),
 workflowLocalRequest:async path=>{requests.push(path);if(path.startsWith('flow/simple/jobs/'))return {native_inputs:{},store_id:'store'};assert(path.includes('download_existing=true'));return {record};},
 jobReadRecord:(target,value)=>{target.state=value.state;},sync:async id=>{assert.equal(id,job.id);assert.equal(job.state,'done');synced=true;job.state='imported';},
 URL,URLSearchParams,Blob,document:{createElement:()=>({click:()=>{}})},setTimeout:fn=>fn(),storeProject:async()=>{},refresh:async()=>{}};
vm.createContext(context);vm.runInContext(source,context);
context.trackingReport().then(()=>{assert(synced);assert.equal(job.state,'imported');assert.equal(requests.length,2);assert(stateValue.trackingReportMessage.includes('không tạo video mới'));console.log('PASS existing report/check action requests download-only and syncs recovered job into UI');}).catch(e=>{console.error(e);process.exitCode=1;});
