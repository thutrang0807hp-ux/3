"""Native session/project/upload contracts. Offline; never contacts Google."""
import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from .check_flow_task_tracker import PROJECT, IMAGE, VIDEO, OTHER, response
from .flow_native_pipeline import (NativePipelineStopped, NativeProjectSession,
    ensure_native_project, upload_identity, image_resolved, unique_id)
from .flow_task_protocol import UnsupportedFlowPayload, rpc_payload


class ShapeCases(unittest.TestCase):
    def test_upload_exact_slot_not_first_uuid_anywhere(self):
        self.assertEqual(upload_identity([[IMAGE, ['metadata', OTHER]]], PROJECT), IMAGE)
        for payload in ([None, IMAGE], [[PROJECT]], [[None, IMAGE]], [IMAGE]):
            with self.assertRaises(UnsupportedFlowPayload):
                upload_identity(payload, PROJECT)

    def test_detail_bound_to_exact_image_project_url(self):
        good = [IMAGE, PROJECT, None, 'https://flow-content.google/image/'+IMAGE+'?signed=PRIVATE']
        self.assertTrue(image_resolved(good, IMAGE, PROJECT))
        for changed in ([OTHER]+good[1:], [IMAGE, OTHER]+good[2:],
                        good[:3]+['https://evil.test/image/'+IMAGE],
                        good[:3]+['https://flow-content.google/image/'+OTHER],
                        good[:3]+['https://flow-content.google/video/'+IMAGE]):
            with self.assertRaises(UnsupportedFlowPayload):
                image_resolved(changed, IMAGE, PROJECT)

    def test_wrapped_asset_detail(self):
        row=[IMAGE,PROJECT,None,'https://flow-content.google/image/'+IMAGE]
        for payload in ([None,None,[row]],[None,None,None,[row]]):
            self.assertTrue(image_resolved(payload,IMAGE,PROJECT))

    def test_project_creation_cannot_choose_between_ids(self):
        self.assertEqual(unique_id([[PROJECT],PROJECT]),PROJECT)
        for value in ([PROJECT,OTHER],[],[123]):
            with self.assertRaises(UnsupportedFlowPayload):
                unique_id(value)

    def test_empty_payload_allowed_only_explicitly_for_read_bootstrap(self):
        raw=b")]}'\n"+json.dumps([['wrb.fr','nzlxg',None,None,None,None]]).encode()
        self.assertEqual(rpc_payload(raw,'nzlxg',allow_empty=True),[])
        with self.assertRaises(UnsupportedFlowPayload):rpc_payload(raw,'nzlxg')

    def test_scalar_project_id_supported_without_weakening_generation(self):
        self.assertEqual(rpc_payload(response(PROJECT,'jHPbke'),'jHPbke',allow_project_id=True),[PROJECT])
        with self.assertRaises(UnsupportedFlowPayload):
            rpc_payload(response(VIDEO,'MZZa6b'),'MZZa6b',allow_project_id=True)


class Vault:
    def __init__(self):self.values={}
    def secret(self,key):return copy.deepcopy(self.values.get(key))
    def set_secret(self,key,value):self.values[key]=copy.deepcopy(value)


class ProjectCases(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.vault=Vault();self.check=AsyncMock();self.creates=0
        self.fail_create=False;self.fail_navigation=False
        self.page=SimpleNamespace(url='https://flow.google.com/',wait_for_function=AsyncMock())
        async def evaluate(script,args):
            self.assertEqual(args['method'],'jHPbke')
            self.assertEqual(args['payload'],['projects/*',[None,['SceneForge · room']],[None,22]])
            self.creates+=1
            if self.fail_create:return {'error':'transport_unconfirmed'}
            return {'status':200,'body':response(PROJECT,'jHPbke').decode()}
        async def goto(url,**kwargs):
            if self.fail_navigation:raise TimeoutError('navigation failed')
            self.page.url=url
        self.page.evaluate=evaluate;self.page.goto=goto
        self.session=SimpleNamespace(page=self.page)

    async def test_create_persist_before_navigation_and_reuse(self):
        await ensure_native_project(self.session,self.vault,'account','room',self.check)
        self.assertEqual(self.creates,1)
        self.assertTrue(self.page.url.endswith(PROJECT))
        await ensure_native_project(self.session,self.vault,'account','room',self.check)
        self.assertEqual(self.creates,1)

    async def test_uncertain_create_does_not_create_again(self):
        self.fail_create=True
        with self.assertRaises(NativePipelineStopped):
            await ensure_native_project(self.session,self.vault,'account','room',self.check)
        self.fail_create=False
        with self.assertRaises(NativePipelineStopped):
            await ensure_native_project(self.session,self.vault,'account','room',self.check)
        self.assertEqual(self.creates,1)

    async def test_navigation_failure_keeps_known_project_id(self):
        self.fail_navigation=True
        with self.assertRaises(TimeoutError):
            await ensure_native_project(self.session,self.vault,'account','room',self.check)
        self.fail_navigation=False
        await ensure_native_project(self.session,self.vault,'account','room',self.check)
        self.assertEqual(self.creates,1)

    async def test_changed_account_guard_stops_before_creation(self):
        self.check.side_effect=NativePipelineStopped('account changed')
        with self.assertRaises(NativePipelineStopped):
            await ensure_native_project(self.session,self.vault,'account','room',self.check)
        self.assertEqual(self.creates,0)

    async def test_generation_method_denied_by_session_bootstrap_port(self):
        native=NativeProjectSession(self.page,self.check)
        with self.assertRaises(ValueError):await native.rpc('MZZa6b',PROJECT,[])
        self.assertEqual(self.creates,0)


if __name__=='__main__':unittest.main()
