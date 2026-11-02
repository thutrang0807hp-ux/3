"""Upload-ID provenance tests; synthetic data only."""
import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode
from unittest.mock import AsyncMock

from .flow_native_reference import UploadMediaCapture
from .check_flow_task_tracker import PROJECT, IMAGE, OTHER, response


class Request:
    method = 'POST'
    url = 'https://flow.google.com/_/AiSandboxAngularFrontend/data/batchexecute'
    def __init__(self, raw, project=PROJECT):
        payload = [[None,22,None,None,None,project],base64.b64encode(raw).decode(),'image/png']
        self.post_data = urlencode({'f.req':json.dumps([[['maseQ',json.dumps(payload),None,'generic']]]),
                                    'at':'PRIVATE_UPLOAD_TOKEN'})


class UploadCases(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.image=Path(self.folder.name)/'image.png'
        self.image.write_bytes(b'original image bytes')
        self.report={'reference_sha256':hashlib.sha256(self.image.read_bytes()).hexdigest()}
        self.capture=UploadMediaCapture(SimpleNamespace(url='https://flow.google.com/project/'+PROJECT),self.image,self.report)

    async def test_exact_image_project_and_unique_id(self):
        request=Request(self.image.read_bytes())
        self.capture.request(request)
        self.assertIn(request,self.capture.requests)
        await self.capture.read(SimpleNamespace(body=AsyncMock(return_value=response([IMAGE,PROJECT], 'maseQ'))))
        self.assertEqual(self.report['uploaded_media_id'],IMAGE)
        self.assertNotIn('PRIVATE_UPLOAD_TOKEN',json.dumps(self.report))

    async def test_wrong_source_or_project_is_not_captured(self):
        for request in (Request(b'other image'),Request(self.image.read_bytes(),OTHER)):
            self.capture.request(request)
        self.assertFalse(self.capture.requests)

    async def test_ambiguous_response_never_picks_first_id(self):
        await self.capture.read(SimpleNamespace(body=AsyncMock(return_value=response([IMAGE,OTHER], 'maseQ'))))
        self.assertNotIn('uploaded_media_id',self.report)

    async def test_two_matching_uploads_with_different_ids_invalidate_receipt(self):
        for media in (IMAGE,OTHER):
            await self.capture.read(SimpleNamespace(body=AsyncMock(return_value=response([media], 'maseQ'))))
        self.assertNotIn('uploaded_media_id',self.report)
        self.assertEqual(self.report['uploaded_media_evidence'],'ambiguous_upload_ids')


if __name__=='__main__':
    unittest.main()
