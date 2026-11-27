"""CLI restore must not invoke the legacy RPC bootstrap before original CLI."""
import asyncio,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
from .simple_flow import SimpleFlow
from .request_ledger import RequestLedger
async def main():
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);vault=SimpleNamespace(secret=lambda key:None,set_secret=lambda *args:None)
  service=SimpleFlow(root,vault,RequestLedger(root))
  session=SimpleNamespace(background=True,email='selected@example.com',page=SimpleNamespace(context=object(),url='https://flow.google.com/project/11111111-1111-4111-8111-111111111111'),ensure_project=AsyncMock())
  service.account_bridge=SimpleNamespace(attach=AsyncMock(return_value=(session,{'account_id':'account'})),check=AsyncMock())
  service.pinned_account='account';service.pinned_room='room';service.native_pipeline_enabled=True;service.cli_driver_enabled=True
  with patch('local_engine.flow_native_pipeline.ensure_native_project',AsyncMock(side_effect=AssertionError('Legacy RPC called'))) as legacy:
   await service.restore()
   legacy.assert_not_called();session.ensure_project.assert_awaited_once_with(vault,'account','room')
  assert service.connected and service.project.endswith('111111111111')
 print('PASS actual CLI restore selects UI project preparation, never legacy RPC bootstrap')
if __name__=='__main__':asyncio.run(main())
