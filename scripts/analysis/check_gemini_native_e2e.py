"""Real native headless transport + production submit/ledger. Gemini/auth are fixtures."""
import asyncio,base64,io,shutil,sys,tempfile,threading,uuid,zipfile
from pathlib import Path
from fastapi import FastAPI
from PIL import Image
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
class Vault:
 def __init__(self):self.lock=threading.RLock();self.tables={};self.secrets={}
 def secret(self,k):return self.secrets.get(k)
 def set_secret(self,k,v):self.secrets[k]=v
 def rows(self,t):return [dict(v)for v in self.tables.get(t,{}).values()]
 def put(self,t,r):self.tables.setdefault(t,{})[r['id']]=dict(r)
 def delete_secret(self,k):self.secrets.pop(k,None)
async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);pkg=root/'pkg';(pkg/'local_engine').mkdir(parents=True)
  with zipfile.ZipFile(ROOT/'downloads/v46/SceneForge-Veo-v46-Source.zip')as z:
   for n in z.namelist():
    if n.startswith('local_engine/')and n.endswith('.py')and '/'not in n[13:]: (pkg/n).write_bytes(z.read(n))
  for p in (ROOT/'veo-node-v46/local_engine').glob('*.py'):shutil.copy(p,pkg/'local_engine'/p.name)
  sys.path.insert(0,str(pkg))
  from local_engine.gemini_chat import install_gemini_chat
  from local_engine.request_ledger import RequestLedger
  from local_engine.browser_profiles import profiles
  data=root/'data';data.mkdir();(data/'ledger').mkdir();v=Vault();s=install_gemini_chat(FastAPI(),v,data,RequestLedger(data/'ledger'))
  aid='gchat-account-native';v.put('accounts',{'id':aid,'service':'gemini_chat','name':'Native fixture','transport':'native','enabled':True,'active':True,'session_verified':True,'state':'ready','models':[]})
  m=profiles(v,data);e=m.reserve('gemini_chat',aid);m.settings(e,executable='/usr/bin/chromium');m.bind(e,aid);s.select({'account_id':aid,'mode':'selected'})
  async def forbidden(*args):raise AssertionError('SDK/extension should not be used')
  s.runner=forbidden
  b=io.BytesIO();Image.new('RGB',(360,640),'#336699').save(b,'PNG');png=b.getvalue();encoded=base64.b64encode(png).decode();sent=[]
  fixture='''<rich-textarea><div contenteditable="true" role="textbox"></div></rich-textarea><input type="file" multiple><button class="send-button" aria-label="Send message">Send</button><script>document.querySelector('input').onchange=e=>{for(const f of e.target.files){const n=document.createElement('div');n.className='file-preview';const i=new Image();i.src=URL.createObjectURL(f);n.append(i);document.body.append(n);}};document.querySelector('button').onclick=async()=>{await window.recordSend({prompt:document.querySelector('[contenteditable]').innerText,files:await Promise.all([...document.querySelector('input').files].map(async f=>({name:f.name,bytes:[...new Uint8Array(await f.arrayBuffer())]})))});setTimeout(()=>{const n=document.createElement('model-response');n.innerHTML='<generated-image><img src="data:image/png;base64,IMAGE"></generated-image>';document.body.append(n);},600);};</script>'''.replace('IMAGE',encoded)
  ctx=await s.native.context(aid)
  async def route(r):
   if r.request.url.startswith('https://gemini.google.com/'):await r.fulfill(body=fixture,content_type='text/html')
   else:await r.abort()
  await ctx.route('**/*',route);await ctx.expose_function('recordSend',lambda value:sent.append(value));await ctx.add_cookies([{'name':'__Secure-1PSID','value':'fixture','domain':'.google.com','path':'/','secure':True}]);await s.native.verify(aid)
  async def submit():
   rid='gchat-'+str(uuid.uuid4());await s.submit({'request_id':rid,'kind':'image','role':'image','image_engine':'studio-v1','ratio':'9:16','prompt':'# UNIVERSAL REFERENCE IMAGE EDIT V6.0\n'+('detailed scene ' *1800),'references':[{'mime_type':'image/png','data':encoded}for _ in range(3)],'room_id':'room','scene_id':'scene','confirm_send':True,'selection_token':s.selection()['token']});return rid
  try:
   # An unrelated Chrome session can close while the app-owned headless job continues.
   async with async_playwright()as pw:
    ordinary=await pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True)
    rid=await submit();await ordinary.close()
    for _ in range(300):
     if s.lookup(rid)['state']in ('done','failed','unknown'):break
     await asyncio.sleep(.05)
    record=s.lookup(rid);assert record['state']=='done',record
   assert len(sent)==1 and len(sent[0]['files'])==3 and len(sent[0]['prompt'])>20000
   assert all(bytes(f['bytes'])==png for f in sent[0]['files']);assert (s.root/record['result']['file']).read_bytes()==png
   # A failed download is received again without a second prompt.
   save=s.native.save
   async def fail_once(*args):raise OSError('fixture download failure')
   s.native.save=fail_once;rid2=await submit()
   for _ in range(300):
    if s.lookup(rid2)['state']in ('done','failed','unknown'):break
    await asyncio.sleep(.05)
   assert s.lookup(rid2)['state']=='unknown';assert len(sent)==2
   s.native.save=save;await s.receive_image(rid2)
   for _ in range(300):
    if s.lookup(rid2)['state']=='done':break
    await asyncio.sleep(.05)
   assert s.lookup(rid2)['state']=='done',s.lookup(rid2);assert len(sent)==2,'receive must not resend prompt'
   # Native sign-in handoff verifies the saved profile, never imports cookies through SDK.
   class Login:
    closed=False
    def __init__(self,lease):self.process=self;self.exited=False;self.lease=lease
    def poll(self):return 0 if self.exited else None
    async def finish_signin(self):self.exited=True
    async def close(self):
     if not self.closed:self.closed=True;self.lease.release()
    async def stop(self):await self.close()
   async def login_factory(entry,url,cookies=None):
    lease=m.lease(entry);await lease.acquire();return Login(lease)
   m.native=login_factory
   verify=s.native.verify
   async def verify_handoff(ident):
    assert ident in m.registry();assert not m.lease(m.registry()[ident]).locked()
   s.native.verify=verify_handoff
   pending=await s.login({'name':'Native login fixture'})
   logged=await s.finish_login({'id':pending['id']})
   assert logged['account']['transport']=='native' and logged['account']['session_verified']
   assert s.selection()['account_id']==logged['id']
   s.native.verify=verify
   await s.native.close_account(aid)
   ctx2=await s.native.context(aid);await ctx2.route('**/*',route)
   await s.native.verify(aid)  # Saved Google cookie survives headless restart.
   print('PASS native persistent headless Chrome survives closing unrelated browser, authenticated verify, 25k prompt + 3 exact attachments, production ledger commits correct result, receive-only retries without extension/SDK or duplicate send')
  finally:await s.close()
asyncio.run(main())
