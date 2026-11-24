/* Frame edit settings are persisted input, never an image-generation side effect. */
(()=>{
 const defaults={width:1080,height:1920};
 const applied=s=>{const c=project.frameStudioDefaults;return c&&(!c.sceneIds||c.sceneIds.includes(s.id))?c:null;};
 const gcd=(a,b)=>b?gcd(b,a%b):a;
 function output(s){const c=applied(s),v=s.frameOutput||c?.output||project.frameOutputDefault||defaults,w=Number(v.width),h=Number(v.height);if(!Number.isInteger(w)||!Number.isInteger(h)||w<256||h<256||w>8192||h>8192||w*h>33554432)throw Error('Chiều rộng/cao phải là số nguyên 256–8192 px, tối đa 32 triệu điểm ảnh.');const d=gcd(w,h);return{width:w,height:h,ratio:w/d+':'+h/d};}
 function legacyPhysicalFacts(s){
  if(s.frameProductFactsVersion!==168)return '';
  const raw=String(project.productScript?.brief?.facts||project.refs.product?.description||'').slice(0,6000);
  const physical=/(?:\b\d+(?:[.,]\d+)?\s*(?:kg|mg|g|ml|cl|l|mm|cm)\b)|(?:kích thước|chiều cao|chiều rộng|chiều dài|đường kính|khối lượng|trọng lượng|dung tích|chất liệu|màu sắc|màu đỏ|màu xanh|nắp|hình trụ|height|width|diameter|dimensions|net weight|volume|material|colour|color|lid|cap)/i;
  return raw.split(/\n|[;；]/).map(t=>t.trim()).filter(t=>physical.test(t)).join('\n').slice(0,1800);
 }
 function cleanSpecs(raw){
  const text=String(raw||'').slice(0,6000),rows=[],add=(k,v)=>{if(v)rows.push(k+': '+v.replace(/\s+/g,' ').trim());};
  const scalar=(key,re)=>{for(const m of text.matchAll(re))add(key,m[1]);};
  scalar('Net weight',/(?:khối lượng(?: tịnh)?|trọng lượng(?: tịnh)?|net weight|weight)\s*[:：=-]?\s*(\d+(?:[.,]\d+)?\s*(?:kg|mg|g)\b)/giu);
  scalar('Capacity',/(?:dung tích|thể tích|capacity|net volume)\s*[:：=-]?\s*(\d+(?:[.,]\d+)?\s*(?:ml|cl|l)\b)/giu);
  scalar('Height',/(?:chiều cao|\bcao|\bheight)\s*[:：=-]?\s*(\d+(?:[.,]\d+)?\s*(?:mm|cm|m)\b)(?![²³23])/giu);
  scalar('Width',/(?:chiều rộng|\brộng|\bwidth)\s*[:：=-]?\s*(\d+(?:[.,]\d+)?\s*(?:mm|cm|m)\b)(?![²³23])/giu);
  scalar('Length',/(?:chiều dài|\bdài|\blength)\s*[:：=-]?\s*(\d+(?:[.,]\d+)?\s*(?:mm|cm|m)\b)(?![²³23])/giu);
  scalar('Diameter',/(?:đường kính|đk|diameter|[Ø⌀])\s*[:：=-]?\s*(\d+(?:[.,]\d+)?\s*(?:mm|cm|m)\b)(?![²³23])/giu);
  scalar('Dimensions',/(?:kích thước|dimensions|size)\s*[:：=-]?\s*(\d+(?:[.,]\d+)?\s*(?:(?:mm|cm)\s*)?(?:[x×]\s*\d+(?:[.,]\d+)?\s*(?:(?:mm|cm)\s*)?){1,2}(?:mm|cm)\b)/giu);
  for(const line of text.split(/\n|[;；]/)){const m=line.trim().match(/^(?:NET\s*[:：]?\s*)?(\d+(?:[.,]\d+)?\s*(kg|mg|g|ml|cl|l))\s*$/i);if(m)add(/^(ml|cl|l)$/i.test(m[2])?'Capacity':'Net weight',m[1]);}
  return [...new Set(rows)].join('; ');
 }
 function physicalFacts(s){return [169,170].includes(s.framePromptVersion)?cleanSpecs(project.productScript?.brief?.facts||project.refs.product?.description||''):legacyPhysicalFacts(s);}
 const flat=v=>String(v||'').replace(/\s+/g,' ').trim();
 function compact(s,lang='en'){
  const cfg=input(s),o=output(s),bindings=SFPromptPipeline.imageBindings(s),codes=role=>bindings.filter(b=>b.role===role).map(b=>b.code),products=codes('product'),people=codes('person'),outfits=codes('outfit'),backgrounds=codes('background');
  const notes=Object.fromEntries(refsFor(s).filter(k=>k!=='product').map(k=>[k,flat(sceneReference(s,k).description)]));
  const edits=[cfg.request?'Shared: '+flat(cfg.request):'',s.extraRequest?'User: '+flat(s.extraRequest):'',s.promptRevision?.image?'Scene: '+flat(s.promptRevision.image)+' (wins over shared edits to the same detail)':''].filter(Boolean).join(' ');
  const person=[people.length?'Use '+people.join(', ')+' for the appearance of people/parts already visible in R1; a hands-only shot stays hands-only.':'',notes.person?'Person: '+notes.person:'',outfits.length?'Use '+outfits.join(', ')+' for clothing.':people.length&&SFFrameIdentity.config().outfit==='person'?'Also use the person references for clothing.':people.length?'Keep R1 clothing.':'',notes.outfit?'Outfit: '+notes.outfit:''].filter(Boolean).join(' ');
  const product=products.length?'Use '+products[0]+' for the exact product shape, proportions, cap/top details and cap state, color/gradient, material and visible label. Replace the whole object naturally in the hand; do not reuse the old R1 product shape. Ignore the ad outside the product.'+(products.length>1?' '+products.slice(1).join(', ')+' are extra views of that same variant only.':''):'Keep the R1 product unless explicitly edited.';
  const facts=[products.length?cfg.physicalFacts:'',products.length&&cfg.productDimensions?'User dimensions: '+flat(cfg.productDimensions):''].filter(Boolean).join('; ');
  const rows=[
   ['REFERENCE ROLES',bindings.map(b=>b.code+' = '+(b.role==='source'?'source scene':b.role)).join('; ')+'.'],
   ['COMPOSITION','Keep R1 camera viewpoint, action, lighting and unselected details; selected replacements and explicit edits below take precedence.'],
   ['PRODUCT LOCK',product],
   ...(person?[['PERSON / OUTFIT LOCK',person]]:[]),
   ...(backgrounds.length||notes.background?[['BACKGROUND',(backgrounds.length?'Use '+backgrounds.join(', ')+' for the background; keep R1 viewpoint. ':'')+(notes.background||'')]]:[]),
   ...(facts?[['PHYSICAL FACTS',facts+'. Weight/capacity is not a height or diameter; do not invent lengths or label text.']]:[]),
   ...(edits?[['USER EDITS',edits]]:[]),
   ...(cfg.keptRoles.length?[['KEEP','Keep these R1 roles unchanged, including against shared edits: '+cfg.keptRoles.join(', ')+'.']]:[]),
   ['OUTPUT',o.width+' x '+o.height+' pixels; '+o.ratio+'; one '+(o.width<o.height?'portrait':o.width>o.height?'landscape':'square')+' image. Reframe without stretching the product.'],
   ['IMAGE QUALITY','Photorealistic, sharp product details, natural texture, shadows and reflections. Remove source subtitles/promo overlays, keep real packaging text. No new captions, watermark or collage.']
  ];
  const anchor=bindings.find(b=>b.role==='appearance');if(anchor)rows.splice(rows.length-2,0,['CONTINUITY',anchor.code+' assists only '+(anchor.matchingRoles||[]).join(', ')+'; original subject references take priority.']);
  if(lang==='vi'){
   const labels={'REFERENCE ROLES':'VAI TRÒ ẢNH','COMPOSITION':'BỐ CỤC','PRODUCT LOCK':'GIỮ ĐÚNG SẢN PHẨM','PERSON / OUTFIT LOCK':'NGƯỜI / TRANG PHỤC','BACKGROUND':'BỐI CẢNH','PHYSICAL FACTS':'THÔNG SỐ THẬT','USER EDITS':'YÊU CẦU','KEEP':'GIỮ NGUYÊN','OUTPUT':'ĐẦU RA','IMAGE QUALITY':'CHẤT LƯỢNG','CONTINUITY':'ĐỒNG NHẤT'};
   const translated={'REFERENCE ROLES':bindings.map(b=>b.code+' = '+({source:'cảnh gốc',product:'sản phẩm',person:'người',outfit:'trang phục',background:'bối cảnh',appearance:'diện mạo đã duyệt'}[b.role]||b.role)).join('; ')+'.','COMPOSITION':'Giữ góc máy, hành động, ánh sáng và phần không chọn thay của R1. Áp dụng các thay thế và yêu cầu rõ ràng bên dưới.','PRODUCT LOCK':products.length?'Sản phẩm theo '+products[0]+': đúng dáng, tỉ lệ, chi tiết và trạng thái nắp, màu/chuyển màu, chất liệu, nhãn thật. Thay toàn bộ đồ trong tay, không lấy vỏ đồ cũ R1. Bỏ phần quảng cáo ngoài sản phẩm.':'Giữ sản phẩm R1, trừ yêu cầu chỉnh rõ ràng.','PHYSICAL FACTS':facts+'. Khối lượng/dung tích không phải chiều cao hay đường kính; không bịa số đo hoặc chữ nhãn.','KEEP':'Giữ nguyên các phần sau của R1 kể cả khi yêu cầu chung khác: '+cfg.keptRoles.join(', ')+'.','OUTPUT':o.width+' × '+o.height+' px · '+o.ratio+' · một ảnh liền mạch, đổi khung không kéo méo sản phẩm.','IMAGE QUALITY':'Chân thực, rõ chi tiết sản phẩm, chất liệu, bóng và phản chiếu tự nhiên. Bỏ phụ đề/chữ quảng cáo đè của nguồn, giữ chữ thật trên bao bì. Không thêm phụ đề mới, watermark hoặc chia ô.'};
   return rows.map(([k,v])=>labels[k]+': '+flat(translated[k]||v)).join('\n');
  }
  return rows.map(([k,v])=>k+': '+flat(v)).join('\n');
 }
 function input(s){const c=applied(s),result={output:s.frameOutput||c?.output||project.frameOutputDefault||null,request:s.frameUseCommon===false?'':c?.request||'',productDimensions:c?.productDimensions||'',productPrimary:c?.productPrimary||'',productViews:c?.productViews===true,personEdit:s.frameUseCommon!==false&&c?.personEdit===true,keptRoles:Object.entries(s.frameReferenceChoices||{}).filter(([,v])=>v.mode==='keep').map(([k])=>k),enabled:s.frameEditPolicy===166};if(s.frameProductFactsVersion===168)result.physicalFacts=physicalFacts(s);if([169,170].includes(s.framePromptVersion))result.promptVersion=s.framePromptVersion;return result;}
 function reference(s,k,ref){
  if(k!=='product')return ref;
  const c=applied(s),primary=c?.productPrimary,custom=s.frameReferenceChoices?.product?.mode==='custom';
  if(!s.frameEditPolicy&&!primary)return ref;
  let index=primary?ref.images.findIndex((i,n)=>(i.id||'index:'+n)===primary):-1;
  const oldPending=(project.cloudJobs||[]).some(j=>j.sceneId===s.id&&j.kind==='image'&&j.frameStudioVersion===164&&!j.referenceManifest&&!['imported','failed','not_submitted','abandoned','stale','invalid'].includes(j.state));
  if(primary&&index<0&&!custom&&!oldPending){
   // A legacy per-scene filter must never silently swap the explicit common primary.
   const all=project.refs.product?.images||[],chosen=all.find((i,n)=>(i.id||'index:'+n)===primary);
   if(!chosen)return {...ref,images:[],selectionError:'Ảnh sản phẩm chính đã chọn không còn. Chọn lại ảnh chính trước khi tạo; chưa tự dùng ảnh khác.'};
   return {...ref,images:[typeof chosen==='string'?{image:chosen,primary:true}:{...chosen,primary:true}],selectionNote:'Dùng đúng ảnh chính chung, thay lựa chọn lọc cũ của cảnh.'};
  }
  if(!ref.images.length)return ref;
  if(index<0)index=Math.max(0,ref.images.findIndex(i=>i.primary));
  const images=c?.productViews?ref.images.map((i,n)=>typeof i==='string'?{image:i,primary:n===index}:{...i,primary:n===index}):[typeof ref.images[index]==='string'?{image:ref.images[index],primary:true}:{...ref.images[index],primary:true}];
  return {...ref,images};
 }

 function compose(s,base,lang='en'){
  const r=project.promptPipeline?.records?.[s.id+':image:'];if(s.framePromptVersion===169){if(typeof s.framePromptOverride==='string')return s.framePromptOverride;if(r?.applied&&!r.localRecipe&&r.result?.promptFrame)return r.result.promptFrame[lang]||r.result.promptFrame.en;return compact(s,lang);}if(!s.frameEditPolicy&&!r?.frameEditPolicy)return base; // Old pending jobs retain their exact prompt/signature.
  const config=input(s),o=output(s),bound=SFPromptPipeline.imageBindings(s).filter(b=>b.role==='product'),product=bound.length>0,keep=Object.entries(s.frameReferenceChoices||{}).filter(([,v])=>v.mode==='keep').map(([k])=>k);
  const en=[
   'FINAL FRAME EDIT SETTINGS — override conflicting source-derived appearance and output-size instructions above.',
   'OUTPUT: '+o.width+' x '+o.height+' pixels; aspect ratio '+o.ratio+'. One unified '+(o.width<o.height?'portrait':o.width>o.height?'landscape':'square')+' photograph. Recompose the outer canvas when needed; do not stretch the person or product, crop off the product, or add panels. Keep the original camera direction and action, not its old canvas aspect ratio.',
   product?'AUTHORITATIVE PRODUCT: '+bound[0]?.code+' is the primary replacement product. Other product references are supplementary views ONLY if they show that same variant. Any continuity anchor is subordinate to this primary product reference; never copy a conflicting anchor product. Discard R1 product silhouette, cap, proportions, color, surface, label and brand. Replace the whole object, not just its printed text or color. Copy the primary reference object\'s height-to-width ratio, outline, cap thickness and geometry, seams, material, true base color/gradient, logo and label layout. Do not average different packages or inherit the old source jar\'s design. Use only the product inside an advertising reference; ignore its surrounding ad text, hand and background. Preserve its own relative dimensions; adapt placement and hand contact to its geometry rather than forcing it into the old object shape.':'PRODUCT: keep the source product; no replacement product is selected.',
   product&&config.productDimensions?'REAL PRODUCT DIMENSIONS supplied by the user: '+config.productDimensions+'. Use these for scale relative to hand/environment, not as captions.':'Do not infer exact physical size from an uncalibrated photograph. Use physically plausible scale and the reference product proportions; never enlarge the product to fill the frame.',
   product&&config.physicalFacts?'DECLARED PHYSICAL PRODUCT FACTS from the user script brief (literal supplied data, not observed source-video facts):\n'+config.physicalFacts+'\nUse explicit height/width/diameter measurements for physical scale if supplied and applicable to this selected variant. Weight such as 200 g or capacity such as 200 ml does NOT determine height, diameter or a solid volume; never convert mass/capacity into invented centimetres. The primary image remains authoritative for shape, cap geometry, colors, finish and authentic visible label. Do not overwrite its design or print the brief text as a caption/label. If the brief refers to another variant, do not import visual details from that variant. Explicit real-dimension input above takes precedence over conflicting brief measurements.':'',
   'DETAIL: high-end photorealistic product photography with 4K-level detail and clarity, natural high-definition photographic detail, accurate material and reference colors under the scene lighting, clean edges, real texture, no invented embossed details, no waxy skin or excessive sharpening. Preserve authentic visible product lettering; do not invent unreadable text.',
   config.personEdit?'VISIBLE PERSON EDIT: apply the shared request to the body parts actually visible in each source shot. A hands-only shot remains hands-only: preserve finger count, grip/action and contact points, change the requested hand appearance, never add a face or a full person. A wide shot remains wide. Do not copy the hand from a product advertising reference.':'',
   config.request?'SHARED USER EDIT for this selected scene: '+config.request+'. Explicitly requested edits may change the named source parts even without a replacement image; keep all unmentioned parts unchanged.':'',
   s.promptRevision?.image?'SCENE-SPECIFIC EDIT (takes precedence over shared wording for the same property): '+s.promptRevision.image:'',
   keep.length?'EXPLICIT PER-SCENE KEEP (highest priority for these roles): '+keep.join(', ')+'. Do not change these roles even when a shared request asks otherwise.':'',
   'Return the finished edited image, not an explanation. Requested pixel dimensions are the generation target, not permission to fake detail.'
  ].filter(Boolean).join('\n\n');
  const vi=['YÊU CẦU ẢNH CUỐI: '+o.width+' × '+o.height+' px · '+o.ratio+'. Đổi khung theo tỉ lệ đã chọn, không kéo méo người hoặc sản phẩm.',product?'Sản phẩm theo ảnh tham chiếu chính: thay toàn bộ hình dáng, nắp, tỉ lệ, màu, chất liệu và nhãn; không giữ vỏ sản phẩm gốc, không chỉ đổi chữ/màu. Ảnh quảng cáo chỉ lấy sản phẩm, bỏ tay và bối cảnh trong ảnh tham chiếu.':'Giữ sản phẩm gốc.',config.productDimensions?'Kích thước sản phẩm thật: '+config.productDimensions:'',product&&config.physicalFacts?'Thông số lấy từ Kịch bản: '+config.physicalFacts+' · Khối lượng/dung tích không suy ra số cm. Giữ thiết kế, màu và chữ theo ảnh chính, không biến thông số thành chữ mới trên nhãn.':'',config.personEdit?'Chỉ đổi phần người đang xuất hiện: cảnh có tay chỉ đổi tay, giữ cách cầm, không thêm cả người.':'',config.request?'Yêu cầu chung: '+config.request:'',s.promptRevision?.image?'Yêu cầu riêng: '+s.promptRevision.image:'',keep.length?'Giữ nguyên theo lựa chọn riêng: '+keep.join(', '):''].filter(Boolean).join('\n\n');
  return base+'\n\n'+(lang==='vi'?vi:en);
 }
 const before=imageFramePrompt;imageFramePrompt=(s,lang='en')=>s.framePromptVersion===170?SFUniversalFrame.current(s,lang):compose(s,before(s,lang),lang);
 window.SFFrameSettings={output,input,physicalFacts,cleanSpecs,compact,reference,applied,compose,defaults};
})();
