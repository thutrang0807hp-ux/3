const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync('workflow.html','utf8');const a=html.indexOf('let automaticSpeechCache=null;'),b=html.indexOf('\nfunction speechControls(',a);
const project={id:'one',scenes:[],script:[]};const c={project,clipParts:s=>s.parts,dialogueFor:s=>project.script.filter(l=>l.speechReview?.status!=='suspect'&&l.start<s.end&&l.end>s.start),speechEligible:l=>l.speechReview?.status!=='suspect'};vm.createContext(c);vm.runInContext(html.slice(a,b),c);
const scene=(id,start,end,parts=[{id:'a',start,end,duration:end-start}])=>({id,start,end,parts,hasPerson:false,dialogueParts:{}}),line=(text,start,end)=>({id:'line',start,end,newText:text,original:'DO NOT READ ORIGINAL'});
const all=()=>project.scenes.flatMap(s=>s.parts.map(p=>c.speechForPart(s,p)));
const words=x=>x.trim().split(/\s+/u).filter(Boolean);
for(const text of ['Một hai ba bốn năm sáu bảy tám chín mười.','Một.','Lọ xanh,\n nắp đen; giữ nhãn thật!']){
 project.scenes=[scene('first',0,2.8),scene('second',2.8,6)];project.script=[line(text,0,6)];const before=JSON.stringify(project.script);const result=all();assert.deepEqual(words(result.map(x=>x.text).join(' ')),words(text));assert(result.every(x=>x.pending===false));assert.equal(JSON.stringify(project.script),before);
}
project.scenes=[scene('long',0,17,[{id:'a',start:0,end:8,duration:8},{id:'b',start:8,end:16,duration:8},{id:'c',start:16,end:17,duration:1}])];project.script=[line('một hai ba bốn năm sáu bảy tám chín mười mười-một mười-hai',0,17)];assert.deepEqual(words(all().map(x=>x.text).join(' ')),words(project.script[0].newText));
const old=all()[0].text;project.script[0].newText='THAY ĐỔI KỊCH BẢN';assert.notEqual(all()[0].text,old);assert.deepEqual(words(all().map(x=>x.text).join(' ')),words(project.script[0].newText));
project.scenes[0].dialogueParts.a='MANUAL';assert.equal(all()[0].text,'MANUAL');project.scenes[0].dialogueParts.a='';assert.equal(all()[0].text,'');delete project.scenes[0].dialogueParts.a;assert.notEqual(all()[0].text,'');
project.script[0].speechReview={status:'suspect'};assert(all().every(x=>x.text===''));project.script=[line('',0,17)];assert(all().every(x=>x.text===''));
console.log('PASS automatic clip allocation preserves every new-script word once across scenes/parts, punctuation and cache changes; respects manual/silent clips and excluded speech; never reads original');
