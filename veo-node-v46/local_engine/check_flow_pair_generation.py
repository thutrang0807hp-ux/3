"""Local browser/real ledger tests; never contacts Google or generates paid video."""
import asyncio,base64,hashlib,io,tempfile
from pathlib import Path
from unittest.mock import AsyncMock,patch
from PIL import Image
from playwright.async_api import async_playwright
from fastapi import HTTPException
from .simple_flow import SimpleFlow,SimpleStopped,MODEL
from .request_ledger import RequestLedger
from .vault import Vault
from .flow_pair_generation import seal_pair,validate_pair
from .flow_prepare import PrepareStopped
from .flow_settings import DEFAULTS
from .simple_flow_dom import ResultObserver
from .check_flow_prepare import SETTINGS

async def main():
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);buffer=io.BytesIO();Image.new('RGB',(40,60),'green').save(buffer,format='PNG');raw=buffer.getvalue();encoded=base64.b64encode(raw).decode();image='data:image/png;base64,'+encoded
  prompt='A person waves.\nKeep the same outfit.'
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
   html=SETTINGS+'<form><img width=40 height=60 src="'+image+'"><textarea></textarea><button type=button onclick="window.sent++">Generate</button></form><script>window.sent=0;document.addEventListener("keydown",e=>{if(e.key==="Escape")document.querySelector("#settings").hidden=true})</script>'
   async def intercepted(route):
    if route.request.resource_type=='document':await route.fulfill(body='<html></html>',content_type='text/html')
    else:await route.fulfill(json={'name':'operations/provider-job-fixture','state':'RUNNING'})
   await page.route('**/*',intercepted)
   await page.goto('https://flow.google.com/project/fixture')
   await page.set_content(html);await page.locator('textarea').fill(prompt)
   await page.locator('form button').evaluate("e=>e.onclick=()=>{window.sent++;window.generated=fetch('/v1/video:generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:document.querySelector('textarea').value})}).then(r=>r.json())}")
   service=SimpleFlow(root,Vault(root),RequestLedger(root))
   service.account_bridge=type('Bridge',(),{'background':True,'selection':lambda _:{'available':True,'token':'token','account_id':'account'}})()
   service.page=service.pair_page=page;service.connected=True;service.pair_trial_only=True
   service.assert_ready=AsyncMock();service.disconnect_browser=AsyncMock();service.capture_preview=AsyncMock()
   report={'request_id':'flow-pair-fixture','state':'inputs_sent','account_id':'account','room_id':'room','scene_id':'scene','part':'part',
    'delivered':True,'image_attached':True,'prompt_filled':True,'prompt_verified':True,'settings_verified':True,
    'reference_sha256':hashlib.sha256(raw).hexdigest(),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()}
   service.pair_report=report;await seal_pair(service,report,DEFAULTS)
   assert report['generation_ready']
   payload={'prepared_request_id':report['request_id'],'account_id':'account','room_id':'room','scene_id':'scene','part':'part','prompt':prompt}
   await validate_pair(service,payload,raw)
   for changed in (dict(payload,scene_id='other'),dict(payload,prompt='Changed text')):
    try:await validate_pair(service,changed,raw);raise AssertionError('Changed input accepted')
    except PrepareStopped:pass
   await page.locator('form img').evaluate("e=>e.src='changed-image'")
   try:await validate_pair(service,payload,raw);raise AssertionError('Changed attachment accepted')
   except PrepareStopped:pass
   await page.locator('form img').evaluate('(e,url)=>e.src=url',image)
   # Real ResultObserver must read multiline prompt from a new card.
   observer=ResultObserver(page,prompt);await observer.baseline()
   await page.evaluate('''prompt=>{const card=document.createElement('article');card.setAttribute('data-generation-id','new-result');card.innerHTML='<p></p><span>37%</span>';card.querySelector('p').textContent=prompt;document.body.append(card)}''',prompt)
   row=await observer.read();assert row and row['progress']==37,row
   await page.locator('[data-generation-id=new-result]').evaluate('e=>e.remove()')
   # Provider-ID sender/ledger/download cases now live in check_flow_task_integration.
   await browser.close()
 print('PASS: pair receipt guards image/prompt/scene; ResultObserver reads actual DOM progress independently. Provider-ID sender is tested by check_flow_task_integration.')

if __name__=='__main__':asyncio.run(main())
