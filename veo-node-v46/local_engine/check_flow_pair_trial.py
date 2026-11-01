"""Orchestration regressions; these do not establish live Flow compatibility."""
import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from . import flow_pair_trial as m

class PairTrialTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, *, upload_error=False, settings_error=False, attach_error=False):
        events=[]
        async def upload(*args):
            events.append('upload')
            if upload_error: await asyncio.sleep(1)
            return True
        async def write(*args, **kwargs):
            events.append('prompt')
            return 'verified-digest'
        async def trace(*args, **kwargs):
            events.append('trace')
            if attach_error: await asyncio.sleep(1)
            return 'known-id'
        settings=AsyncMock(side_effect=RuntimeError('settings unavailable')) if settings_error else AsyncMock(return_value=True)
        page=SimpleNamespace(keyboard=SimpleNamespace(press=AsyncMock()))
        with tempfile.TemporaryDirectory() as folder:
            image=Path(folder)/'flow-pair-0123456789abcdef01234567.png'
            image.write_bytes(b'fixture')
            with patch.object(m,'apply_settings',settings), patch.object(m,'upload_to_project',upload), patch.object(m,'write_prompt',write), patch.object(m,'library_snapshot',AsyncMock(return_value={})), patch.object(m,'trace_uploaded_media',trace), patch.object(m,'attach_traced_media',AsyncMock(return_value={'count':1,'ids':['known-id']})):
                report=await m.upload_and_fill_prompt(page,image,'text',upload_timeout=.02,attachment_timeout=.02)
        return report,events

    async def test_prompt_precedes_attachment_and_is_read_back(self):
        report,events=await self.exercise()
        self.assertEqual(events,['upload','prompt','trace','prompt'])
        self.assertTrue(report['image_attached'])
        self.assertTrue(report['prompt_verified'])
        self.assertFalse(report['generation_submitted'])

    async def test_upload_timeout_still_fills_prompt_once_without_retry(self):
        report,events=await self.exercise(upload_error=True)
        self.assertEqual(events,['upload','prompt'])
        self.assertTrue(report['upload_uncertain'])
        self.assertTrue(report['prompt_verified'])
        self.assertFalse(report['delivered'])
        self.assertIn('Prompt đã điền dù upload chưa xác nhận.', report['logs'])

    async def test_settings_failure_does_not_block_upload(self):
        report,_=await self.exercise(settings_error=True)
        self.assertTrue(report['delivered'])
        self.assertTrue(report['prompt_verified'])
        self.assertIn('settings',report['errors'])

    async def test_attachment_timeout_keeps_prompt(self):
        report,events=await self.exercise(attach_error=True)
        self.assertEqual(report['state'],'inputs_sent')
        self.assertFalse(report['image_attached'])
        self.assertTrue(report['prompt_verified'])
        self.assertIn('attachment',report['errors'])

    async def test_unrelated_new_media_id_is_never_selected(self):
        report={'upload_provenance':{}}
        with patch.object(m,'library_snapshot',AsyncMock(return_value={'unrelated':{'ready':True,'filename_match':False}})):
            with self.assertRaises(m.PairStopped):
                await m.trace_uploaded_media(None,{},'unique-file',AsyncMock(),report,timeout=.01)
        self.assertNotIn('method',report['upload_provenance'])

if __name__=='__main__': unittest.main()
