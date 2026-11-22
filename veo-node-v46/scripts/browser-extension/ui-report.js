'use strict';
// Explicit, local-only diagnostics: allow-listed UI names, no page text/URLs/values.
function sceneForgeFlowUiReport(){
 const roots=[document];
 for(let index=0;index<roots.length&&index<40;index++)for(const node of roots[index].querySelectorAll('*'))if(node.shadowRoot)roots.push(node.shadowRoot);
 const visible=e=>!!e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden';
 const safeLabel=raw=>{
  const normalized=String(raw||'').normalize('NFKC').replace(/[\u2010-\u2015\u2212\u00b7-]/g,' ').replace(/\s+/g,' ').trim();
  const model=normalized.match(/^(Veo\s*\d(?:\.\d+)?\s*(?:Lite|Fast|Quality)?|Omni\s*\d(?:\.\d+)?\s*(?:Flash)?|Nano Banana(?:\s*\d(?:\.\d+)?)?\s*(?:Lite|Pro)?)(?=\s|$)/i);
  if(model)return model[0].trim();
  const known=normalized.match(/^(Agent|Tác nhân|Settings|Generation settings|Cài đặt|Video|Videos|Frames to Video|Frames|Khung hình|16:9|9:16|x1|x2|x3|x4|Image generation default|Video generation default|Save|Lưu|8s|8 giây|9:16|x1)$/i);
  return known?known[0]:'[other]';
 };
 const caption=e=>{
  const copy=e.cloneNode(true);copy.querySelectorAll('i,.material-icons,.material-symbols-outlined').forEach(n=>n.remove());
  const aria=safeLabel(e.getAttribute('aria-label')),text=safeLabel(copy.textContent);
  return {name:aria!=='[other]'?aria:text,aria_name:aria,text_name:text,aria_present:e.hasAttribute('aria-label')};
 };
 const editors=roots.flatMap(r=>Array.from(r.querySelectorAll('textarea,[contenteditable="true"],[contenteditable="plaintext-only"]')).filter(visible));
 const editorDepth=node=>{if(editors.length!==1)return null;let ancestor=editors[0].parentElement;for(let depth=0;ancestor&&depth<7&&ancestor!==document.body&&ancestor!==document.documentElement;depth++,ancestor=ancestor.parentElement)if(ancestor.contains(node))return depth;return null;};
 const controls=[];let total=0;
 for(let index=0;index<roots.length;index++){
  for(const node of roots[index].querySelectorAll('button,[role="button"],[role="option"],[role="menuitem"],[role="menuitemradio"],[role="menuitemcheckbox"],select,[role="combobox"],option')){
   if(!visible(node))continue;total++;
   const names=caption(node);if(names.name==='[other]'&&!node.matches('select,[role="combobox"]'))continue;
   const attr=(key,allowed)=>allowed.includes(node.getAttribute(key))?node.getAttribute(key):null;
   controls.push({root:index,tag:node.tagName,role:attr('role',['button','option','menuitem','menuitemradio','menuitemcheckbox','combobox']),...names,
    editor_ancestor_depth:editorDepth(node),haspopup:attr('aria-haspopup',['true','menu','listbox','dialog']),expanded:attr('aria-expanded',['true','false']),pressed:attr('aria-pressed',['true','false']),state:attr('data-state',['active','inactive','checked','unchecked','on','off','open','closed']),selected:attr('aria-selected',['true','false']),checked:attr('aria-checked',['true','false']),disabled:!!node.disabled});
  }
 }
 const summaries=[];
 for(const root of roots)for(const node of root.querySelectorAll('button,[role="button"]')){
  if(!visible(node))continue;const text=node.textContent.normalize('NFKC').replace(/\s+/g,' ').trim();
  if(!/^Video\b/i.test(text)||!/\b\d{3,4}p\b/.test(text))continue;
  const duration=text.match(/\b(\d+)\s*(?:giây|seconds?|s\b)/i),quantity=text.match(/\bx\s*([1-4])\b/i);
  summaries.push({duration:duration?Number(duration[1]):null,quantity:quantity?Number(quantity[1]):null});
 }
 const last=globalThis.__sceneForgeDomDiagnostic;
 return {report_version:4,page_kind:(location.hostname==='labs.google'?/^\/fx\/(?:[a-z]{2}(?:-[a-z]{2})?\/)?tools\/flow\/project\/[a-zA-Z0-9_-]+\/?$/i:/^\/project\/[a-zA-Z0-9_-]+\/?$/).test(location.pathname)?'project':'home',video_summaries:summaries,agent_defaults_visible:Array.from(document.querySelectorAll('h1,h2,h3,h4,[role="heading"],label,p,span')).filter(visible).some(e=>/^(Agent settings|Cài đặt tác nhân|Video generation default)$/i.test(e.textContent.trim())),extension_adapter:last?.adapter||null,last_failure:last?{stage:last.stage,code:last.code}:null,origin:location.hostname==='flow.google.com'?'flow.google.com':location.hostname==='labs.google'?'labs.google':'other',roots:roots.length,visible_controls:total,controls:controls.slice(0,100),editable_count:roots.reduce((n,r)=>n+Array.from(r.querySelectorAll('textarea,[contenteditable="true"],[contenteditable="plaintext-only"]')).filter(visible).length,0),iframe_count:document.querySelectorAll('iframe').length,generated_content:false,contains_cookie_values:false,contains_prompts:false};
}
