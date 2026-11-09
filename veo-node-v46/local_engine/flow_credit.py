"""Read displayed Flow balance for the selected verified account; never submit generation."""
import asyncio,math,re,time
from fastapi import HTTPException
LABEL=r'(?:AI\s+credits?|tín\s+dụng\s+AI|điểm\s+tín\s+dụng\s+AI|credits?\s+remaining|số\s+dư\s+tín\s+dụng)'
NUMBER=r'(?:[0-9]{1,3}(?:[,.\u00a0 ][0-9]{3})+|[0-9]+)'
def parse_balance(texts):
 values=set()
 for text in texts:
  if not isinstance(text,str):continue
  lines=[re.sub(r'[ \t]+',' ',s).strip()for s in text.splitlines()if s.strip()]
  for i,line in enumerate(lines):
   choices=[line]
   if i+1<len(lines):choices.append(line+' '+lines[i+1])
   for candidate in choices:
    for pattern in [rf'{LABEL}\s*[:：]?\s*({NUMBER})',rf'({NUMBER})\s*{LABEL}']:
     m=re.fullmatch(pattern,candidate,re.I)
     if m:
      number=int(re.sub(r'[,\.\u00a0 ]','',m[1]))
      if number<=9007199254740991:values.add(number)
 return next(iter(values))if len(values)==1 else None

async def read_page(page):
 async def read():
  nodes=page.locator('header,[role="menu"],[role="dialog"][aria-label*="account" i],[role="dialog"][aria-label*="tài khoản" i]')
  texts=[]
  for node in (await nodes.all())[:160]:
   if await node.is_visible():texts.append(await node.inner_text(timeout=1000))
  return parse_balance(texts)
 value=await read()
 if value is not None:return value
 # Only the account menu; never a create/buy/upgrade control.
 buttons=page.get_by_role('button',name=re.compile(r'^(?:Google Account|Tài khoản Google)(?:[:：\s]|$)',re.I))
 visible=[b for b in await buttons.all()if await b.is_visible()]
 if len(visible)!=1:return None
 await visible[0].click(timeout=3000)
 try:
  for _ in range(8):
   value=await read()
   if value is not None:return value
   await asyncio.sleep(.25)
  return None
 finally:
  try:await page.keyboard.press('Escape')
  except Exception:pass

def install_flow_credit(app,accounts,simple,data):
 def snapshot():
  aid=accounts.pool.status().get('account_id');row=next((r for r in accounts.pool.rows()if r['id']==aid),None)
  if not row:return {'account_id':None,'credit':None,'credit_at':None,'name':None}
  n=row.get('credit');valid=isinstance(n,(int,float))and not isinstance(n,bool)and 0<=n<=9007199254740991 and math.isfinite(n)
  return {'account_id':aid,'name':row.get('name','Flow'),'credit':n if valid else None,'credit_at':row.get('credit_at')if valid else None}
 @app.get('/local-api/flow/credit')
 async def cached():return snapshot()
 @app.post('/local-api/flow/credit/refresh')
 async def refresh():
  async with simple.gate:
   if simple.busy():raise HTTPException(409,'Flow đang xử lý video. Đợi xong rồi cập nhật credit.')
   selected=snapshot();aid=selected['account_id'];bridge=simple.account_bridge
   if not aid or not bridge:raise HTTPException(409,'Chọn tài khoản Flow đã đăng nhập trong Cài đặt → Tài khoản trước.')
   session=None;owned=False
   try:
    current=bridge.binding(aid)
    if not current:raise HTTPException(409,'Tài khoản được chọn chưa có phiên web dùng được.')
    if simple.account_session and simple.pinned_account==aid:
     session=simple.account_session;await bridge.check(session,current)
    else:
     # Prefer an existing native window. Otherwise open an owned background session.
     from .flow_account_session import AccountWebSession
     native=AccountWebSession(data,accounts,background=False)
     try:session,_=await native.attach(aid)
     except Exception:session,_=await bridge.attach(aid)
     owned=True
    await bridge.check(session,current)
    value=await asyncio.wait_for(read_page(session.page),timeout=15)
    await bridge.check(session,current)
    if snapshot()['account_id']!=aid:raise HTTPException(409,'Tài khoản đang chọn đã đổi. Chưa cập nhật số dư.')
    if value is None:return {**snapshot(),'read':False,'message':'Chưa thấy nhãn số dư AI credits trên Flow. Đã giữ số cũ; mở menu tài khoản Flow rồi thử lại.'}
    row=next(r for r in accounts.pool.rows()if r['id']==aid);row.update(credit=value,credit_at=time.time(),credit_source='flow-visible-account-ui');accounts.vault.put('accounts',row)
    return {**snapshot(),'read':True}
   except HTTPException:raise
   except Exception:return {**snapshot(),'read':False,'message':'Chưa đọc được số dư Flow. Kiểm tra phiên tài khoản; số cũ được giữ nguyên.'}
   finally:
    if owned and session:
     try:await session.disconnect()
     except Exception:pass
