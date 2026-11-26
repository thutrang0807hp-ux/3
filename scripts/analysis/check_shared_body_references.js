// Execute the actual role resolver and byte packer, including a legacy hands-only scene.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync('workflow.html','utf8');
const fn=name=>html.split('\n').find(l=>l.startsWith(name));
const refs=Object.fromEntries(['product','person','outfit','background'].map(k=>[k,{images:[],description:''}]));
refs.product.images=[{id:'jar',asset:'jar'}];refs.person.images=[{id:'nails',asset:'nails',personId:'p1'}];refs.person.people=[{id:'p1'}];
const s={id:'s',refsUsed:['product'],referencePeople:['p1']};
const c={project:{refs},window:{},assets:new Map([['jar','PRODUCT_BYTES'],['nails','NAIL_BYTES']]),SFPromptContract:{orderedImages:a=>a},SFFrameIdentity:{binding:()=>null,anchor:()=>null},productFrameContext:()=>null,record:()=>null,directEvidence:()=> 'SOURCE_BYTES',blob:async x=>x,encode:async x=>x};
vm.createContext(c);vm.runInContext(fn('function sceneReference(')+'\n'+html.slice(html.indexOf('function refsFor('),html.indexOf('\nfunction sceneReferenceSignature'))+'\n'+fn('function imageBindings(')+'\n'+fn('async function generationRefs('),c);c.s=s;
(async()=>{
 assert.deepEqual(Array.from(c.refsFor(s)),['product','person']);
 assert.deepEqual(Array.from(c.imageBindings(s),b=>b.role),['source','product','person']);
 assert.deepEqual(Array.from(await c.generationRefs(s)),['SOURCE_BYTES','PRODUCT_BYTES','NAIL_BYTES']);
 s.frameReferenceChoices={person:{mode:'keep'}};assert(!c.refsFor(s).includes('person'));
 s.frameReferenceChoices.person={mode:'custom',images:[{id:'own',asset:'own'}]};c.assets.set('own','PRIVATE_NAIL_BYTES');s.referenceRoleOverrides={person:false};
 assert.deepEqual(Array.from(await c.generationRefs(s)),['SOURCE_BYTES','PRODUCT_BYTES','PRIVATE_NAIL_BYTES']);
 delete s.frameReferenceChoices.person;assert(!c.refsFor(s).includes('person'));delete s.referenceRoleOverrides.person;
 refs.person.images.push({id:'other',asset:'other',personId:'p2'});refs.person.people.push({id:'p2'});
 assert.equal(c.sceneReference(s,'person').images.length,1,'preserve chosen person');
 refs.outfit.images=[{id:'dress',asset:'dress'}];c.assets.set('dress','DRESS_BYTES');assert(c.refsFor(s).includes('outfit'));
 // Video calls explicitly omit replacement roles; keep that transport behavior.
 assert.deepEqual(Array.from(await c.generationRefs(s,null,false)),['SOURCE_BYTES']);
 console.log('PASS shared nail bytes sent with product, matching bindings/order; keep/custom/explicit exclusion and person selection preserved; no roles in video-only packing');
})().catch(e=>{console.error(e);process.exitCode=1;});
