"""Original Node runtime, real headless Chrome/CDP, production queue; Gemini is a fixture."""
import asyncio,base64,io,json,os,shutil,sys,tempfile,threading,uuid,zipfile
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
  root=Path(tmp);pkg=root/'pkg';(pkg/'local_engine').mkdir(parents=True);(pkg/'vendor').mkdir()
  with zipfile.ZipFile(ROOT/'downloads/v46/SceneForge-Veo-v46-Source.zip')as z:
   for n in z.namelist():
    if n.startswith('local_engine/')and n.endswith('.py')and '/'not in n[13:]: (pkg/n).write_bytes(z.read(n))
  for p in (ROOT/'veo-node-v46/local_engine').glob('*.py'):shutil.copy(p,pkg/'local_engine'/p.name)
  for suffix in ['zip','json']:shutil.copy(ROOT/('veo-node-v46/vendor/gemini-native-node.'+suffix),pkg/'vendor')
  sys.path.insert(0,str(pkg))
  from local_engine.gemini_chat import install_gemini_chat
  from local_engine.request_ledger import RequestLedger
  from local_engine.browser_profiles import profiles
  data=root/'data';data.mkdir();(data/'ledger').mkdir();v=Vault();s=install_gemini_chat(FastAPI(),v,data,RequestLedger(data/'ledger'));m=profiles(v,data)
  aid='gchat-account-node';v.put('accounts',{'id':aid,'service':'gemini_chat','name':'Native Node fixture','transport':'native','enabled':True,'active':True,'session_verified':True,'state':'ready','models':[]})
  chrome=root/'test-chrome';chrome.write_text('#!/bin/sh\nexec /usr/bin/chromium --no-sandbox "$@"\n');chrome.chmod(0o755)
  e=m.reserve('gemini_chat',aid);m.settings(e,executable=str(chrome));m.bind(e,aid);s.select({'account_id':aid,'mode':'selected'})
  async def forbidden(*args):raise AssertionError('SDK/extension should not run')
  s.runner=forbidden
  images={}
  for name,color in [('A','blue'),('B','red'),('FAIL','green'),('AFTER','yellow')]:
   b=io.BytesIO();Image.new('RGB',(360,640),color).save(b,'PNG');images[name]=b.getvalue()
  encoded={k:base64.b64encode(b).decode()for k,b in images.items()};sent=[];fail_page=False
  fixture='''<meta charset="UTF-8"><rich-textarea><div contenteditable="true" role="textbox">STALE UNSENT DRAFT</div></rich-textarea><input type="file" multiple><button class="send-button" aria-label="Send message">Send</button><button aria-label="Tools" id="tools">Tools</button><div role="menu" id="tools-menu" hidden><button role="menuitem" aria-label="Create images">Create images</button></div><script>
document.querySelector('#tools').onclick=()=>{document.querySelector('#tools-menu').hidden=false};document.querySelector('#tools-menu button').onclick=()=>{window.imageMode=true;document.querySelector('#tools-menu').hidden=true};const images=IMAGES;const actualFetch=window.fetch.bind(window),actualCanvas=HTMLCanvasElement.prototype.toDataURL;
window.fetch=(u,...args)=>{if(window.blockDownload&&String(u).startsWith('data:image'))throw Error('fixture download blocked');return actualFetch(u,...args)};
HTMLCanvasElement.prototype.toDataURL=function(...args){if(window.blockDownload)throw Error('fixture pixel read blocked');return actualCanvas.apply(this,args)};
document.querySelector('input').onchange=e=>{for(const f of e.target.files){const n=document.createElement('uploader-file-preview');n.setAttribute('data-upload-preview','1');const i=new Image();i.src=URL.createObjectURL(f);n.append(i);document.body.append(n);}};
document.querySelector('button').onclick=async event=>{if(!event.isTrusted){window.untrustedClick=true;return;}const prompt=document.querySelector('[contenteditable]').innerText;window.turnName=prompt.match(/TURN:(TEXTONLY|BLOCKED|AFTER|FAIL|A|B)/)[1];window.blockDownload=window.turnName==='FAIL';if(window.turnName==='BLOCKED')return;await actualFetch('/fixture-record',{method:'POST',body:JSON.stringify({name:turnName,prompt,imageMode:window.imageMode===true,old178Previews:document.querySelectorAll('user-query img, .input-area-container img, .file-preview img, .attachment-preview img, .attachment img, .preview-container img').length,knownPreviews:document.querySelectorAll('uploader-file-preview').length,files:await Promise.all([...document.querySelector('input').files].map(async f=>({name:f.name,bytes:[...new Uint8Array(await f.arrayBuffer())]})))})});const thinking=document.createElement('model-response');thinking.textContent='Thinking';document.body.append(thinking);setTimeout(()=>{const n=document.createElement('model-response');if(turnName==='TEXTONLY'){n.innerHTML='<message-content>Công cụ tạo ảnh không khả dụng. Tôi không thể trực tiếp tạo hoặc xuất tệp hình ảnh.</message-content>';document.body.append(n);return;}n.innerHTML='<generated-image><img src="data:image/png;base64,'+images[turnName]+'"></generated-image>';document.body.append(n);},500);};</script>'''.replace('IMAGES',json.dumps(encoded))
  row=await s.native.context(aid)
  async with async_playwright()as pw:
   inspector=await pw.chromium.connect_over_cdp('http://127.0.0.1:'+str(row['port']));ctx=inspector.contexts[0]
   async def route(r):
    if r.request.url.endswith('/fixture-record'):sent.append(json.loads(r.request.post_data));await r.fulfill(body='{}',content_type='application/json')
    elif r.request.url.startswith('https://gemini.google.com/'):
     if fail_page:await r.abort('timedout')
     else:await r.fulfill(body=fixture,content_type='text/html')
    else:await r.abort()
   await ctx.route('**/*',route);await ctx.add_cookies([{'name':'__Secure-1PSID','value':'fixture','domain':'.google.com','path':'/','secure':True}]);await s.native.verify(aid)
   aid2='gchat-account-node-second';v.put('accounts',{'id':aid2,'service':'gemini_chat','name':'Second Node fixture','transport':'native','enabled':True,'active':False,'session_verified':True,'state':'ready','models':[]})
   e2=m.reserve('gemini_chat',aid2);m.settings(e2,executable=str(chrome));m.bind(e2,aid2)
   row2=await s.native.context(aid2);inspector2=await pw.chromium.connect_over_cdp('http://127.0.0.1:'+str(row2['port']));ctx2=inspector2.contexts[0]
   await ctx2.route('**/*',route);await ctx2.add_cookies([{'name':'__Secure-1PSID','value':'fixture2','domain':'.google.com','path':'/','secure':True}]);await s.native.verify(aid2)
   s.select({'mode':'balanced','account_id':aid})
   async def submit(name):
    rid='gchat-'+str(uuid.uuid4());await s.submit({'request_id':rid,'kind':'image','role':'image','image_engine':'studio-v1','ratio':'9:16','prompt':'# UNIVERSAL REFERENCE IMAGE EDIT V6.0\nTURN:'+name+'\n'+('detail ' *3300),'references':[{'mime_type':'image/png','data':encoded['A']},{'mime_type':'image/png','data':encoded['B']}],'room_id':'room','scene_id':name,'confirm_send':True,'selection_token':s.selection()['token']});return rid
   async def wait(rid):
    for _ in range(900):
     result=s.lookup(rid)
     if result['state']in ('done','failed','unknown')and (rid not in s.tasks or s.tasks[rid].done()):return result
     await asyncio.sleep(.1)
    raise AssertionError('production task did not finish')
   try:
    ordinary=await pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True)
    a,b=await asyncio.gather(submit('A'),submit('B'));await ordinary.close()
    for rid,name in [(a,'A'),(b,'B')]:
     result=await wait(rid);assert result['state']=='done',result;assert (s.root/result['result']['file']).read_bytes()==images[name]
    assert sorted(r['name']for r in sent)==['A','B'];assert s.lookup(a)['result']['account_id']!=s.lookup(b)['result']['account_id'];s.select({'mode':'selected','account_id':aid});assert all(len(r['prompt'])>20000 and len(r['files'])==2 and r['imageMode']and 'STALE UNSENT DRAFT'not in r['prompt'] for r in sent);assert all(r['old178Previews']==0 and r['knownPreviews']==2 for r in sent)
    assert all(bytes(r['files'][0]['bytes'])==images['A']and bytes(r['files'][1]['bytes'])==images['B']for r in sent)
    q1,q2=await asyncio.gather(submit('A'),submit('B'))
    for rid,name in [(q1,'A'),(q2,'B')]:
     result=await wait(rid);assert result['state']=='done'and result['result']['account_id']==aid,result;assert (s.root/result['result']['file']).read_bytes()==images[name]
    bad=await submit('FAIL');result=await wait(bad);assert result['state']=='unknown',result
    after=await submit('AFTER');result=await wait(after);assert result['state']=='done',result;assert (s.root/result['result']['file']).read_bytes()==images['AFTER']
    count=len(sent)
    try:await s.receive_image(bad);raise AssertionError('Receive should not resubmit a failed upstream turn')
    except Exception as exc:
     from fastapi import HTTPException
     assert isinstance(exc,HTTPException)and exc.status_code==409,exc
    assert len(sent)==count
    s.native.paths(bad)[1].write_bytes(images['FAIL'])  # Simulate completed file awaiting a failed import.
    receiving=await s.receive_image(bad);assert receiving['state']=='downloading'
    result=await wait(bad);assert result['state']=='done'and len(sent)==count,result
    assert (s.root/result['result']['file']).read_bytes()==images['FAIL']
    only=await submit('TEXTONLY');result=await wait(only);assert result['state']=='unknown'and 'công cụ tạo ảnh không khả dụng'in result['message'],result
    count=len(sent);blocked=await submit('BLOCKED');result=await wait(blocked);assert result['state']=='unknown'and 'Chưa xác nhận Gemini nhận lượt mới'in result['message'],result;assert len(sent)==count
    fail_page=True;before=len(sent);opening=await submit('GOTOFAIL');result=await wait(opening)
    assert result['state']=='unknown'and result['native_trace']['stage']=='open_gemini',result
    assert '[open_gemini]'in result['message']and len(sent)==before,result
    assert not list(s.native.receipts.glob('*.image')),'successful image caches should be retired'
    print('PASS original Node/CDP: ordinary browser closed, parallel separate-account A/B exact images, >20k prompt+2 exact refs, failed download retained, next job succeeds, failed turn follows upstream cleanup, no automatic retry, no extension/SDK, successful caches retired')
   finally:await inspector.close();await inspector2.close();await s.close()
asyncio.run(main())
