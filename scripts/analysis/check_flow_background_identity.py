"""Exercise actual account verification against Chromium Flow-page fixtures."""
import asyncio,sys,tempfile
from unittest.mock import patch,AsyncMock
from types import SimpleNamespace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'veo-node-v46'))
from local_engine.flow_background_session import BackgroundFlowSession
from local_engine.flow_ui_session import SessionUnavailable,FlowUiSession
from playwright.async_api import async_playwright

async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await browser.new_page()
  await page.route('https://flow.google.com/**',lambda r:r.fulfill(body='<html><head></head><body></body></html>',content_type='text/html'))
  await page.goto('https://flow.google.com/')
  s=BackgroundFlowSession(tempfile.mkdtemp(),None,'selected@example.com');s.page=page;s.browser=browser;s.email='selected@example.com'
  async def fixture(markup):
   await page.evaluate('delete window.WIZ_global_data');await page.locator('body').evaluate('(n,html)=>n.innerHTML=html',markup)
  await page.evaluate("window.WIZ_global_data={oPEP7c:'selected@example.com'}")
  assert await s.assert_ready()
  await fixture('<script type="application/json">{"oPEP7c":"SELECTED@example.com"}</script>')
  assert await s.assert_ready()
  await fixture('<p>Flow workspace without email metadata</p>')
  assert await s.assert_ready()
  strict=FlowUiSession(tempfile.mkdtemp());strict.page=page;strict.browser=browser;strict.email=s.email
  try:await strict.assert_ready()
  except SessionUnavailable:pass
  else:raise AssertionError('Legacy strict session changed')
  for markup in ['<script type="application/json">{"oPEP7c":"other@example.com"}</script>','<script type="application/json">{"oPEP7c":"selected@example.com","nested":{"oPEP7c":"other@example.com"}}</script>']:
   await fixture(markup)
   try:await s.assert_ready()
   except SessionUnavailable:pass
   else:raise AssertionError('Unverified/wrong/ambiguous account was accepted')
  await fixture('<script type="application/json">{"oPEP7c":"selected@example.com"}</script>')
  assert await s.assert_ready()
  await page.evaluate("window.WIZ_global_data={oPEP7c:'other@example.com'}")
  try:await s.assert_ready()
  except SessionUnavailable:pass
  else:raise AssertionError('Live account switch ignored')
  # Exercise attach itself with a real intercepted Flow page, not just parser.
  s.profile.mkdir(parents=True,exist_ok=True)
  factory=lambda:SimpleNamespace(start=AsyncMock(return_value=pw))
  with patch('local_engine.flow_background_session.launch_background',AsyncMock(return_value=page.context)):
   await s.attach(factory)
  assert s.email=='selected@example.com'
  assert await s.assert_ready()
  assert not s.require_page_identity
  projects={}
  vault=SimpleNamespace(secret=lambda key:projects.get(key),set_secret=lambda key,value:projects.update({key:value}))
  await page.evaluate("()=>{const button=document.createElement('button');button.textContent='New project';button.onclick=()=>location.href='https://flow.google.com/project/11111111-1111-4111-8111-111111111111';document.body.replaceChildren(button);}")
  await s.ensure_project(vault,'account','room')
  assert page.url.endswith('11111111-1111-4111-8111-111111111111')
  await page.goto('https://flow.google.com/')
  await s.ensure_project(vault,'account','room')
  assert page.url.endswith('11111111-1111-4111-8111-111111111111')
  await browser.close()
 print('PASS actual attach without email metadata; live/global and bootstrap identity, wrong/ambiguous accounts/switches rejected; legacy strict verification preserved; Chromium fixtures, no Google calls')
asyncio.run(main())
