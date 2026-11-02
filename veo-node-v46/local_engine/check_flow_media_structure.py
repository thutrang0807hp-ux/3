"""Chromium fixtures for on-demand frame/media structure diagnostics only."""
import asyncio,json
from unittest.mock import AsyncMock,patch
from playwright.async_api import async_playwright
from .flow_media_structure import collect_media_structure
from .flow_tracking_diagnostics import observer_report
from .simple_flow_dom import ResultObserver

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await browser.new_page();await page.route('**/*',lambda route:route.abort())
  await page.set_content('''<script>window.sent=0;window.downloads=0</script>
  <flow-result-tile><img data-media-id="thumbnail-only" width=60 height=90 src="https://example.invalid/photo?token=SENSITIVE"><div><span>00:08</span><button onclick="window.downloads++">Download video</button><button onclick="window.sent++">Generate</button></div></flow-result-tile>''')
  await page.evaluate('''()=>{
   const frames=[
    ['visible','<div data-generation-id="framed-result"><p>Framed prompt</p><video width=80 height=100 src="https://example.invalid/video?token=SENSITIVE"></video><span>61%</span></div>',false],
    ['hidden','<img width=50 height=50 src=hidden>',true],
    ['shadow','<media-host></media-host>',false]
   ];
   for(const [id,html,hidden] of frames){const f=document.createElement('iframe');f.id=id;f.name=id;f.srcdoc=html;f.hidden=hidden;document.body.append(f)}
  }''')
  await page.frame_locator('#visible').locator('video').wait_for(state='visible')
  shadow=page.frame(name='shadow')
  await shadow.wait_for_selector('media-host',state='attached')
  await shadow.evaluate('''()=>{const root=document.querySelector('media-host').attachShadow({mode:'open'});root.innerHTML='<section><p>Shadow result</p><img data-media-id="shadow-image" width=50 height=60 src=shadow><button>Download</button></section>'}''')
  observer=ResultObserver(page,'A long original prompt for diagnostics.')
  # The periodic/light report must not run structural scanning.
  scanner=AsyncMock(side_effect=AssertionError('Unexpected heavy scan'))
  with patch('local_engine.flow_media_structure.collect_media_structure',scanner):
   light=await observer_report(observer)
  scanner.assert_not_awaited();assert light['media_structure'] is None
  full=await observer_report(observer,include_structure=True)
  structure=full['media_structure'];assert full['structure_requested'] and structure['frame_count']==4,structure
  main=next(f for f in structure['frames'] if f['main_frame'])['structure']
  assert any(a['tag']=='flow-result-tile' and any(c['name']=='Download video' for c in a['controls']) for m in main['media'] for a in m['ancestors'])
  assert any(f.get('inspection')=='hidden_frame_metadata_only' for f in structure['frames'])
  framed=next(f['structure'] for f in structure['frames'] if any(m['element']['tag']=='video' for m in f.get('structure',{}).get('media',[])))
  assert framed['media'][0]['element']['tag'] in ('video','span')
  assert any(m['in_shadow_root'] for f in structure['frames'] for m in f.get('structure',{}).get('media',[]))
  assert 'SENSITIVE' not in json.dumps(structure)
  assert await page.evaluate('window.sent')==0 and await page.evaluate('window.downloads')==0
  assert not structure['video_attribution_confirmed']
  # A detached/unreadable frame is reported individually, not a total failure.
  with patch.object(shadow,'evaluate',AsyncMock(side_effect=RuntimeError('fixture frame unavailable'))):
   partial=await collect_media_structure(page,budget=3)
  assert any(f.get('error_type')=='RuntimeError' for f in partial['frames'])
  assert any(f['inspection']=='read' for f in partial['frames'])
  exhausted=await collect_media_structure(page,budget=.000001)
  assert any(f['inspection']=='budget_exhausted' for f in exhausted['frames'])
  await browser.close()
 print('PASS: on-demand only; reads thumbnail ancestors/controls, visible iframe and open shadow root; hidden/unreadable frames and exhausted budget reported; no Generate/download clicks or signed media URLs.')

if __name__=='__main__':asyncio.run(main())
