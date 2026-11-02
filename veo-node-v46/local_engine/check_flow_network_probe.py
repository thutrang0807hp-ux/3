"""Intercepted Chromium traffic only: no Google calls and no paid generation."""
import asyncio,json
from playwright.async_api import async_playwright
from unittest.mock import AsyncMock
from .flow_network_probe import FlowNetworkProbe,candidate_facts,json_document,MAX_BODY

async def until(predicate,timeout=3):
 end=asyncio.get_running_loop().time()+timeout
 while asyncio.get_running_loop().time()<end:
  if predicate():return
  await asyncio.sleep(.01)
 raise AssertionError('Capture condition timed out')

async def main():
 secret='PRIVATE_CREDENTIAL_MARKER';prompt='A person waves naturally.'
 schema=candidate_facts({'name':'operations/op-new','error':{'code':7,'message':secret},'access_token':secret,'mediaUrl':'https://example.invalid/?token='+secret},prompt)
 assert any(f['value']=='operations/op-new' for f in schema['facts'])
 assert any(f['kind']=='error_code' and f['value']==7 for f in schema['facts'])
 assert secret not in json.dumps(schema)
 assert json_document(")]}'\n{\"done\":true}")=={'done':True}
 try:json_document(b'x'*(MAX_BODY+1));raise AssertionError('Oversized JSON accepted')
 except ValueError:pass
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await browser.new_page()
  baseline_release=asyncio.Event();generate_release=asyncio.Event()
  async def route(request_route):
   request=request_route.request;url=request.url
   if '/project/' in url:
    await request_route.fulfill(content_type='text/html',body='''<script>window.sent=0</script><button onclick="window.sent++;window.result=fetch('/v1/video:generate?token=PRIVATE_CREDENTIAL_MARKER',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer PRIVATE_CREDENTIAL_MARKER'},body:JSON.stringify({prompt:window.originalPrompt,accessToken:'PRIVATE_CREDENTIAL_MARKER'})}).then(r=>r.json())">Generate</button>''');return
   if '/media:status' in url:
    await baseline_release.wait();await request_route.fulfill(json={'operationId':'old-before-click','state':'RUNNING'});return
   if '/video:generate' in url:
    await generate_release.wait();await request_route.fulfill(json={'operations':[{'name':'operations/op-new','mediaId':'media-new','metadata':{'state':'RUNNING'}}],'accessToken':secret,'mediaUrl':'https://example.invalid/video?token='+secret});return
   if '/operations/' in url:
    await request_route.fulfill(status=503,json={'operationId':'op-new','error':{'code':7,'status':'RESOURCE_EXHAUSTED','message':secret}});return
   await request_route.fulfill(json={'operationId':'unfamiliar-endpoint-id','done':False})
  await page.route('**/*',route)
  await page.goto('https://flow.google.com/project/fixture');await page.evaluate('(text)=>window.originalPrompt=text',prompt)
  probe=FlowNetworkProbe(page,'flow-network-fixture',prompt,AsyncMock(),initial_response_timeout=.05)
  await probe.start()
  before=asyncio.create_task(page.evaluate("fetch('/v1/media:status').then(r=>r.json())"))
  await until(lambda:len(probe.report['requests'])==1);await asyncio.sleep(.02)
  await probe.mark_generate_attempt()
  await page.get_by_role('button',name='Generate').click();probe.mark_click_returned()
  baseline_release.set();await before
  await asyncio.sleep(.08)
  assert probe.report['initial_response_wait']=='warning_no_candidate_response',probe.snapshot()
  assert probe.report['candidate_response_count_after_generate_attempt']==0
  generate_release.set();await page.evaluate('window.result')
  await until(lambda:any(e.get('response_facts') for e in probe.report['requests'] if e['method']=='POST'))
  await page.evaluate("fetch('/v1/operations/op-new').then(r=>r.json())")
  await page.evaluate("fetch('/v1/unfamiliar').then(r=>r.json())")
  await until(lambda:any(e.get('http_status')==503 and e.get('response_facts') for e in probe.report['requests']))
  result=await probe.stop()
  assert result['initial_response_wait']=='late_candidate_seen' and result['http_error_response_count']==1
  baseline=next(e for e in result['requests'] if not e['request_after_generate_attempt'])
  assert baseline['request_ms_from_generate']<=0 and baseline['response_ms_from_generate']>=0 and not baseline.get('candidate_response')
  created=next(e for e in result['requests'] if e['method']=='POST')
  assert created['request_facts']['exact_prompt_paths']==['$.prompt']
  assert any(f['value']=='operations/op-new' for f in created['response_facts']['facts'])
  assert any(e['priority']=='background' for e in result['requests'])
  assert any(f['kind']=='error_code' for e in result['requests'] for f in (e.get('response_facts') or {}).get('facts',[]))
  assert secret not in json.dumps(result) and prompt not in json.dumps(result)
  assert not result['association_confirmed'] and not result['generation_submitted_by_probe']
  assert await page.evaluate('window.sent')==1
  count=len(result['requests']);await page.evaluate("fetch('/v1/operations/after-stop').then(r=>r.json())")
  assert len(probe.snapshot()['requests'])==count
  # Export limit remains explicit; metadata and HTTP status still survive.
  limited=FlowNetworkProbe(page,'flow-network-limited',prompt,AsyncMock(),max_fact_bytes=1)
  await limited.start();await limited.mark_generate_attempt()
  await page.evaluate("fetch('/v1/operations/limited').then(r=>r.json())")
  await until(lambda:'fact_export_byte_limit' in limited.report['warnings'])
  final=await limited.stop();assert any(e.get('http_status')==503 for e in final['requests'])
  await browser.close()
 print('PASS: browser Request/Response pairing, pre-click request with late response, relative timestamps, 15s-warning logic with late candidate, 503 JSON retained, unknown endpoint sampled, secrets/prompt stripped, bounded export, listeners removed; only fixture button clicked once.')

if __name__=='__main__':asyncio.run(main())
