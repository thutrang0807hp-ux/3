"""Configure the visible Flow settings panel and read back every requested value."""
import asyncio,re,time
from .simple_flow_upload import prompt_composer

PANEL_SCRIPT=r'''() => {
 const visible=e=>!!e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden'&&getComputedStyle(e).opacity!=='0';
 const text=e=>{const c=e.cloneNode(true);c.querySelectorAll('i,svg,[class*=symbol],[class*=material]').forEach(x=>x.remove());return(c.textContent||e.getAttribute('aria-label')||'').normalize('NFKC').replace(/[\u2010-\u2015\u2212·•-]/g,' ').replace(/\s+/g,' ').trim().toLowerCase()};
 const selector='button,[role=button],[role=tab],[role=radio],[role=option],[role=menuitemradio],select';
 const controls=root=>[...root.querySelectorAll(selector)].filter(visible);
 document.querySelectorAll('[data-sf-flow-settings]').forEach(e=>e.removeAttribute('data-sf-flow-settings'));
 const roots=[];
 for(const button of controls(document).filter(e=>text(e)==='video')){
  for(let e=button.parentElement,depth=0;e&&e!==document.body&&depth<8;e=e.parentElement,depth++){
   const labels=controls(e).map(text);
   if(labels.includes('image')&&labels.includes('video')&&labels.some(x=>/^(ingredients|frames|veo|nano|imagen|\d+\s*:\s*\d+)/.test(x))){if(!roots.includes(e))roots.push(e);break;}
  }
 }
 if(!roots.length)return null;
 roots.sort((a,b)=>a.getBoundingClientRect().width*a.getBoundingClientRect().height-b.getBoundingClientRect().width*b.getBoundingClientRect().height);
 if(roots.length>1&&!roots[1].contains(roots[0]))return null;
 const root=roots[0];root.setAttribute('data-sf-flow-settings','current');
 function light(e){for(let n=e;n;n=n.parentElement){const color=getComputedStyle(n).backgroundColor;const a=color.match(/[\d.]+/g)?.map(Number)||[];if(a.length>=3&&(a.length<4||a[3]>.95))return(.2126*a[0]+.7152*a[1]+.0722*a[2])/255;}return null;}
 return controls(root).map((e,i)=>{
  e.setAttribute('data-sf-flow-setting',String(i));
  const values=['aria-selected','aria-pressed','aria-checked'].map(a=>e.getAttribute(a));let selected=null;
  if(values.includes('false'))selected=false;else if(values.includes('true'))selected=true;
  const state=e.getAttribute('data-state');if(selected===null&&['active','checked','on'].includes(state))selected=true;if(selected===null&&['inactive','unchecked','off'].includes(state))selected=false;
  const label=e.tagName==='SELECT'?text(e.selectedOptions[0]||e):text(e);
  return {token:String(i),label,role:e.getAttribute('role'),selected,light:light(e),tag:e.tagName,disabled:!!e.disabled};
 });
}'''

GROUPS={
 'video':('video',{'video','image'}),
 'ingredients':('ingredients',{'ingredients','ingredients to video','frames','frames to video'}),
 'ratio':('9:16',{'9:16','16:9'}),
 'outputs':('x1',{'x1','x2','x3','x4','1x','2x','3x','4x'})}
def clean(label):return re.sub(r'\s+','',label)if re.fullmatch(r'(?:\d+\s*:\s*\d+|x\s*[1-4]|[1-4]\s*x)',label)else label

def selected_group(rows,name):
 desired,labels=GROUPS[name]
 items=[{**row,'label':clean(row['label'])}for row in rows if clean(row['label'])in labels]
 wanted=[x for x in items if x['label']==desired or name=='ingredients'and x['label']=='ingredients to video' or name=='outputs'and x['label']=='1x']
 if len(wanted)!=1:return None,None
 explicit=[x for x in items if x['selected']is True]
 if explicit:return len(explicit)==1 and explicit[0]['token']==wanted[0]['token'],wanted[0]
 if wanted[0]['selected']is False:return False,wanted[0]
 # The supplied dark Flow UI highlights selected toggles with a lighter background.
 ranked=sorted([x for x in items if x['light']is not None],key=lambda x:x['light'],reverse=True)
 if len(ranked)>=2 and ranked[0]['light']-ranked[1]['light']>=.04:
  return ranked[0]['token']==wanted[0]['token'],wanted[0]
 return None,wanted[0]

def lite(label):return bool(re.fullmatch(r'veo\s*3\.1\s+lite',label))

async def configure_flow_settings(page,check,report,verify_only=False):
 """Never click Generate; ambiguous or unreadable setting states stop preparation."""
 async def fail(message):report['preparation_error']=message;return False
 async def panel():
  rows=await page.evaluate(PANEL_SCRIPT)
  if rows is not None:return rows
  editor,scope=await prompt_composer(page)
  if scope is None:return None
  trigger=scope.get_by_role('button',name=re.compile(r'^(Settings trigger|Generation settings)$',re.I)).filter(visible=True)
  if await trigger.count()!=1:return None
  await check();report['preparation_stage']='open_settings_panel'
  if await trigger.get_attribute('aria-expanded')!='true':await trigger.click(timeout=5000)
  end=time.monotonic()+3
  while time.monotonic()<end:
   rows=await page.evaluate(PANEL_SCRIPT)
   if rows is not None:return rows
   await asyncio.sleep(.1)
  report['settings_menu_unrecognized']=await page.locator('button,[role=tab],[role=radio],[role=option],select').filter(visible=True).evaluate_all("xs=>xs.slice(0,160).map(e=>{const r=e.getBoundingClientRect();return {name:e.getAttribute('aria-label'),text:(e.innerText||'').slice(0,160),role:e.getAttribute('role'),state:e.getAttribute('data-state'),selected:e.getAttribute('aria-selected'),pressed:e.getAttribute('aria-pressed'),left:r.left,top:r.top}})")
  return None
 async def snapshot():
  rows=await panel()
  if rows is not None:report['settings_controls']=rows
  return rows
 await check()
 # Close upload/asset-picker overlays before inspecting the composer settings.
 await page.keyboard.press('Escape')
 rows=await snapshot()
 if rows is None:return await fail('Chưa mở và đọc được bảng cài đặt Flow; chưa điền prompt.')
 for name in ('video','ingredients'):
  await check();rows=await snapshot()
  if rows is None:return await fail('Bảng cài đặt Flow đã đóng hoặc thay đổi.')
  selected,target=selected_group(rows,name)
  if selected is not True:
   if verify_only:return await fail('Cấu hình '+name+' đã thay đổi; chưa điền prompt.')
   if target is None or target['disabled']:return await fail('Chưa tìm được lựa chọn '+name+' duy nhất trong bảng Flow.')
   report['preparation_stage']='set_'+name
   await page.locator('[data-sf-flow-settings=current] [data-sf-flow-setting="'+target['token']+'"]').click(timeout=3000)
   end=time.monotonic()+3
   while time.monotonic()<end:
    rows=await snapshot()
    if rows is not None and selected_group(rows,name)[0]is True:break
    await asyncio.sleep(.1)
   else:return await fail('Chưa xác nhận lựa chọn '+name+' đã được áp dụng; không tự coi là thành công.')
 rows=await snapshot()
 models=[row for row in (rows or[])if re.match(r'^(veo|imagen|nano)\b',row['label'])]
 if len(models)!=1:return await fail('Chưa đọc duy nhất mô hình đang chọn trên Flow.')
 if not lite(models[0]['label']):
  if verify_only:return await fail('Mô hình Flow đã đổi; chưa điền prompt.')
  report['preparation_stage']='set_model'
  trigger=page.locator('[data-sf-flow-settings=current] [data-sf-flow-setting="'+models[0]['token']+'"]')
  if models[0]['tag']=='SELECT':
   options=await trigger.locator('option').evaluate_all('xs=>xs.map(e=>({text:e.textContent,value:e.value}))')
   wanted=[x for x in options if lite(re.sub(r'[-·–—]',' ',x['text']).strip().lower())]
   if len(wanted)!=1:return await fail('Chưa có lựa chọn Veo 3.1 Lite duy nhất.')
   await trigger.select_option(wanted[0]['value'])
  else:
   await trigger.click(timeout=3000)
   found=await page.locator('[role=option],[role=menuitem],[role=menuitemradio],[role=listbox] button').filter(visible=True).evaluate_all(r'''xs=>xs.map((e,i)=>{const c=e.cloneNode(true);c.querySelectorAll('i,svg,[class*=symbol],[class*=material]').forEach(n=>n.remove());const t=c.textContent.normalize('NFKC').replace(/[\u2010-\u2015\u2212·-]/g,' ').replace(/\s+/g,' ').trim();e.setAttribute('data-sf-lite-option',String(i));return {token:String(i),text:t};}).filter(x=>/^Veo\s*3\.1\s+Lite$/i.test(x.text))''')
   if len(found)!=1:return await fail('Menu mô hình chưa có Veo 3.1 Lite duy nhất; không dùng Fast/Quality thay thế.')
   await page.locator('[data-sf-lite-option="'+found[0]['token']+'"]').click(timeout=3000)
  end=time.monotonic()+3
  while time.monotonic()<end:
   rows=await snapshot()
   if rows and len([x for x in rows if lite(x['label'])])==1:break
   await asyncio.sleep(.1)
  else:return await fail('Chưa xác nhận mô hình Veo 3.1 Lite đã được chọn.')
 for name in ('ratio','outputs'):
  await check();rows=await snapshot()
  if rows is None:return await fail('Bảng cài đặt Flow đã đóng hoặc thay đổi.')
  selected,target=selected_group(rows,name)
  if selected is not True:
   if verify_only:return await fail('Cấu hình '+name+' đã thay đổi; chưa điền prompt.')
   if target is None or target['disabled']:return await fail('Chưa tìm được lựa chọn '+name+' duy nhất trong bảng Flow.')
   report['preparation_stage']='set_'+name
   await page.locator('[data-sf-flow-settings=current] [data-sf-flow-setting="'+target['token']+'"]').click(timeout=3000)
   end=time.monotonic()+3
   while time.monotonic()<end:
    rows=await snapshot()
    if rows is not None and selected_group(rows,name)[0]is True:break
    await asyncio.sleep(.1)
   else:return await fail('Chưa xác nhận lựa chọn '+name+' đã được áp dụng; không tự coi là thành công.')
 # Read all fields again; changing the model may reset ratio or output count.
 rows=await snapshot()
 states={name:selected_group(rows or[],name)[0]for name in GROUPS}
 models=[x for x in (rows or[])if re.match(r'^(veo|imagen|nano)\b',x['label'])]
 if not all(x is True for x in states.values())or len(models)!=1 or not lite(models[0]['label']):
  return await fail('Một cài đặt đã thay đổi sau khi chọn mô hình. Chưa điền prompt.')
 await page.keyboard.press('Escape')
 editor,scope=await prompt_composer(page)
 if scope is None:return await fail('Chưa trở lại được ô prompt sau cài đặt.')
 summary=scope.get_by_role('button',name=re.compile(r'^(Settings trigger|Generation settings)$',re.I)).filter(visible=True)
 if await summary.count()!=1:return await fail('Chưa đọc lại được tóm tắt cài đặt.')
 text=await summary.inner_text(timeout=2000)
 report['settings_summary']=text[:200]
 if not re.search(r'\b8\s*s\b',text,re.I)or not re.search(r'\bx\s*1\b',text,re.I):
  return await fail('Tóm tắt Flow chưa xác nhận 8 giây và x1; chưa điền prompt.')
 report['verified_settings']={'mode':'video','references':'ingredients','ratio':'9:16','model':'Veo 3.1 Lite','outputs':1,'duration_seconds':8}
 return True

async def prepare_scene_prompt(page,asset,reference,prompt,check,report):
 from .simple_flow_upload import prepare_uploaded_prompt
 if not await configure_flow_settings(page,check,report):return False
 report['settings_before_attachment']=dict(report['verified_settings'])
 async def verify_before_fill():
  return await configure_flow_settings(page,check,report)
 return await prepare_uploaded_prompt(page,asset,reference,prompt,check,report,mode_verified=True,before_fill=verify_before_fill)
