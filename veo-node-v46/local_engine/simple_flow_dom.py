"""Visible-UI adapter. Unknown layouts require review; never infer a paid retry."""
import asyncio,re,time

CREATE=re.compile(r'^(Generate|Create video|Tạo video|Tạo)$',re.I)

async def composer(page):
 editors=page.locator('textarea,[contenteditable="true"],[role="textbox"]').filter(visible=True)
 if await editors.count()!=1:return None,None
 editor=editors.first
 # Keep controls scoped to the composer, never to all historical result cards.
 scope=editor.locator('xpath=ancestor::form[1]')
 if await scope.count()!=1:
  # Non-form Flow layouts keep image controls beside the inner prompt row.
  # Choose the smallest composer containing Generate, not an arbitrary + row.
  scope=None
  for depth in range(1,8):
   candidate=editor.locator('xpath=ancestor::*['+str(depth)+']')
   if await candidate.count()!=1 or await candidate.evaluate('(e)=>["BODY","HTML"].includes(e.tagName)'):break
   if await candidate.locator('article,video').count():break
   named=candidate.get_by_role('button',name=CREATE).filter(visible=True)
   icons=candidate.locator('button').filter(has_text=re.compile(r'^\s*arrow_forward\s*$')).filter(visible=True)
   if await named.count()==1 or await icons.count()==1:
    scope=candidate;break
  if scope is None:return editor,None
 if await scope.count()!=1:return editor,None
 return editor,scope

async def create_button(page):
 editor,scope=await composer(page)
 buttons=(scope or page).get_by_role('button',name=CREATE).filter(visible=True)
 if await buttons.count()==1 and await buttons.is_enabled():return buttons
 if scope is not None:
  icons=scope.locator('button').filter(has_text=re.compile(r'^\s*arrow_forward\s*$')).filter(visible=True)
  if await icons.count()==1 and await icons.is_enabled():return icons
 return None

async def wait_composer(page,check,timeout=90):
 """DOM navigation and an account marker do not mean the Flow app has loaded."""
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  await check()
  editor,scope=await composer(page)
  if editor is not None and scope is not None and await editor.is_editable():
   # Generate may remain disabled until image/prompt are supplied.
   buttons=scope.get_by_role('button',name=CREATE).filter(visible=True)
   icons=scope.locator('button').filter(has_text=re.compile(r'^\s*arrow_forward\s*$')).filter(visible=True)
   if await buttons.count()==1 or await icons.count()==1:return True
  await asyncio.sleep(.25)
 return False

async def settings_ready(page):
 _,scope=await composer(page)
 if scope is None:return False
 # Read actual controls, not the body (which may mention an old model in history).
 controls=scope.locator('button,[role="combobox"],select').filter(visible=True)
 text=' '.join(await controls.evaluate_all('''xs=>xs.filter(e=>{const values=['aria-selected','aria-pressed','aria-checked'].map(a=>e.getAttribute(a));if(values.includes('false'))return false;if(['tab','radio','option','menuitemradio'].includes(e.getAttribute('role')))return values.includes('true')||['active','checked'].includes(e.getAttribute('data-state'));return true;}).map(e=>e.tagName==='SELECT'?(e.selectedOptions[0]?.textContent||''):(e.innerText||''))'''))
 return bool(re.search(r'Veo.*Lite|Lite.*Veo',text,re.I) and
  re.search(r'8\s*(?:s\b|sec|giây)',text,re.I) and re.search(r'9\s*:\s*16',text) and
  re.search(r'(?:\bx\s*1\b|\b1\s*x\b)',text,re.I) and
  re.search(r'Ingredients to Video|\bIngredients\b|Thành phần thành video|Từ thành phần|Thành phần',text,re.I))

async def _prepare_settings(page):
 if await settings_ready(page):return True
 _,scope=await composer(page)
 if scope is None:return False
 ingredients=scope.get_by_role('tab',name=re.compile(r'^(Ingredients to Video|Ingredients|Thành phần thành video|Thành phần)$',re.I)).filter(visible=True)
 if await ingredients.count()==1 and await ingredients.get_attribute('aria-selected')!='true' and await ingredients.get_attribute('data-state')not in ('active','checked'):await ingredients.click(timeout=3000)
 # Standard select controls can be configured without guessing popover structure.
 choices=[(r'model|mô hình',r'Veo.*Lite|Lite.*Veo'),(r'duration|thời lượng',r'^8\s*(s|seconds?|giây)$'),
  (r'aspect|ratio|tỉ lệ|tỷ lệ',r'9\s*:\s*16'),(r'outputs?|số lượng',r'^(1|x1|1x)$'),
  (r'mode|chế độ',r'Ingredients to Video|Ingredients|Thành phần thành video|Từ thành phần')]
 for label,desired in choices:
  selects=scope.get_by_role('combobox',name=re.compile(label,re.I)).filter(visible=True)
  if await selects.count()!=1 or await selects.evaluate('(e)=>e.tagName')!='SELECT':continue
  options=await selects.locator('option').evaluate_all('(xs)=>xs.map(e=>({label:e.textContent,value:e.value,disabled:e.disabled}))')
  matched=[x for x in options if not x['disabled'] and re.search(desired,x['label'],re.I)]
  if len(matched)==1:await selects.select_option(matched[0]['value'])
 # Flow also uses button popovers. Only named settings controls and exact
 # options are eligible; this path never presses Generate or an image tile.
 popovers=[(r'^(Text to Video|Frames to Video|Ingredients to Video|Từ văn bản|Từ khung hình|Khung hình thành video)$',r'^(Ingredients to Video|Ingredients|Từ thành phần|Thành phần thành video)$'),
  (r'^Veo\s+\d.*',r'^Veo\s+3\.1\s*[-·]?\s*Lite$'),
  (r'^\d+\s*(s|seconds?|giây)$',r'^8\s*(s|seconds?|giây)$'),
  (r'^(9\s*:\s*16|16\s*:\s*9)$',r'^9\s*:\s*16$'),
  (r'^(x\s*[1-4]|[1-4]\s*x)$',r'^(x\s*1|1\s*x)$')]
 for trigger_name,desired in popovers:
  trigger=scope.get_by_role('button',name=re.compile(trigger_name,re.I)).filter(visible=True)
  if await trigger.count()!=1:continue
  label=(await trigger.inner_text()).strip()
  if re.fullmatch(desired,label,re.I)or ('Lite'in label and '8'in label and '9:16'in label):continue
  await trigger.click(timeout=3000)
  options=page.get_by_role('option',name=re.compile(desired,re.I)).or_(page.get_by_role('menuitem',name=re.compile(desired,re.I))).filter(visible=True)
  try:
   await options.first.wait_for(state='visible',timeout=1500)
   if await options.count()==1 and await options.is_enabled():await options.click(timeout=3000)
   else:await trigger.press('Escape')
  except Exception:await trigger.press('Escape')
 return await settings_ready(page)

async def prepare_settings(page):
 try:return await _prepare_settings(page)
 except Exception:return False

async def previews(page):
 _,scope=await composer(page)
 if scope is None:return []
 return await scope.locator('img').evaluate_all('xs=>xs.filter(e=>e.getClientRects().length&&e.complete&&e.naturalWidth>32&&e.naturalHeight>32).map(e=>e.currentSrc||e.src)')

async def uploaded_preview(page,before,timeout=30):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  current=await previews(page)
  # Exactly one newly attached preview; no uploading progress still in the composer.
  _,scope=await composer(page)
  if len(current)==len(before)+1 and len([x for x in current if x and x not in before])==1 and scope is not None:
   busy=scope.locator('[role=progressbar],[aria-busy=true]').filter(visible=True)
   errors=scope.get_by_role('alert').filter(visible=True)
   if not await busy.count() and not await errors.count():return True
  await asyncio.sleep(.25)
 return False

SNAPSHOT=r'''prompt => {
 const normalize=s=>String(s||'').replace(/\s+/g,' ').trim(),needle=normalize(prompt);
 // Flow sometimes renders plain div cards without a server ID. Give a local
 // identity to the narrowest container holding ONE activity and its prompt.
 const anchors=[...document.querySelectorAll('video,[role="progressbar"],span')].filter(e=>e.matches('video,[role="progressbar"]')||/^\s*\d{1,3}\s*%\s*$/.test(e.innerText||''));
 if(needle.length>=8)for(const anchor of anchors){
  let e=anchor.parentElement;
  for(let depth=0;e&&depth<7&&e!==document.body;depth++,e=e.parentElement){
   if(!normalize(e.innerText).includes(needle))continue;
   if(anchors.filter(a=>e.contains(a)).length!==1)break;
   if(!e.id&&!e.matches('[data-generation-id],[data-media-id],[data-id],[data-sceneforge-result-id]'))e.setAttribute('data-sceneforge-result-id',crypto.randomUUID());
   break;
  }
 }
 const selector='article,[data-generation-id],[data-media-id],[data-id],[data-sceneforge-result-id]';
 const seen=new Set();return [...document.querySelectorAll(selector)].filter(e=>e.getClientRects().length).map(e=>{
  const attr=['data-generation-id','data-media-id','data-id','data-sceneforge-result-id','id'].find(a=>e.getAttribute(a));
  if(!attr)return null;const id=attr+'='+e.getAttribute(attr);if(seen.has(id))return null;seen.add(id);
  const bar=e.querySelector('[role="progressbar"]'),text=e.innerText||'';
  const raw=bar?.getAttribute('aria-valuenow'),max=Number(bar?.getAttribute('aria-valuemax')||100);
  // Do not mistake a percentage in the user's prompt for generation progress.
  const percentNodes=[...e.querySelectorAll('span,[role="status"]')].filter(n=>n.getClientRects().length&&/^\s*\d{1,3}\s*%\s*$/.test(n.innerText||''));
  const percent=percentNodes.length===1?(percentNodes[0].innerText||'').match(/(\d{1,3})\s*%/):null;
  let progress=raw!==null&&raw!==undefined&&raw!==''&&max>0?Number(raw)/max*100:percent?Number(percent[1]):null;
  if(!Number.isFinite(progress)||progress<0||progress>100)progress=null;else progress=Math.round(progress*100)/100;
  const videos=[...e.querySelectorAll('video')].filter(v=>v.getClientRects().length&&(v.currentSrc||v.src));
  const failed=/generation failed|couldn.t generate|tạo không thành công|không thể tạo|tạo thất bại/i.test(text);
  return {id,attr,value:e.getAttribute(attr),text,progress,failed,existed:!!window.__sfFlowOldCards?.has(e)||videos.some(v=>window.__sfFlowOldCards?.has(v)),video:videos.length===1,media_url:videos.length===1?(videos[0].currentSrc||videos[0].src):null,
   activity:!!bar||!!percent||videos.length>0||failed||/generating|queued|đang tạo|đang chờ/i.test(text)};
 }).filter(Boolean);
}'''

class ResultObserver:
 """Attribute a new stable card by its prompt. Never pick a first/old video."""
 def __init__(self,page,prompt):self.page=page;self.prompt=' '.join(prompt.split());self.before=set();self.card=None;self.ambiguous=False;self.clicked=False;self.auto_download=None
 async def baseline(self):
  self.before={x['id']for x in await self.page.evaluate(SNAPSHOT,self.prompt)}
  await self.page.evaluate('()=>{window.__sfFlowOldCards=new WeakSet(document.querySelectorAll("body *"));}')
 async def read(self):
  if not await self.page.evaluate('()=>!!window.__sfFlowOldCards'):
   self.ambiguous=True;return None
  rows=await self.page.evaluate(SNAPSHOT,self.prompt)
  candidates=[x for x in rows if not x['existed'] and x['id']not in self.before and x['activity'] and len(self.prompt)>=8 and self.prompt in ' '.join(x['text'].split())]
  if len(candidates)>1:self.ambiguous=True
  if self.ambiguous:return None
  if self.card:
   match=[x for x in rows if x['id']==self.card]
   return match[0]if len(match)==1 and self.prompt in ' '.join(match[0]['text'].split()) else None
  # Nested containers for the same result are also ambiguous: don't guess.
  if len(candidates)!=1:return None
  self.card=candidates[0]['id'];return candidates[0]
 async def download(self,row,register):
  if self.clicked or not row.get('video'):return False
  card=self.page.locator('['+row['attr']+']').filter(visible=True)
  matches=[]
  for item in await card.all():
   if await item.get_attribute(row['attr'])==row['value']:matches.append(item)
  if len(matches)!=1:return False
  card=matches[0];await card.hover()
  names=re.compile(r'^(Download|Download video|Tải xuống|Tải video)$',re.I)
  buttons=card.get_by_role('button',name=names).or_(card.get_by_role('link',name=names)).filter(visible=True)
  if await buttons.count()==0:
   buttons=card.locator('button').filter(has_text=re.compile(r'^\s*(download|file_download)\s*$',re.I)).filter(visible=True)
  if await buttons.count()!=1 or not await buttons.is_enabled():return False
  self.clicked=True
  # Only this click's event can suppress manual result review.
  async with self.page.expect_download(timeout=15000)as pending:
   await buttons.click(timeout=5000)
   # Some Flow layouts open a download menu. Only an original, non-generative
   # download option is eligible; never click upscale or generate again.
   await asyncio.sleep(.2)
   options=self.page.get_by_role('menuitem',name=re.compile(r'^(Original|Original size|Download original|720p|Gốc|Tải bản gốc)(\s*\(.*\))?$',re.I)).filter(visible=True)
   if await options.count()==1 and await options.is_enabled():await options.click(timeout=5000)
  self.auto_download=await pending.value;register(self.auto_download)
  return True
