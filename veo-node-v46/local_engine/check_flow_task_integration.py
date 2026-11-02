"""Real Chromium + real sender/ledger/ffprobe with intercepted HTTP only.

The fixture speaks the proposed Flow wire schema. This validates our wiring,
not the availability/correctness of that schema on live Google Flow.
"""
import asyncio
import base64
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit
from PIL import Image
from playwright.async_api import async_playwright
from .check_flow_prepare import SETTINGS
from .check_flow_task_tracker import (
    PROJECT, IMAGE, VIDEO, WORKFLOW, OTHER, PROMPT, SECRET, URL, ENDPOINT,
    REFERENCE_RPC, STATUS_RPC, DETAIL_RPC, media_payload, response,
)
from .flow_pair_generation import seal_pair, validate_pair
from .flow_prepare import PrepareStopped
from .flow_settings import DEFAULTS
from .flow_task_tracker import FlowTaskTracker
from .request_ledger import RequestLedger
from .simple_flow import SimpleFlow, MODEL
from .vault import Vault


class FixtureTimer(FlowTaskTracker):
    """Only waiting periods are shortened; real parsing/read/download code runs."""
    async def tick(self):
        if self.identity:
            self.next_poll = 0
        await super().tick()

    def correlation_expired(self):
        return self.attempt is not None and self.clock() - self.attempt >= 2 and not self.identity


async def until(predicate, timeout=12):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return
        await asyncio.sleep(.02)
    raise AssertionError('Fixture wait timed out')


async def scenario(browser, root, movie, mode):
    pipeline = mode.startswith('pipeline_')
    if pipeline:
        mode = 'native_' + mode.removeprefix('pipeline_')
    native = mode.startswith('native_')
    if native:
        mode = mode.removeprefix('native_')
    root.mkdir()
    buffer = io.BytesIO()
    Image.new('RGB', (40, 60), 'green').save(buffer, format='PNG')
    raw = buffer.getvalue()
    encoded = base64.b64encode(raw).decode()
    html = SETTINGS + '<form><img width=40 height=60 src="data:image/png;base64,' + encoded + '"><textarea></textarea><button type=button id=generate>Generate</button></form><script>window.sent=0;window.WIZ_global_data={cfb2h:"fixture-build",SNlM0e:"' + SECRET + '"};</script>'
    if native:
        if mode != 'missing_id':
            html = html.replace('<form>', '<form data-media-id="' + IMAGE + '">')
        if mode != 'missing_key':
            html += '<script type="application/json" src="https://www.google.com/recaptcha/enterprise.js?render=FIXTURE_SITE_KEY"></script>'
        html += '<script>window.grecaptcha={enterprise:{ready:f=>f(),execute:()=>Promise.resolve("PRIVATE_NATIVE_TOKEN")}};</script>'
    if pipeline:
        # No composer, settings panel, filechooser, chip or Generate button.
        html = '<title>Flow fixture</title><script>window.sent=0;window.WIZ_global_data={cfb2h:"fixture-build",SNlM0e:"'+SECRET+'"};window.grecaptcha={enterprise:{ready:f=>f(),execute:()=>Promise.resolve("PRIVATE_NATIVE_TOKEN")}};</script>'
        html += '<script type="application/json" src="https://www.google.com/recaptcha/enterprise.js?render=FIXTURE_SITE_KEY"></script>'
    context = await browser.new_context()
    counts = {'generate': 0, 'status': 0, 'detail': 0, 'download': 0}
    if pipeline:
        counts.update(upload=0,resolve=0,warmup=0)
    async def intercepted(route):
        r = route.request
        if r.resource_type == 'document':
            await route.fulfill(body=html, content_type='text/html; charset=utf-8')
            return
        if urlsplit(r.url).hostname == 'flow-content.google':
            counts['download'] += 1
            await route.fulfill(status=403 if mode == 'download_error' else 200,
                body=movie.read_bytes(), content_type='video/mp4',
                headers={'access-control-allow-origin': 'https://flow.google.com'})
            return
        fields = parse_qs(r.post_data or '')
        call = json.loads(fields['f.req'][0])[0][0]
        method = call[0]
        if pipeline and method in ('NfrxTb','ve2Lsc','DTaVef','nzlxg'):
            counts['warmup'] += 1
            wire=response([],method)
            await route.fulfill(body=wire,content_type='text/plain; charset=utf-8')
            return
        if pipeline and method == 'maseQ':
            counts['upload'] += 1
            upload=json.loads(call[1])
            assert upload[0][5]==PROJECT and upload[0][10]==['PRIVATE_NATIVE_TOKEN',1]
            assert upload[1]==encoded and upload[2]=='image/png'
            assert upload[3:8]==[1,None,None,None,None]
            if mode=='upload_transport_error':
                await route.abort();return
            if mode=='upload_rejected':
                rows=[['wrb.fr','maseQ',None,None,None,[7,SECRET,['PUBLIC_ERROR_UNUSUAL_ACTIVITY']]]]
                frame=json.dumps(rows).encode()
                wire=b")]}'\n\n"+str(len(frame)).encode()+b'\n'+frame+b'\n'
            else:
                wire=response([[OTHER if mode=='wrong_upload_id' else IMAGE]],method)
            if mode=='project_changed':
                await page.evaluate('(id)=>history.replaceState({},"","/project/"+id)',OTHER)
            await route.fulfill(body=wire,content_type='text/plain; charset=utf-8')
            return
        if pipeline and method==DETAIL_RPC and json.loads(call[1])==[IMAGE]:
            counts['resolve'] += 1
            data=[IMAGE,OTHER if mode=='wrong_image_project' else PROJECT,None,'https://flow-content.google/image/'+IMAGE+'?signature='+SECRET]
            await route.fulfill(body=response(data,method),content_type='text/plain; charset=utf-8')
            return
        if method == REFERENCE_RPC:
            counts['generate'] += 1
            if mode == 'transport_error':
                await route.abort()
                return
            if native:
                sent = json.loads(call[1])
                assert sent[0][0][2:4] == ['veo_3_1_r2v_lite', 1]
                assert sent[0][0][1] == [[None, IMAGE]]
                assert sent[1][5] == PROJECT
                assert sent[1][10] == ['PRIVATE_NATIVE_TOKEN', 1]
                from .flow_scene_job import Prepared
                from .flow_scene_rpc import reference_payload
                ids = iter([sent[0][0][5][4], sent[0][0][5][5], sent[2][0]])
                assert sent == reference_payload(PROMPT, Prepared('account', PROJECT, IMAGE),
                                                 sent[1], new_id=lambda: next(ids))
            payload = media_payload()
            if mode == 'rpc_rejected':
                rows=[['wrb.fr',REFERENCE_RPC,None,None,None,[7,SECRET,['PUBLIC_ERROR_UNUSUAL_ACTIVITY']]],['e',4,None,None,123]]
                await route.fulfill(body=")]}'\n1\n"+json.dumps(rows),content_type='application/json')
                return
            if mode == 'unlinked':
                payload = [OTHER]  # Does not identify any video row.
        elif method == STATUS_RPC:
            counts['status'] += 1
            assert json.loads(call[1]) == [None, None, [[VIDEO]]]
            if mode == 'read_error':
                await route.fulfill(status=503, body='unavailable', content_type='text/plain')
                return
            code = 4 if mode == 'failed' else 2 if mode == 'stop' else 3
            payload = media_payload(code=code, media=OTHER if mode == 'wrong_video' else VIDEO)
        elif method == DETAIL_RPC:
            counts['detail'] += 1
            assert json.loads(call[1]) == [VIDEO]
            payload = media_payload(url='https://flow-content.google/video/' + VIDEO + '?signature=' + SECRET)
        else:
            raise AssertionError('Unexpected RPC: ' + method)
        wire=response(payload,method)
        if mode=='rpc_lines_success':
            rows=[['wrb.fr',method,json.dumps(payload),None,None,None],['e',4,None,None,123]]
            wire=")]}'\n1\n"+json.dumps(rows)+'\n'
        await route.fulfill(body=wire, content_type='text/plain; charset=utf-8')
    await context.route('**/*', intercepted)
    page = await context.new_page()
    await page.goto(URL)
    if not pipeline:
      await page.locator('textarea').fill(PROMPT)
      await page.locator('#generate').evaluate(r'''(button, {endpoint, project, image, prompt, duplicate}) => {
        button.onclick = () => {
            window.sent++;
            const payload = [[[[null, null, [[[prompt]]]], [[null, image]], 'veo_3_1_lite', 1]], [null, 22, null, null, null, project]];
            const body = new URLSearchParams({'f.req': JSON.stringify([[['MZZa6b', JSON.stringify(payload), null, 'generic']]]), at: 'PRIVATE_SESSION_VALUE'});
            const send = () => fetch(endpoint, {method:'POST', body}).then(r => r.text());
            window.generated = duplicate ? Promise.all([send(), send()]) : send();
        };
    }''', {'endpoint': ENDPOINT, 'project': PROJECT, 'image': IMAGE, 'prompt': PROMPT, 'duplicate': mode == 'ambiguous'})
    service = SimpleFlow(root, Vault(root), RequestLedger(root))
    service.direct_reference_enabled = native
    service.native_pipeline_enabled = pipeline
    service.account_bridge = type('Bridge', (), {'background': True, 'selection': lambda _: {'available': True, 'token': 'token', 'account_id': 'account'}})()
    service.page = service.pair_page = page
    service.project = URL
    service.connected = True
    service.pair_trial_only = True
    service.assert_ready = AsyncMock()
    if pipeline and mode=='account_changed':
        from .simple_flow import SimpleStopped
        async def check_account():
            if counts['upload']:
                raise SimpleStopped('Tài khoản fixture đã đổi; chưa gửi tạo.')
        service.assert_ready=check_account
    service.disconnect_browser = AsyncMock()
    service.capture_preview = AsyncMock()
    report = {'request_id': 'flow-pair-' + mode, 'state': 'inputs_sent', 'account_id': 'account',
        'room_id': 'room', 'scene_id': 'scene', 'part': 'a', 'delivered': True,
        'image_attached': True, 'prompt_filled': True, 'prompt_verified': True, 'settings_verified': True,
        'reference_sha256': hashlib.sha256(raw).hexdigest(), 'prompt_sha256': hashlib.sha256(PROMPT.encode()).hexdigest()}
    service.pair_report = report
    if not pipeline:
        await seal_pair(service, report, DEFAULTS)
        assert report['generation_ready']
    validation = {'prepared_request_id': report['request_id'], 'account_id': 'account',
        'room_id': 'room', 'scene_id': 'scene', 'part': 'a', 'prompt': PROMPT}
    if not pipeline:
        await validate_pair(service, validation, raw)
        for changes in ({'prompt': 'Different'}, {'scene_id': 'wrong'}):
            try:
                await validate_pair(service, {**validation, **changes}, raw)
                raise AssertionError('Changed pair accepted')
            except PrepareStopped:
                pass
    body = {'request_id': 'flow-video-test-' + mode.replace('_', '-'), 'kind': 'video', 'model': MODEL, 'prompt': PROMPT,
        'references': [{'mime_type': 'image/png', 'data': encoded}], 'room_id': 'room',
        'scene_id': 'scene', 'part': 'a', 'confirm_send': True, 'automatic': True,
        'selection_token': 'token', 'prepared_request_id': report['request_id']}
    if pipeline:
        body.pop('prepared_request_id')
        body['native_pipeline']=True
    with patch('local_engine.flow_task_tracker.FlowTaskTracker', FixtureTimer):
        await service.submit(body)
        if mode == 'stop':
            await until(lambda: service.lookup(body['request_id'])['phase'] == 'generating')
            await service.stop()
        else:
            await asyncio.wait_for(service.task, 20)
    record = service.lookup(body['request_id'])
    assert await page.evaluate('window.sent') == (0 if native else 1)
    if pipeline:
        assert counts['warmup']==4 and counts['upload']==1, (record,counts)
        if mode in ('upload_rejected','upload_transport_error','wrong_image_project','account_changed','project_changed'):
            assert record['state']=='failed' and not service.sent and counts['generate']==0, record
            assert record['native_inputs']['upload_attempted'] is True
            assert not record['native_inputs']['generation_ready']
            assert counts['upload']==1
            await service.submit(body)
            assert counts['upload']==1
            await context.close()
            return counts
    if mode in ('missing_id', 'missing_key'):
        assert record['state'] == 'failed' and counts == {'generate':0,'status':0,'detail':0,'download':0}, record
        assert not service.sent
        assert not await page.evaluate('Object.keys(window).some(k=>k.startsWith("__sfNativeReference_"))')
        await context.close()
        return counts
    assert counts['generate'] == (2 if mode == 'ambiguous' else 1), counts
    assert record['progress'] is None and record['progress_source'] is None, record
    if mode in ('success','rpc_lines_success'):
        assert record['state'] == 'done' and record['submitted'] is True, record
        result = record['result']
        assert result['provider_identity'] == {'media_id': VIDEO, 'project_id': PROJECT, 'workflow_id': WORKFLOW}
        assert result['scene_id'] == 'scene' and result['part'] == 'a'
        assert (service.root / result['file']).read_bytes() == movie.read_bytes()
        assert counts['detail'] == counts['download'] == 1
    elif mode == 'failed':
        assert record['state'] == 'failed' and record['submitted'] is True, record
        assert record['provider_task']['state'] == 'failed' and counts['detail'] == 0
    else:
        assert record['state'] == 'unknown' and record['result'] is None, record
        if mode in ('ambiguous', 'unlinked'):
            assert not record['provider_task']['association_confirmed'] and counts['download'] == 0
        if mode in ('wrong_video', 'read_error'):
            assert record['provider_task']['read_failures'] == 3 and counts['detail'] == 0
        if mode == 'download_error':
            assert counts['download'] == 1 and not service.ledger.metadata(body['request_id'])['provider_video_downloaded']
        if mode=='rpc_rejected':
            assert record['provider_task']['state']=='rpc_rejected'and record['phase']=='submit_rejected'
            assert 'PUBLIC_ERROR_UNUSUAL_ACTIVITY'in record['message']
            assert counts['status']==counts['download']==0
    assert not service.task_trackers and not service.network_probes
    exported = json.dumps(record) + json.dumps(service.diagnose(body['request_id']))
    assert SECRET not in exported and 'signature=' not in exported
    assert 'PRIVATE_NATIVE_TOKEN' not in exported
    # Lookup/repeat of exactly the same local request must not send again.
    again = await service.submit(body)
    assert again['state'] == record['state'] and counts['generate'] == (2 if mode == 'ambiguous' else 1)
    assert service.diagnose(body['request_id'])['can_retry'] is False
    await context.close()
    return counts


async def main():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        movie = root / 'fixture.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=90x160:d=8',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-y', str(movie)], check=True)
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            try:
                for mode in (sys.argv[1:] or ('success', 'failed', 'unlinked', 'ambiguous', 'wrong_video', 'read_error', 'download_error', 'stop')):
                    counts = await scenario(browser, root / mode, movie, mode)
                    print('PASS', mode, counts, flush=True)
            finally:
                await browser.close()
    print('PASS: intercepted schema fixtures only; no Google requests or paid generation.')


if __name__ == '__main__':
    asyncio.run(main())
