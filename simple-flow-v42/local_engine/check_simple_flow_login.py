"""Login state ordering with mocked browser process; no Google/browser operations."""
import asyncio,tempfile,types,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,Mock,patch
from .simple_flow import SimpleFlow
from .vault import Vault
from .request_ledger import RequestLedger
async def wait(s,kind):
 for _ in range(100):
  if s.pending and s.pending['kind']==kind:return s.pending['id']
  await asyncio.sleep(.01)
 raise AssertionError(s.status())
async def main():
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);s=SimpleFlow(root,Vault(root),RequestLedger(root))
  process=Mock();process.poll.return_value=0
  page=SimpleNamespace(url='https://flow.google.com/project/fixture',goto=AsyncMock(),evaluate=AsyncMock(return_value='fixture@invalid'),is_closed=lambda:False)
  ctx=SimpleNamespace(pages=[page],close=AsyncMock())
  pw=SimpleNamespace(chromium=SimpleNamespace(launch_persistent_context=AsyncMock(return_value=ctx)),stop=AsyncMock())
  start=AsyncMock(return_value=pw);module=types.ModuleType('playwright.async_api');module.async_playwright=lambda:SimpleNamespace(start=start)
  with patch.dict(sys.modules,{'playwright.async_api':module}),patch.object(s,'find_browser',return_value=Path('/installed/edge')),patch('subprocess.Popen',return_value=process)as launch:
   await s.connect({'browser':'msedge'});step=await wait(s,'login')
   start.assert_not_awaited();args=launch.call_args.args[0];assert not any('debugging' in a or 'AutomationControlled'in a for a in args)
   assert '--disable-background-mode'in args
   await s.respond({'id':step,'accept':True});step=await wait(s,'project');start.assert_awaited_once()
   profile=pw.chromium.launch_persistent_context.call_args.args[0]
   assert str(root/'browser-profiles'/'simple-flow'/'msedge')==profile
   await s.respond({'id':step,'accept':True});await s.task
   assert s.status()['selection']['available']and s.email=='fixture@invalid'
   await s.close();ctx.close.assert_awaited_once();pw.stop.assert_awaited_once()
 print('PASS login ordering: explicit browser/profile, no automation client before first confirmation, ready only after project confirmation; cleanup. Mocks only; not Google sign-in verification.')
if __name__=='__main__':asyncio.run(main())
