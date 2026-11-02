"""Draft: correlate the existing UI send, then issue ONLY status/detail reads.

No Generate RPC, no replay, no automatic retry, no token/body/URL persistence.
Read RPC schemas still require verification against the user's live Flow session.
"""
import asyncio
from .flow_batch_session import batch_script
import copy
import hashlib
import time
from urllib.parse import parse_qs, urlsplit
from .flow_task_protocol import (
    BATCH_PATH, REFERENCE_RPC, STATUS_RPC, DETAIL_RPC, SCHEMA,
    UnsupportedFlowPayload, FlowRpcRejected, asset_video_url, batch_endpoint, media_status,
    project_from_url, reference_request, rpc_payload, submitted_media,
    UUID,
)


# Only the two read methods below can reach fetch. No caller-supplied body or URL.
READ_RPC = batch_script('read')


class FlowTaskTracker:
    def __init__(self, page, prompt, project_url, check, persist, *, clock=time.monotonic):
        self.page, self.prompt, self.check, self.persist = page, prompt, check, persist
        self.project_id = project_from_url(project_url)
        self.clock = clock
        self.attempt = None
        self.requests = {}
        self.identity = None
        self.blocked = False
        self.next_poll = 0
        self.poll_count = 0
        self.video_url = None   # Memory only. Never part of snapshot / ledger / JSON.
        self.report = {'schema': SCHEMA, 'association_confirmed': False,
                       'expected_prompt_sha256': hashlib.sha256(' '.join(prompt.split()).encode()).hexdigest(),
                       'state': 'unlinked', 'progress': None, 'progress_source': None,
                       'poll_count': 0, 'read_failures': 0, 'generation_submitted_by_tracker': False,
                       'automatic_retry': False, 'rejections': [], 'status_response_verified': False}

    def _publish(self):
        # Persistence is synchronous, before the caller can poll/download a result.
        try:
            self.persist(self.snapshot())
        except Exception:
            self.blocked = True
            self.video_url = None
            self.report.update(state='persistence_failed', association_confirmed=False)
            raise

    def _reject(self, code):
        if code not in self.report['rejections'] and len(self.report['rejections']) < 20:
            self.report['rejections'].append(code)
            return True
        return False

    def mark_generate_attempt(self):
        if self.attempt is not None:
            raise RuntimeError('one_generate_attempt_only')
        self.attempt = self.clock()
        self.report['state'] = 'awaiting_submit_response'
        self._publish()

    def bind_direct_request(self, reference_id):
        """Own sender's single response; no passive/UI request correlation."""
        if (self.attempt is None or self.requests or self.blocked or
                not isinstance(reference_id, str) or not UUID.fullmatch(reference_id)):
            raise UnsupportedFlowPayload('direct_request_binding_invalid')
        self.requests['native-direct'] = {'input_media_ids': [reference_id]}
        self.report.update(submission_method='native_reference_rpc',
                           submit_http_request='native-direct')
        self._publish()

    def accept_direct_response(self, status, raw):
        if self.report.get('submission_method') != 'native_reference_rpc':
            raise UnsupportedFlowPayload('direct_response_without_request')
        self.observe_response('native-direct', status, raw)
        if self.identity:
            self.next_poll = self.clock() + 10

    def observe_request(self, key, url, method, content_type, raw, after_attempt):
        if self.attempt is None or not after_attempt or not batch_endpoint(url) or method != 'POST':
            return
        # source-path is used transiently; auth query/form fields are never retained.
        paths = parse_qs(urlsplit(url).query, max_num_fields=40).get('source-path', [])
        if paths != ['/project/' + self.project_id]:
            if self._reject('request_source_project_mismatch'):
                self._publish()
            return
        try:
            parsed = reference_request(raw, content_type, self.prompt, self.project_id)
        except (ValueError, TypeError, UnicodeError, RecursionError) as error:
            code = str(error) if isinstance(error, UnsupportedFlowPayload) else 'request_decode_failed'
            if self._reject(code):
                self._publish()
            return
        if key in self.requests:
            return
        # A second matching UI request is ambiguous, even if its response is late.
        if self.requests or self.clock() - self.attempt > 15:
            self.blocked = True
            self.identity = self.video_url = None
            self.report.update(state='ambiguous_submit', association_confirmed=False)
            for field in ('media_id', 'project_id', 'workflow_id'):
                self.report.pop(field, None)
            self._reject('multiple_or_late_matching_sends')
            self._publish()
            return
        self.requests[key] = parsed
        self.report['submit_http_request'] = key
        self._publish()

    def observe_response(self, key, status, raw):
        if key not in self.requests or self.blocked:
            return
        if not 200 <= status < 300:
            self.report.update(state='submit_unconfirmed', submit_http_status=status)
            self._publish()
            return
        try:
            payload = rpc_payload(raw, REFERENCE_RPC)
            identity = submitted_media(payload, self.project_id)
            if identity['media_id'] in self.requests[key]['input_media_ids']:
                raise UnsupportedFlowPayload('submit_returned_input_image')
        except (ValueError, TypeError, UnicodeError, RecursionError) as error:
            code = str(error) if isinstance(error, UnsupportedFlowPayload) else 'response_decode_failed'
            self._reject(code)
            self.report['state'] = 'rpc_rejected' if isinstance(error,FlowRpcRejected) else 'submit_unconfirmed'
            if isinstance(error,FlowRpcRejected):self.report['submit_rpc_error']=error.details
            self._publish()
            return
        if self.identity is not None and self.identity != identity:
            self.blocked = True
            self.identity = None
            self.report.update(state='ambiguous_submit', association_confirmed=False)
            for field in ('media_id', 'project_id', 'workflow_id'):
                self.report.pop(field, None)
            self._publish()
            return
        self.identity = identity
        self.report.update(state='pending', association_confirmed=True, linked_at_unix=time.time(), **identity)
        # Let the 15-second correlation window settle before result actions.
        self.next_poll = max(self.clock(), self.attempt + 15)
        self._publish()

    def snapshot(self):
        return copy.deepcopy(self.report)

    def invalidate(self, code):
        self.blocked = True
        self.identity = self.video_url = None
        self.report.update(state='needs_review', association_confirmed=False)
        for field in ('media_id', 'project_id', 'workflow_id'):
            self.report.pop(field, None)
        self._reject(code)
        self._publish()

    async def _read(self, method):
        if method not in (STATUS_RPC, DETAIL_RPC) or self.blocked or not self.identity:
            raise UnsupportedFlowPayload('read_requires_identity')
        await self.check()
        if project_from_url(self.page.url) != self.project_id:
            raise UnsupportedFlowPayload('read_project_changed')
        reply = await asyncio.wait_for(self.page.evaluate(READ_RPC, {
            'method': method, 'project': self.project_id, 'media': self.identity['media_id'],
            'batchPath': BATCH_PATH,
        }), timeout=10)
        await self.check()
        if project_from_url(self.page.url) != self.project_id:
            raise UnsupportedFlowPayload('read_project_changed')
        if not isinstance(reply, dict) or type(reply.get('status')) is not int:
            raise UnsupportedFlowPayload('read_reply_shape')
        if not 200 <= reply['status'] < 300:
            raise UnsupportedFlowPayload('read_http_error')
        return rpc_payload(reply.get('body'), method)

    async def tick(self):
        """One bounded status read, optionally detail. Read failures keep identity."""
        if self.blocked or not self.identity or self.report['state'] in ('failed', 'ready'):
            return
        if self.clock() < self.next_poll:
            return
        self.next_poll = self.clock() + 10
        self.poll_count += 1
        self.report['poll_count'] = self.poll_count
        try:
            status = media_status(await self._read(STATUS_RPC), self.identity)
            if self.blocked:
                return
            self.report.update(status, status_response_verified=True)
            self.report.pop('tracking_error', None)
            self._publish()
            if status['state'] == 'success':
                payload = await self._read(DETAIL_RPC)
                if self.blocked:
                    return
                self.video_url = asset_video_url(payload, self.identity)
                self.report['state'] = 'ready'
                self._publish()
        except Exception as error:
            self.video_url = None
            # No raw error messages: browser errors may embed a signed URL/body.
            code = str(error) if isinstance(error, UnsupportedFlowPayload) else type(error).__name__
            self.report['tracking_error'] = code
            if isinstance(error,FlowRpcRejected):self.report['tracking_rpc_error']=error.details
            self.report['read_failures'] += 1
            self._publish()

    def correlation_expired(self):
        return self.attempt is not None and self.clock() - self.attempt >= 60 and not self.identity

    async def download_to(self, target):
        """Stream the linked asset only; a valid local video is checked by service.

        Redirects/CORS failures are reported, never worked around by credential
        export. No page download event is accepted as proof of this result.
        """
        import base64
        import secrets
        from .flow_task_protocol import checked_video_url
        if (self.blocked or not self.identity or self.report['state'] != 'ready' or
                not checked_video_url(self.video_url, self.identity['media_id'])):
            raise UnsupportedFlowPayload('download_requires_linked_asset')
        key = '__sfLinkedMedia_' + secrets.token_hex(12)
        try:
            await self.check()
            await asyncio.wait_for(self.page.evaluate(r'''async ({key, url}) => {
                const controller = new AbortController();
                const timer = setTimeout(() => controller.abort(), 120000);
                const state = {controller, timer}; window[key] = state;
                try {
                    const response = await fetch(url, {credentials: 'omit', redirect: 'error', signal: controller.signal});
                    if (!response.ok || !response.body ||
                        Number(response.headers.get('content-length') || 0) > 104857600)
                        throw Error('linked_media_unavailable');
                    state.reader = response.body.getReader(); state.total = 0; state.rest = null;
                } catch (error) { controller.abort(); throw Error('linked_media_unavailable'); }
            }''', {'key': key, 'url': self.video_url}), timeout=12)
            size = 0
            with target.open('wb') as stream:
                while True:
                    await self.check()
                    if self.blocked:
                        raise UnsupportedFlowPayload('download_attribution_changed')
                    part = await asyncio.wait_for(self.page.evaluate(r'''async key => {
                        const s = window[key]; if (!s?.reader) throw Error('linked_media_closed');
                        let bytes = s.rest; s.rest = null;
                        if (!bytes) {
                            const next = await s.reader.read();
                            if (next.done) return null;
                            bytes = next.value;
                        }
                        if (bytes.length > 262144) { s.rest = bytes.subarray(262144); bytes = bytes.subarray(0, 262144); }
                        s.total += bytes.length;
                        if (s.total > 104857600) { s.controller.abort(); throw Error('linked_media_limit'); }
                        let text = '';
                        for (let i = 0; i < bytes.length; i += 8192) text += String.fromCharCode(...bytes.subarray(i, i + 8192));
                        return btoa(text);
                    }''', key), timeout=15)
                    if part is None:
                        break
                    chunk = base64.b64decode(part, validate=True)
                    size += len(chunk)
                    if size > 100 * 1024**2:
                        raise UnsupportedFlowPayload('download_size_limit')
                    stream.write(chunk)
            await self.check()
            if self.blocked or not size:
                raise UnsupportedFlowPayload('download_incomplete_or_ambiguous')
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        finally:
            try:
                await asyncio.wait_for(self.page.evaluate(r'''async key => {
                    const s = window[key]; delete window[key];
                    if (s) { clearTimeout(s.timer); s.controller.abort();
                        try { await s.reader?.cancel(); } catch {} }
                }''', key), timeout=2)
            except Exception:
                pass
