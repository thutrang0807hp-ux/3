"""Reviewable regression cases; synthetic fixtures, never contact Google.

Run only after code review:
  python3 -m local_engine.check_flow_task_tracker
These cases do not validate current Flow's live wire format.
"""
import asyncio
import json
import unittest
from urllib.parse import urlencode
from .flow_task_protocol import (
    BATCH_PATH, REFERENCE_RPC, STATUS_RPC, DETAIL_RPC, UnsupportedFlowPayload,
    asset_video_url, checked_video_url, reference_request, rpc_payload, submitted_media,
)
from .flow_task_tracker import FlowTaskTracker, READ_RPC

PROJECT = '11111111-1111-4111-8111-111111111111'
IMAGE = '22222222-2222-4222-8222-222222222222'
VIDEO = '33333333-3333-4333-8333-333333333333'
WORKFLOW = '44444444-4444-4444-8444-444444444444'
OTHER = '55555555-5555-4555-8555-555555555555'
PROMPT = 'A person waves.\nKeep the same outfit.'
SECRET = 'PRIVATE_SESSION_VALUE'
IDENTITY = {'media_id': VIDEO, 'project_id': PROJECT, 'workflow_id': WORKFLOW}
URL = 'https://flow.google.com/project/' + PROJECT
ENDPOINT = 'https://flow.google.com' + BATCH_PATH + '?' + urlencode({'rpcids': REFERENCE_RPC, 'source-path': '/project/' + PROJECT})
FORM_TYPE = 'application/x-www-form-urlencoded;charset=UTF-8'


def request(prompt=PROMPT, project=PROJECT, count=1):
    row = [[None, None, [[ [prompt] ]]], [[None, IMAGE]], 'veo_3_1_lite', 1]
    payload = [[row] * count, [None, 22, None, None, None, project]]
    return urlencode({'f.req': json.dumps([[[REFERENCE_RPC, json.dumps(payload), None, 'generic']]]), 'at': SECRET})


def media_payload(code=2, media=VIDEO, workflow=WORKFLOW, project=PROJECT, url=None):
    metadata = [None] * 9
    metadata[8] = [code]
    row = [media, project, workflow, None, None, metadata]
    if url:
        row.append(url)
    return [None, None, [row]]


def response(payload, rpc=REFERENCE_RPC):
    frame = json.dumps([['wrb.fr', rpc, json.dumps(payload, ensure_ascii=False), None, None, None]], ensure_ascii=False).encode()
    return b")]}'\n\n" + str(len(frame)).encode() + b'\n' + frame + b'\n'


class ProtocolCases(unittest.TestCase):
    def test_form_xssi_nested_payload_and_identity(self):
        parsed = reference_request(request(), FORM_TYPE, PROMPT, PROJECT)
        self.assertEqual(parsed['input_media_ids'], [IMAGE])
        payload = rpc_payload(response(media_payload()), REFERENCE_RPC)
        self.assertEqual(submitted_media(payload, PROJECT), IDENTITY)

    def test_request_requires_exact_prompt_project_and_one_output(self):
        for raw in (request(prompt='Different prompt'), request(project=OTHER), request(count=2)):
            with self.assertRaises(UnsupportedFlowPayload):
                reference_request(raw, FORM_TYPE, PROMPT, PROJECT)
        # A matching prompt in metadata must not compensate for a different prompt field.
        raw = request(prompt='Different prompt') + '&debug=' + PROMPT
        with self.assertRaises(UnsupportedFlowPayload):
            reference_request(raw, FORM_TYPE, PROMPT, PROJECT)

    def test_error_with_http_200_duplicate_rpc_and_broken_framing(self):
        error = json.dumps([['wrb.fr', REFERENCE_RPC, None, None, None, [7]]])
        with self.assertRaises(UnsupportedFlowPayload):
            rpc_payload(error, REFERENCE_RPC)
        row = ['wrb.fr', REFERENCE_RPC, json.dumps(media_payload())]
        with self.assertRaises(UnsupportedFlowPayload):
            rpc_payload(json.dumps([row, row]), REFERENCE_RPC)
        with self.assertRaises(UnsupportedFlowPayload):
            rpc_payload(response(media_payload())[:-8], REFERENCE_RPC)

    def test_no_arbitrary_uuid_or_thumbnail_fallback(self):
        with self.assertRaises(UnsupportedFlowPayload):
            submitted_media([OTHER, [VIDEO, PROJECT, WORKFLOW]], PROJECT)
        with self.assertRaises(UnsupportedFlowPayload):
            submitted_media(media_payload(project=OTHER), PROJECT)

    def test_asset_identity_and_url_are_both_required(self):
        signed = 'https://flow-content.google/video/' + VIDEO + '?signature=' + SECRET
        self.assertEqual(asset_video_url(media_payload(url=signed), IDENTITY), signed)
        self.assertIsNone(checked_video_url('https://flow-content.google.evil.invalid/video/' + VIDEO, VIDEO))
        self.assertIsNone(checked_video_url('https://flow-content.google/video/' + OTHER, VIDEO))
        with self.assertRaises(UnsupportedFlowPayload):
            asset_video_url(media_payload(media=OTHER, url=signed), IDENTITY)


class TrackerCases(unittest.IsolatedAsyncioTestCase):
    def make_tracker(self):
        now = [100.0]
        calls, persisted = [], []
        async def check():
            pass
        class Page:
            url = URL
            async def evaluate(self, script, args):
                if script != READ_RPC:
                    raise AssertionError('Unexpected browser action')
                calls.append(args)
                if args['method'] == STATUS_RPC:
                    payload = media_payload(code=3)
                elif args['method'] == DETAIL_RPC:
                    payload = media_payload(url='https://flow-content.google/video/' + VIDEO + '?signature=' + SECRET)
                else:
                    raise AssertionError('Generation/replay attempted')
                return {'status': 200, 'body': response(payload, args['method'])}
        tracker = FlowTaskTracker(Page(), PROMPT, URL, check, persisted.append, clock=lambda: now[0])
        return tracker, now, calls, persisted

    def link(self, tracker, key='http-1'):
        tracker.mark_generate_attempt()
        tracker.observe_request(key, ENDPOINT, 'POST', FORM_TYPE, request(), True)
        tracker.observe_response(key, 200, response(media_payload()))

    async def test_one_send_id_status_detail_no_secret_export(self):
        tracker, now, calls, persisted = self.make_tracker()
        self.link(tracker)
        await tracker.tick()
        self.assertEqual(calls, [])  # Correlation window has not settled.
        now[0] += 16
        await tracker.tick()
        self.assertEqual([call['method'] for call in calls], [STATUS_RPC, DETAIL_RPC])
        self.assertEqual(tracker.snapshot()['state'], 'ready')
        self.assertIn(SECRET, tracker.video_url)  # Transient signed URL needed for download.
        self.assertNotIn(SECRET, json.dumps(persisted))
        self.assertNotIn(PROMPT, json.dumps(persisted))
        self.assertEqual(persisted[1]['submit_http_request'], 'http-1')
        self.assertTrue(any(record.get('media_id') == VIDEO for record in persisted))

    async def test_preclick_and_wrong_prompt_never_link_or_poll(self):
        tracker, now, calls, _ = self.make_tracker()
        tracker.observe_request('before', ENDPOINT, 'POST', FORM_TYPE, request(), False)
        tracker.mark_generate_attempt()
        tracker.observe_response('before', 200, response(media_payload()))
        tracker.observe_request('wrong', ENDPOINT, 'POST', FORM_TYPE, request(prompt='wrong'), True)
        tracker.observe_response('wrong', 200, response(media_payload()))
        now[0] += 61
        await tracker.tick()
        self.assertTrue(tracker.correlation_expired())
        self.assertFalse(tracker.snapshot()['association_confirmed'])
        self.assertEqual(calls, [])

    async def test_second_matching_send_blocks_even_before_its_response(self):
        tracker, now, calls, _ = self.make_tracker()
        self.link(tracker)
        tracker.observe_request('http-2', ENDPOINT, 'POST', FORM_TYPE, request(), True)
        now[0] += 16
        await tracker.tick()
        self.assertTrue(tracker.blocked)
        self.assertIsNone(tracker.identity)
        self.assertFalse(tracker.snapshot()['association_confirmed'])
        self.assertEqual(calls, [])

    async def test_mismatched_poll_does_not_complete_or_read_asset(self):
        tracker, now, calls, _ = self.make_tracker()
        self.link(tracker)
        async def read(method):
            calls.append(method)
            return media_payload(code=3, media=OTHER)
        tracker._read = read
        now[0] += 16
        await tracker.tick()
        self.assertEqual(calls, [STATUS_RPC])
        self.assertEqual(tracker.snapshot()['read_failures'], 1)
        self.assertEqual(tracker.identity, IDENTITY)
        self.assertNotEqual(tracker.snapshot()['state'], 'ready')

    async def test_flow_failure_is_separate_from_read_failure(self):
        tracker, now, calls, _ = self.make_tracker()
        self.link(tracker)
        async def read(method):
            calls.append(method)
            return media_payload(code=4)
        tracker._read = read
        now[0] += 16
        await tracker.tick()
        self.assertEqual(tracker.snapshot()['state'], 'failed')
        self.assertEqual(tracker.snapshot()['read_failures'], 0)
        self.assertEqual(calls, [STATUS_RPC])

    async def test_binding_change_prevents_any_status_request(self):
        tracker, now, calls, _ = self.make_tracker()
        self.link(tracker)
        async def deny():
            raise RuntimeError('Changed account')
        tracker.check = deny
        now[0] += 16
        await tracker.tick()
        self.assertEqual(calls, [])
        self.assertEqual(tracker.snapshot()['read_failures'], 1)

    async def test_persist_failure_prevents_result_use(self):
        tracker, now, calls, _ = self.make_tracker()
        self.link(tracker)
        def deny(_):
            raise OSError('Disk unavailable')
        tracker.persist = deny
        with self.assertRaises(OSError):
            tracker.observe_response('http-1', 200, response(media_payload()))
        now[0] += 16
        await tracker.tick()
        self.assertTrue(tracker.blocked)
        self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
