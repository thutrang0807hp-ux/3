"""Exercise actual account verification against Chromium Flow-page fixtures."""
import asyncio,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'veo-node-v46'))
from local_engine.flow_background_session import BackgroundFlowSession
from local_engine.flow_ui_session import SessionUnavailable
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
  for markup in ['<p>selected@example.com</p>','<script type="application/json">{"oPEP7c":"other@example.com"}</script>','<script type="application/json">{"oPEP7c":"selected@example.com","nested":{"oPEP7c":"other@example.com"}}</script>']:
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
  await browser.close()
 print('PASS live-global and bootstrap identities; absent/wrong/ambiguous accounts and account switching rejected; actual Chromium, no Google calls')
asyncio.run(main())
