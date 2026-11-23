// Execute the actual extension worker with Chrome APIs simulated, no Google/network calls.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const saved={},tabs={1:{id:1,url:'https://gemini.google.com/u/1/app',windowId:2,status:'complete'}};let creates=0,scripts=0;
const context={console,URL,Uint8Array,AbortSignal,setInterval,clearInterval,setTimeout,clearTimeout,btoa:s=>Buffer.from(s,'binary').toString('base64'),sceneForgeGeminiTab:()=>{},fetch:async()=>{throw Error('Unexpected fetch');},chrome:{
 runtime:{id:'fixture',onMessage:{addListener(){}},getPlatformInfo(cb){cb({});}},alarms:{create(){},onAlarm:{addListener(){}}},
 storage:{local:{async get(key){if(key===null)return {...saved};return {[key]:saved[key]};},async set(value){Object.assign(saved,value);}}},
 tabs:{async get(id){if(!tabs[id])throw Error('Missing tab');return tabs[id];},async create(options){creates++;const id=creates+10;tabs[id]={id,url:options.url,windowId:2,status:'complete'};return tabs[id];},async remove(id){delete tabs[id];}},
 scripting:{async executeScript({target,args}){scripts++;return [{result:args[0].operation==='identity'?{ok:true}:{ok:true,image:'aW1hZ2U=',mime:'image/png'}}];}}
}};
vm.createContext(context);vm.runInContext(fs.readFileSync('veo-node-v46/scripts/browser-extension/gemini-worker.js','utf8'),context);
(async()=>{
 const link={id:'route',tabId:1,base:'http://127.0.0.1:8840',browser_key:'secret'};const job={id:'gchat-original',request:{operation:'generate',kind:'image',prompt:'exact',references:[]}};
 context.link=link;context.job=job;
 const result=await vm.runInContext('geminiTabJob(link,job)',context);assert(result.ok);assert.equal(creates,1);assert.equal(scripts,1);assert.equal(tabs[result.tab_id].url,'https://gemini.google.com/u/1/app');
 const same=await vm.runInContext('geminiTabJob(link,job)',context);assert.deepEqual(same,result);assert.equal(creates,1);assert.equal(scripts,1);
 saved['geminiJob:crash']={started:true,tabId:result.tab_id,linkId:'route'};context.crash={id:'crash',request:job.request};const unknown=await vm.runInContext('geminiTabJob(link,crash)',context);assert.equal(unknown.accepted,null);assert.equal(creates,1);assert.equal(scripts,1);
 context.recover={id:'recovery',request:{operation:'receive',target_job:'gchat-original',kind:'image'}};const recovered=await vm.runInContext('geminiTabJob(link,recover)',context);assert(recovered.ok);assert.equal(creates,1);assert.equal(scripts,2);assert.equal(recovered.tab_id,result.tab_id);
 // Simulate worker restart with cached replies: send bytes only, never run the turn again.
 saved.geminiLinks={route:link};let transfers=0;
 context.fetch=async(url)=>{if(url.endsWith('gemini-result'))transfers++;else if(url.endsWith('gemini-poll'))delete saved.geminiLinks.route;return{ok:true,status:200,json:async()=>({job:null,accepted:true})};};
 await vm.runInContext('geminiLoop(link)',context);assert.equal(transfers,2);assert.equal(scripts,2);assert(!saved['geminiJob:gchat-original'].result);assert(!saved['geminiJob:recovery'].result);
 console.log('PASS real extension worker: correct browser/account URL, one dispatch, cached result reuse, interrupted send never replayed, receive uses original tab without creating/sending a new turn');
})().catch(e=>{console.error(e);process.exitCode=1;});
