"""Read-only Flow credit parsing and selected-account API checks; no provider calls."""
import asyncio,importlib.util,tempfile,types
from pathlib import Path
from unittest.mock import patch
import httpx
from fastapi import FastAPI
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2];source=Path('local_engine/flow_credit.py');source=source if source.exists()else ROOT/'veo-node-v46/local_engine/flow_credit.py'
spec=importlib.util.spec_from_file_location('credit_test',source);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
async def main():
 assert mod.parse_balance(['AI credits\n1,050'])==1050
 assert mod.parse_balance(['1.050 tín dụng AI'])==1050
 assert mod.parse_balance(['AI credits: 0'])==0
 for text in ['20 credits per video','Create 4 videos','AI credits 1,5','AI credits: -1','Buy 1000 AI credits']:
  assert mod.parse_balance([text])is None,text
 assert mod.parse_balance(['AI credits 100','AI credits 200'])is None
 async with async_playwright()as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page()
  await page.set_content('<button>Create 20 AI credits</button><header>AI credits: 1,050</header>');assert await mod.read_page(page)==1050
  await page.set_content('<button>Create 20 AI credits</button>');assert await mod.read_page(page)is None
  await page.set_content('<button aria-label="Google Account: fixture@example.test" onclick="document.querySelector(\'[role=menu]\').hidden=false">Account</button><div role="menu" hidden>AI credits<br>1,050</div>');assert await mod.read_page(page)==1050
  await page.set_content('<button aria-label="Sign out Google Account" onclick="window.clicked=true">Sign out</button>');assert await mod.read_page(page)is None;assert not await page.evaluate('!!window.clicked')
  await page.set_content('<header>AI credits: 1,050</header>')
  selected={'id':'A'};rows={'A':{'id':'A','name':'A','credit':99,'credit_at':1},'B':{'id':'B','name':'B','credit':10,'credit_at':2}};writes=[]
  class Pool:
   def status(self):return {'account_id':selected['id']}
   def rows(self):return list(rows.values())
  class Vault:
   def put(self,table,row):rows[row['id']]=row;writes.append(row['id'])
  class Session:
   def __init__(self):self.page=page;self.closes=0
   async def disconnect(self):self.closes+=1
  session=Session()
  class Bridge:
   def binding(self,aid):return {'account_id':aid,'email':aid+'@fixture.test'}
   async def check(self,s,binding):assert s is session
  simple=types.SimpleNamespace(gate=asyncio.Lock(),busy=lambda:False,account_bridge=Bridge(),account_session=session,pinned_account='A')
  accounts=types.SimpleNamespace(pool=Pool(),vault=Vault());app=FastAPI();mod.install_flow_credit(app,accounts,simple,Path('/tmp'))
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local')as client:
   assert(await client.get('/local-api/flow/credit')).json()['credit']==99
   result=(await client.post('/local-api/flow/credit/refresh')).json();assert result['read']and result['credit']==1050 and writes==['A'],result
   await page.set_content('<header>No balance available</header>');result=(await client.post('/local-api/flow/credit/refresh')).json();assert not result['read']and result['credit']==1050 and writes==['A']
   await page.set_content('<header>AI credits: 0</header>');assert(await client.post('/local-api/flow/credit/refresh')).json()['credit']==0
   simple.busy=lambda:True;assert(await client.post('/local-api/flow/credit/refresh')).status_code==409;simple.busy=lambda:False
   async def switched(page):selected['id']='B';return 500
   with patch.object(mod,'read_page',switched):assert(await client.post('/local-api/flow/credit/refresh')).status_code==409
   assert rows['B']['credit']==10 and session.closes==0
  await b.close()
 print('PASS visible account-balance parsing, menu read, separators and zero; reject cost/ambiguous labels; selected account only; preserve prior balance on unreadable UI; busy/account-switch guards; reused session not closed. No real Flow account check.')
asyncio.run(main())
