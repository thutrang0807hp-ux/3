"""Real Chromium session survival and conservative profile-cache cleanup."""
import asyncio,hashlib,importlib.util,sys,tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi import FastAPI,HTTPException
import httpx
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
source=Path('local_engine/profile_cache.py');source=source if source.exists()else ROOT/'veo-node-v46/local_engine/profile_cache.py'
spec=importlib.util.spec_from_file_location('profile_cache_test',source);pc=importlib.util.module_from_spec(spec);spec.loader.exec_module(pc)
async def main():
 with tempfile.TemporaryDirectory(prefix='sf-profile-cache-')as td:
  data=Path(td)/'data';root=data/'browser-profiles/flow-accounts'/('a'*24);root.mkdir(parents=True)
  async with async_playwright()as p:
   async def launch():
    ctx=await p.chromium.launch_persistent_context(str(root),executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox',*pc.CACHE_ARGS]);await ctx.route('**/*',lambda r:r.fulfill(body='<h1>Session fixture</h1>',content_type='text/html'));return ctx
   ctx=await launch();await ctx.add_cookies([{'name':'session-sentinel','value':'keep-me','url':'https://fixture.test','expires':2000000000}]);page=await ctx.new_page();await page.goto('https://fixture.test');await page.evaluate("localStorage.setItem('session','keep-local');new Promise((ok,no)=>{let r=indexedDB.open('keep',1);r.onupgradeneeded=()=>r.result.createObjectStore('session');r.onsuccess=()=>{let db=r.result,tx=db.transaction('session','readwrite');tx.objectStore('session').put('keep-idb','key');tx.oncomplete=()=>{db.close();ok()}};r.onerror=no})")
   # Live profile is excluded even if the API's in-process busy callback is false.
   plan,_=pc.scan(data);assert plan['profiles'][0]['busy']and plan['bytes']==0,plan
   await ctx.close()
   for rel in ['Default/Cache/Cache_Data/junk','Default/Code Cache/js/junk','ShaderCache/junk']:
    f=root/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'x'*4096)
   for rel in ['sceneforge-fingerprint.json','Default/Service Worker/CacheStorage/auth-data','Default/Session Storage/session','Default/Preferences']:
    f=root/rel;f.parent.mkdir(parents=True,exist_ok=True)
    if not f.exists():f.write_bytes(b'keep-auth')
   outside=Path(td)/'outside';outside.mkdir();(outside/'keep').write_text('outside')
   (root/'Profile 2').mkdir();(root/'Profile 2/Cache').symlink_to(outside,target_is_directory=True)
   ignored=data/'browser-profiles/unowned/Default/Cache';ignored.mkdir(parents=True);(ignored/'keep').write_text('unowned')
   def retained():return {str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest()for f in root.rglob('*')if f.is_file()and not any(n in pc.CACHE_DIRS for n in f.relative_to(root).parts)and not f.is_symlink()}
   before=retained();plan,_=pc.scan(data);assert plan['complete']and plan['bytes']>=12288,plan
   with patch.object(pc,'browser_commands',return_value=None):assert pc.clean(data)['files']==0
   assert pc.clean(data,busy=True)['files']==0
   # A modified plan never deletes a new/changed cache file.
   (root/'ShaderCache/junk').write_bytes(b'changed')
   try:pc.clean(data,token=plan['token']);raise AssertionError('stale token accepted')
   except HTTPException as e:assert e.status_code==409
   class Vault:
    def rows(self,name):return []
   app=FastAPI();pc.install_profile_cache(app,Vault(),data,lambda aid:False)
   async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local')as client:
    assert(await client.post('/local-api/accounts/profile-cache',json={})).status_code==400
    plan=(await client.get('/local-api/accounts/profile-cache')).json();r=await client.post('/local-api/accounts/profile-cache',json={'token':plan['token']});assert r.status_code==200,r.text;assert r.json()['bytes']>0
   assert retained()==before;assert(outside/'keep').read_text()=='outside';assert(ignored/'keep').read_text()=='unowned'
   ctx=await launch();assert any(c['name']=='session-sentinel'and c['value']=='keep-me'for c in await ctx.cookies())
   page=await ctx.new_page();await page.goto('https://fixture.test');assert await page.evaluate("localStorage.getItem('session')")=='keep-local'
   assert await page.evaluate("new Promise((ok,no)=>{let r=indexedDB.open('keep',1);r.onsuccess=()=>{let db=r.result,q=db.transaction('session').objectStore('session').get('key');q.onsuccess=()=>{db.close();ok(q.result)}};r.onerror=no})")=='keep-idb'
   await ctx.close()
 print('PASS real Chromium cookie/localStorage/IndexedDB survive cleanup; fingerprint and non-cache files byte-identical; active/unknown profiles skipped; stale token rejected; symlink/unowned paths untouched; API cleanup verified. No real provider login or Windows run.')
asyncio.run(main())
