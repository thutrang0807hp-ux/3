"""Offline contract tests. Do not certify live Google generation or playback."""
import asyncio
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from .flow_scene_job import Identity, Prepared, Scene, SceneStore, SceneWorkflow
from .flow_scene_rpc import DirectReferenceAdapter, reference_payload
from .flow_task_protocol import FlowRpcRejected, REFERENCE_RPC, STATUS_RPC, DETAIL_RPC

PROJECT = '11111111-1111-4111-8111-111111111111'
IMAGE = '22222222-2222-4222-8222-222222222222'
VIDEO = '33333333-3333-4333-8333-333333333333'
WORKFLOW = '44444444-4444-4444-8444-444444444444'
IDENTITY = Identity(VIDEO, PROJECT, WORKFLOW)


class Adapter:
    def __init__(self, root):
        self.root = root
        self.sends = 0
        self.reads = 0
        self.failure = None
        self.status_value = 'success'
        self.receive_error = False

    async def check(self, account, project):
        if account != 'account' or project not in (None, PROJECT):
            raise ValueError('binding_changed')

    async def prepare(self, scene):
        return Prepared(scene.account_id, PROJECT, IMAGE)

    async def submit(self, scene, prepared):
        self.sends += 1
        if self.failure:
            raise self.failure
        return IDENTITY

    async def status(self, identity):
        assert identity == IDENTITY
        self.reads += 1
        return self.status_value

    async def receive(self, identity, request_id):
        if self.receive_error:
            raise OSError('download interrupted')
        path = self.root / 'adapter-validated-fixture.bin'
        # Test double for the receive contract; deliberately not a real video.
        path.write_bytes(b'fixture bytes')
        return path


class JobCases(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        image = self.root / 'reference.bin'
        image.write_bytes(b'image fixture')
        self.scene = Scene('request-1', 'account', 'room', 'scene', 'a', 'Wave.', image)
        self.store = SceneStore(self.root / 'jobs.sqlite')
        self.adapter = Adapter(self.root)
        self.workflow = self.new_workflow()

    def new_workflow(self):
        return SceneWorkflow(self.store, self.adapter, poll_interval=0, max_polls=2)

    async def test_one_send_persisted_identity_correct_scene(self):
        row = await self.workflow.create(self.scene)
        self.assertEqual(row['state'], 'done')
        self.assertEqual(row['result']['scene_id'], 'scene')
        self.assertEqual(row['result']['provider_identity']['media_id'], VIDEO)
        await self.new_workflow().create(self.scene)
        self.assertEqual(self.adapter.sends, 1)

    async def test_concurrent_duplicate_across_workflow_instances(self):
        await asyncio.gather(self.workflow.create(self.scene), self.new_workflow().create(self.scene))
        self.assertEqual(self.adapter.sends, 1)

    async def test_changed_content_same_request_is_rejected(self):
        await self.workflow.create(self.scene)
        from dataclasses import replace
        with self.assertRaisesRegex(ValueError, 'content_changed'):
            await self.workflow.create(replace(self.scene, prompt='Different'))
        self.assertEqual(self.adapter.sends, 1)

    async def test_timeout_during_send_is_unknown_and_never_resubmitted(self):
        self.adapter.failure = TimeoutError('private response content')
        with self.assertRaises(TimeoutError):
            await self.workflow.create(self.scene)
        self.assertEqual(self.store.get(self.scene.request_id)['state'], 'unknown')
        await self.new_workflow().create(self.scene)
        await self.new_workflow().follow(self.scene.request_id)
        self.assertEqual(self.adapter.sends, 1)
        self.assertNotIn('private', json.dumps(self.store.get(self.scene.request_id)))

    async def test_cancellation_during_send_is_unknown(self):
        self.adapter.failure = asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            await self.workflow.create(self.scene)
        self.assertEqual(self.store.get(self.scene.request_id)['state'], 'unknown')

    async def test_native_rejection_is_safe_and_not_polled(self):
        self.adapter.failure = FlowRpcRejected({'rpc_error_code': 7,
            'public_error_codes': ['PUBLIC_ERROR_UNUSUAL_ACTIVITY'], 'raw': 'PRIVATE'})
        row = await self.workflow.create(self.scene)
        self.assertEqual(row['state'], 'rejected')
        self.assertEqual(self.adapter.reads, 0)
        self.assertNotIn('PRIVATE', json.dumps(row))
        await self.new_workflow().create(self.scene)
        self.assertEqual(self.adapter.sends, 1)

    async def test_restart_with_dispatch_boundary_never_sends(self):
        self.store.reserve(self.scene)
        self.store.transition(self.scene.request_id, 'preparing', 'dispatching')
        row = await self.new_workflow().create(self.scene)
        self.assertEqual(row['state'], 'dispatching')
        self.assertEqual(self.adapter.sends, 0)

    async def test_poll_timeout_keeps_identity_and_can_resume(self):
        self.adapter.status_value = 'pending'
        row = await self.workflow.create(self.scene)
        self.assertEqual(row['state'], 'pending')
        self.assertEqual(row['identity']['media_id'], VIDEO)
        self.adapter.status_value = 'success'
        row = await self.new_workflow().follow(self.scene.request_id)
        self.assertEqual(row['state'], 'done')
        self.assertEqual(self.adapter.sends, 1)

    async def test_download_failure_resumes_without_new_generation(self):
        self.adapter.receive_error = True
        with self.assertRaises(OSError):
            await self.workflow.create(self.scene)
        self.assertEqual(self.store.get(self.scene.request_id)['state'], 'receiving')
        self.adapter.receive_error = False
        row = await self.new_workflow().follow(self.scene.request_id)
        self.assertEqual(row['state'], 'done')
        self.assertEqual(self.adapter.sends, 1)

    async def test_other_scene_blocked_while_account_unresolved(self):
        from dataclasses import replace
        self.adapter.status_value = 'pending'
        await self.workflow.create(self.scene)
        with self.assertRaises(sqlite3.IntegrityError):
            await self.new_workflow().create(replace(self.scene, request_id='request-2', scene_id='other'))
        self.assertEqual(self.adapter.sends, 1)

    async def test_persistence_failure_before_send_does_not_dispatch(self):
        from unittest.mock import patch
        with patch.object(self.store, 'transition', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                await self.workflow.create(self.scene)
        self.assertEqual(self.adapter.sends, 0)

    async def test_provider_failure_never_downloads(self):
        self.adapter.status_value = 'failed'
        row = await self.workflow.create(self.scene)
        self.assertEqual(row['state'], 'failed')
        self.assertIsNone(row['result'])

    async def test_identity_commit_failure_cannot_send_again(self):
        from unittest.mock import patch
        transition = self.store.transition
        def write(request_id, expected, state, **values):
            if state == 'pending':
                raise OSError('disk full')
            return transition(request_id, expected, state, **values)
        with patch.object(self.store, 'transition', side_effect=write):
            with self.assertRaises(OSError):
                await self.workflow.create(self.scene)
        self.assertEqual(self.store.get(self.scene.request_id)['state'], 'dispatching')
        await self.new_workflow().create(self.scene)
        self.assertEqual(self.adapter.sends, 1)

    async def test_changed_reference_during_preparation_never_sends(self):
        original = self.adapter.prepare
        async def prepare(scene):
            scene.image.write_bytes(b'changed image')
            return await original(scene)
        self.adapter.prepare = prepare
        with self.assertRaisesRegex(ValueError, 'scene_changed'):
            await self.workflow.create(self.scene)
        self.assertEqual(self.adapter.sends, 0)
        self.assertEqual(self.store.get(self.scene.request_id)['state'], 'prepare_failed')


class PayloadCases(unittest.TestCase):
    def test_single_reference_payload(self):
        prepared = Prepared('account', PROJECT, IMAGE)
        context = [None, 22, None, None, None, PROJECT, None, None, None, None, ['EPHEMERAL', 1]]
        value = reference_payload('Wave.', prepared, context, new_id=lambda: 'ID')
        self.assertEqual(value, [[[[None, None, [[['Wave.']]]], [[None, IMAGE]],
            'veo_3_1_r2v_lite', 1, None, [None, None, None, None, 'ID', 'ID']]],
            context, ['ID', 2]])

    def test_wrong_project_context_rejected(self):
        with self.assertRaises(ValueError):
            reference_payload('Wave.', Prepared('account', PROJECT, IMAGE), [None] * 11)


class RpcAdapterCases(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.calls = []
        self.rejection = False
        self.bad_identity = False
        outer = self
        class Session:
            async def reference_context(self, project):
                return [None, 22, None, None, None, project, None, None, None, None, ['PRIVATE', 1]]

            async def rpc(self, method, project, payload):
                outer.calls.append((method, project, payload))
                media = IMAGE if outer.bad_identity else VIDEO
                metadata = [None] * 9
                metadata[8] = [3]
                row = [media, PROJECT, WORKFLOW, None, None, metadata]
                if method == DETAIL_RPC:
                    row.append('https://flow-content.google/video/' + VIDEO + '?signature=PRIVATE')
                body = [None, None, [row]]
                if outer.rejection:
                    rows = [['wrb.fr', method, None, None, None,
                             [7, 'PRIVATE', ['PUBLIC_ERROR_UNUSUAL_ACTIVITY']]]]
                else:
                    rows = [['wrb.fr', method, json.dumps(body), None, None, None]]
                frame = json.dumps(rows).encode()
                return 200, b")]}'\n\n" + str(len(frame)).encode() + b'\n' + frame + b'\n'

            async def receive(self, identity, url, request_id):
                assert identity == IDENTITY and 'signature=PRIVATE' in url
                return Path('/app/validated/' + request_id + '.mp4')
        self.adapter = DirectReferenceAdapter(Session())
        self.prepared = Prepared('account', PROJECT, IMAGE)
        self.scene = Scene('rpc-request', 'account', 'room', 'scene', 'a', 'Wave.', Path('unused'))

    async def test_direct_dispatch_status_detail_by_identity(self):
        identity = await self.adapter.submit(self.scene, self.prepared)
        self.assertEqual(identity, IDENTITY)
        self.assertEqual(await self.adapter.status(identity), 'success')
        result = await self.adapter.receive(identity, 'rpc-request')
        self.assertEqual(result, Path('/app/validated/rpc-request.mp4'))
        self.assertEqual([row[0] for row in self.calls], [REFERENCE_RPC, STATUS_RPC, DETAIL_RPC])
        self.assertEqual(self.calls[1][2], [None, None, [[VIDEO]]])
        self.assertEqual(self.calls[2][2], [VIDEO])

    async def test_rpc_rejection_is_not_retried(self):
        self.rejection = True
        with self.assertRaises(FlowRpcRejected):
            await self.adapter.submit(self.scene, self.prepared)
        self.assertEqual(len(self.calls), 1)

    async def test_input_image_is_not_accepted_as_video(self):
        self.bad_identity = True
        with self.assertRaises(ValueError):
            await self.adapter.submit(self.scene, self.prepared)
        self.assertEqual(len(self.calls), 1)


if __name__ == '__main__':
    unittest.main()
