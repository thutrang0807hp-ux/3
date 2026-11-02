"""Chromium history-detail fixtures and dedicated same-project inspection guard."""
import asyncio,json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import urlsplit
from playwright.async_api import async_playwright
from .flow_video_history import make_detail_check,read_history_prompt
from .flow_video_detail_probe import inspect_video_details

HTML='''<script>window.expanded=0;window.sent=0;window.downloaded=0;window.reused=0</script>
<flow-grid-tile-container id=grid><flow-video-tile><img class=thumbnail width=60 height=80 src=thumbnail onclick="document.querySelector('#grid').hidden=true;document.querySelector('#history-view').hidden=false;history.pushState({},'', '/project/ABC/edit/asset-id?token=SENSITIVE')"><button onclick="window.reused++">Reuse prompt</button></flow-video-tile></flow-grid-tile-container>
<flow-editor-history-step-video id=history-view hidden><flow-video-tile><img class=thumbnail width=60 height=80 src=thumbnail></flow-video-tile><div><p id=full-prompt>Truncated…</p><button aria-controls=full-prompt onclick="window.expanded++;document.querySelector('#full-prompt').textContent=window.originalPrompt;this.textContent='Collapse prompt'">Expand prompt</button></div><button onclick="window.reused++">Reuse prompt</button><button onclick="window.downloaded++">Download</button><button onclick="window.sent++">Generate</button></flow-editor-history-step-video>'''

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await browser.new_page();await page.route('**/*',lambda r:r.abort());await page.route('https://flow.google.com/**',lambda r:r.fulfill(body=HTML,content_type='text/html'))
  await page.goto('https://flow.google.com/project/ABC')
  prompt='REFERENCE BINDINGS\nSCENE 5. Subject touching toothbrush bristles.'
  await page.evaluate('(text)=>window.originalPrompt=text',prompt)
  selection={'available':True,'account_id':'account'};binding={'account_id':'account','profile_key':'profile'}
  bridge=SimpleNamespace(selection=lambda:selection,check=AsyncMock())
  service=SimpleNamespace(page=page,project='https://flow.google.com/project/ABC',connected=True,account_bridge=bridge,account_session=object(),pinned_binding=binding)
  probe={};detail_check=make_detail_check(service,page=page,project_url=service.project,account_id='account',report=probe)
  async def strict_check():
   # The original generation guard must still reject a detail subroute.
   if urlsplit(page.url).path!='/project/ABC':raise RuntimeError('not the project root')
  report=await inspect_video_details(page,prompt,strict_check,report=probe,detail_check=detail_check)
  assert report['thumbnail_clicked'] and report['history_found'] and report['full_prompt_match'],report
  assert report['expand_prompt_clicked'] and await page.evaluate('window.expanded')==1
  assert report['detail_route']['path_shape']=='/project/[id]/edit/[id]'
  assert 'SENSITIVE' not in json.dumps(report) and not report['request_attribution_confirmed']
  assert await page.evaluate('window.sent+window.downloaded+window.reused')==0
  try:await strict_check();raise AssertionError('Sender guard weakened')
  except RuntimeError:pass
  # Multiple history steps must not be resolved by choosing the first.
  await page.locator('#history-view').evaluate('e=>e.after(e.cloneNode(true))')
  multiple=await read_history_prompt(page,prompt,detail_check,timeout=.1)
  assert not multiple['history_found'] and not multiple['expand_prompt_clicked']
  await page.locator('flow-editor-history-step-video').last.evaluate('e=>e.remove()')
  # Whole-step text containing the expected prompt cannot confirm it by itself.
  await page.locator('#history-view').evaluate('(e,text)=>{e.querySelector("div").remove();const p=document.createElement("p");p.textContent=text;e.append(p)}',prompt)
  unlabelled=await read_history_prompt(page,prompt,detail_check,timeout=.1)
  assert unlabelled['history_found'] and not unlabelled['full_prompt_match']
  # A different project, or changed selection, remains rejected.
  await page.evaluate("history.pushState({},'', '/project/ABCD/edit/asset-id')")
  try:await detail_check();raise AssertionError('Different project accepted')
  except RuntimeError:pass
  await page.evaluate("history.pushState({},'', '/project/ABC/edit/asset-id')")
  selection['account_id']='other'
  try:await detail_check();raise AssertionError('Different account accepted')
  except RuntimeError:pass
  await browser.close()
 print('PASS: known history component/Expand prompt, child route in same project permitted only for inspection, full prompt field required, multiple steps/changed project/account rejected; no Generate/Reuse/Download.')

if __name__=='__main__':asyncio.run(main())
