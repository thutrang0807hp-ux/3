"""Native-session project/upload pipeline for ONE SceneForge scene.

Uses the existing AccountWebSession and RequestLedger; no second account store,
profile or generation authority. Authentication remains inside the normal page.
No Phoma preload, challenge interception, fingerprint patches or token export.
"""
import asyncio
from .flow_batch_session import batch_script, CONTEXT_JS
import base64
import hashlib
import json
import secrets
from urllib.parse import urlsplit

from .flow_native_reference import PREFLIGHT, discard
from .flow_settings import DEFAULTS
from .flow_task_protocol import UUID, FlowRpcRejected, UnsupportedFlowPayload, rpc_payload, project_from_url


METHODS = ('jHPbke', 'NfrxTb', 've2Lsc', 'DTaVef', 'nzlxg', 'maseQ', 'as29s')
WARMUP = (('NfrxTb', [14]), ('ve2Lsc', []), ('DTaVef', [1]), ('nzlxg', []))


class NativePipelineStopped(RuntimeError):
    pass


RPC = batch_script('bootstrap')


def unique_id(payload, *, excluded=()):
    """Bounded, unambiguous ID from a specific project-creation response only."""
    found = set()
    budget = 500
    def walk(value, depth=0):
        nonlocal budget
        budget -= 1
        if budget < 0 or depth > 10:
            raise UnsupportedFlowPayload('project_response_limit')
        if isinstance(value, str) and UUID.fullmatch(value) and value not in excluded:
            found.add(value)
        elif isinstance(value, list):
            for child in value:
                walk(child, depth + 1)
    walk(payload)
    if len(found) != 1:
        raise UnsupportedFlowPayload('project_identity_ambiguous_or_missing')
    return found.pop()


def upload_identity(payload, project):
    """Phoma V0's exact maseQ response slot, not an arbitrary UUID scan."""
    if (not isinstance(payload, list) or not payload or
        not isinstance(payload[0], list) or not payload[0] or
        not isinstance(payload[0][0], str) or not UUID.fullmatch(payload[0][0]) or
        payload[0][0] == project):
        raise UnsupportedFlowPayload('upload_media_identity_shape')
    return payload[0][0]


def image_resolved(payload, media, project):
    """Resolve only the exact image requested; never accept another media ID.

    Detail envelope layouts observed in the supplied code: flat asset or a
    single asset row at index 2/3. URL is checked in memory, never persisted.
    """
    candidates = []
    if isinstance(payload, list) and len(payload) >= 2 and payload[0] == media:
        candidates.append(payload)
    for index in (2, 3):
        if (isinstance(payload, list) and len(payload) > index and
            isinstance(payload[index], list) and len(payload[index]) == 1 and
            isinstance(payload[index][0], list) and payload[index][0]):
            row = payload[index][0]
            if row[0] == media:
                candidates.append(row)
    if len(candidates) != 1:
        raise UnsupportedFlowPayload('reference_detail_identity_missing')
    row = candidates[0]
    if len(row) < 2 or row[1] != project:
        raise UnsupportedFlowPayload('reference_detail_project_mismatch')
    found = set()
    budget = 1500
    def walk(value, depth=0):
        nonlocal budget
        budget -= 1
        if budget < 0 or depth > 12:
            raise UnsupportedFlowPayload('reference_detail_limit')
        if isinstance(value, str) and len(value) <= 16384:
            try:
                url = urlsplit(value)
                if (url.scheme == 'https' and url.hostname == 'flow-content.google' and
                    url.port in (None, 443) and not url.username and not url.password and
                    not url.fragment and url.path == '/image/' + media):
                    found.add(value)
            except ValueError:
                pass
        elif isinstance(value, list):
            for child in value:
                walk(child, depth + 1)
    walk(row)
    if len(found) != 1:
        raise UnsupportedFlowPayload('reference_image_url_missing_or_ambiguous')
    return True


class NativeProjectSession:
    def __init__(self, page, check):
        self.page, self.check = page, check

    async def ready(self):
        await self.check()
        try:
            project = None if urlsplit(self.page.url).path == '/' else project_from_url(self.page.url)
            await self.page.wait_for_function('project => {\n'+CONTEXT_JS+
                '\nreturn !contextFor(project,true).error;\n}', arg=project, timeout=15000)
        except Exception:
            raise NativePipelineStopped('Phiên Flow chưa nạp đủ metadata RPC; chưa upload hoặc gửi tạo.') from None
        await self.check()

    async def rpc(self, method, project, payload, *, upload=None, key=None):
        if method not in METHODS:
            raise ValueError('native_method_denied')
        await self.check()
        reply = await asyncio.wait_for(self.page.evaluate(RPC, {
            'method': method, 'project': project, 'payload': payload, 'upload': upload, 'key': key}), 35)
        if not isinstance(reply, dict) or reply.get('not_sent'):
            raise NativePipelineStopped('Phiên hoặc dự án đổi trước RPC '+method+'; không tự gửi lại.')
        if type(reply.get('status')) is not int or not isinstance(reply.get('body'), str):
            raise NativePipelineStopped('Chưa xác định kết quả RPC '+method+'; giữ lượt, không tự gửi lại.')
        if not 200 <= reply['status'] < 300:
            raise NativePipelineStopped('Flow trả HTTP '+str(reply['status'])+' cho RPC '+method+'. Không tự gửi lại.')
        try:
            result = rpc_payload(reply['body'], method, allow_empty=method in dict(WARMUP),
                                 allow_project_id=method == 'jHPbke')
        except FlowRpcRejected as exc:
            codes = exc.details.get('public_error_codes', [])
            suffix = ' · ' + ', '.join(codes) if codes else ' · mã RPC ' + str(exc.details.get('rpc_error_code', '?'))
            raise NativePipelineStopped('Flow từ chối RPC '+method+suffix+'. Không tự gửi lại.') from None
        except UnsupportedFlowPayload as exc:
            raise NativePipelineStopped('Chưa đọc được phản hồi RPC '+method+' ('+str(exc)+'). Không tự gửi lại.') from None
        await self.check()
        return result

    async def warmup(self, project):
        await self.ready()
        for method, payload in WARMUP:
            await self.rpc(method, project, payload)

    async def resolve(self, project, media, *, sleep=asyncio.sleep):
        for attempt in range(5):
            payload = await self.rpc('as29s', project, [media])
            try:
                return image_resolved(payload, media, project)
            except UnsupportedFlowPayload:
                if attempt == 4:
                    raise NativePipelineStopped('Ảnh đã có ID nhưng chi tiết ảnh chưa khớp ID/project hoặc chưa sẵn sàng. Chưa gửi tạo.') from None
                await sleep((attempt + 1) * .6)

    async def upload(self, project, raw, mime, filename, report, persist):
        key = '__sfNativeUpload_' + secrets.token_hex(12)
        await self.check()
        proof = await asyncio.wait_for(self.page.evaluate(PREFLIGHT, {
            'key': key, 'project': project, 'action': 'MEDIA_GENERATION'}), 12)
        if not isinstance(proof, dict) or proof.get('ready') is not True:
            code = proof.get('error', 'preflight_failed') if isinstance(proof, dict) else 'preflight_failed'
            raise NativePipelineStopped('Phiên chưa sẵn sàng upload trực tiếp ('+code+'). Chưa upload hoặc gửi tạo.')
        try:
            # Save ambiguity boundary before the only upload call. No upload retry.
            report.update(upload_attempted=True, upload_uncertain=True, native_stage='upload_dispatching')
            persist()
            payload = await self.rpc('maseQ', project, None, key=key,
                upload={'base64': base64.b64encode(raw).decode(), 'mime': mime, 'filename': filename})
            try:
                media = upload_identity(payload, project)
            except UnsupportedFlowPayload as exc:
                raise NativePipelineStopped('Upload đã trả phản hồi nhưng chưa có ID ảnh hợp lệ ('+str(exc)+'). Không tự upload lại.') from None
            report.update(uploaded_media_id=media, uploaded_media_project=project,
                uploaded_media_source_sha256=hashlib.sha256(raw).hexdigest(),
                uploaded_media_evidence='native_maseQ_response_slot_0_0',
                delivered=True, upload_uncertain=False, native_stage='upload_id_saved')
            persist()  # Save ID before any resolve/read.
            await self.resolve(project, media)
            return media
        finally:
            await discard(self.page, {'key': key})


async def ensure_native_project(session, vault, account, room, check):
    if not room:
        raise NativePipelineStopped('Chưa có phòng để gắn dự án Flow.')
    key = hashlib.sha256(json.dumps([account, room], separators=(',', ':')).encode()).hexdigest()
    records = vault.secret('flow-background-projects') or {}
    record = records.get(key)
    native = NativeProjectSession(session.page, check)
    if record:
        if record.get('account_id') != account or record.get('room_id') != room or record.get('state') != 'ready':
            raise NativePipelineStopped('Ánh xạ dự án cũ chưa rõ kết quả hoặc khác tài khoản/phòng; không tự tạo dự án khác.')
        url = record.get('url', '')
        project = project_from_url(url)
        if not UUID.fullmatch(project):
            raise NativePipelineStopped('ID dự án đã lưu không hợp lệ.')
    else:
        await native.ready()
        def save(value):
            # Re-read to preserve unrelated mappings created since attachment.
            rows = vault.secret('flow-background-projects') or {}
            rows[key] = {'account_id': account, 'room_id': room, **value}
            vault.set_secret('flow-background-projects', rows)
        save({'state': 'creating', 'creation_method': 'native_rpc'})
        try:
            payload = await native.rpc('jHPbke', None,
                ['projects/*', [None, ['SceneForge · ' + room]], [None, 22]])
            project = unique_id(payload)
            url = 'https://flow.google.com/project/' + project
            save({'state': 'ready', 'url': url, 'creation_method': 'native_rpc'})
        except BaseException:
            save({'state': 'unknown', 'creation_method': 'native_rpc'})
            raise
    await check()
    await session.page.goto(url, wait_until='domcontentloaded', timeout=60000)
    await check()
    if project_from_url(session.page.url) != project:
        raise NativePipelineStopped('Không mở được đúng dự án đã lưu; chưa upload hoặc gửi tạo.')
    await native.ready()


async def prepare_inputs(service, report, raw, mime, prompt, settings, check, *, on_persist=None, on_phase=None, upload_reference=True):
    if not upload_reference:
        from .flow_video_options import normalize_settings
        try:settings=normalize_settings(settings)
        except (ValueError,TypeError) as exc:raise NativePipelineStopped(str(exc)) from None
    elif settings != DEFAULTS:
        raise NativePipelineStopped('Bản thử một cảnh chỉ hỗ trợ Ingredients · Lite · 9:16 · x1.')
    if (not isinstance(raw, bytes) or not 0 < len(raw) <= 6 * 1024**2 or
        mime not in ('image/png','image/jpeg','image/webp') or
        not isinstance(prompt,str) or not prompt.strip() or len(prompt)>20000 or
        report.get('reference_sha256') != hashlib.sha256(raw).hexdigest() or
        report.get('prompt_sha256') != hashlib.sha256(prompt.strip().encode()).hexdigest()):
        raise NativePipelineStopped('Nguồn ảnh hoặc prompt không khớp cảnh; chưa upload hoặc gửi tạo.')
    project = project_from_url(service.page.url)
    report.update(preparation_method='native_reference_pipeline', native_stage='session',
        settings=dict(settings), settings_verified=True, reference_verified=False,
        generation_ready=False, prompt_verified=False, delivered=False, image_attached=False,
        prompt_filled=False, upload_attempted=False, logs=[], errors={})
    # The config above describes the RPC payload; it is NOT a DOM readback.
    report['settings_evidence'] = 'fixed_native_payload_config'
    def persist():
        path = service.root / (report['request_id'] + '.pair.json')
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(path)
        if on_persist:
            on_persist()
    try:
        native = NativeProjectSession(service.page, check)
        report.update(phase='native_session', message='Đang kiểm tra phiên và chuẩn bị workspace RPC; chưa gửi tạo.')
        if on_phase:on_phase('native_session',report['message'])
        persist()
        await native.warmup(project)
        if not upload_reference:
            await check()
            report.update(preparation_method='cli_reference_pipeline', project_id=project, settings_evidence='validated_cli_arguments',
                native_stage='cli_upload_pending', state='cli_inputs_ready', phase='complete',
                generation_ready=True, prompt_verified=True, prompt_evidence='bound_input_prompt_sha256',
                message='Đã kiểm tra ảnh nguồn, prompt và dự án. CLI sẽ upload một ảnh và tạo một video.')
            service.prepare_report = report
            persist()
            return
        report.update(phase='native_upload', message='Đang upload ảnh trực tiếp để nhận ID; chưa gửi tạo.')
        if on_phase:on_phase('native_upload',report['message'])
        persist()
        suffix={'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[mime]
        await native.upload(project, raw, mime, report['request_id'] + suffix, report, persist)
        await check()
        report.update(reference_verified=True, reference_evidence='upload_id_and_as29s_same_project',
            native_stage='ready', state='inputs_sent', phase='complete',
            prompt_verified=True, prompt_evidence='bound_input_prompt_sha256', generation_ready=True,
            message='Ảnh đã upload và xác minh theo ID. Prompt/cấu hình đã gắn với cảnh; sẵn sàng gửi một lần, chưa tạo video.')
        service.prepare_report = report
        persist()
    except BaseException as error:
        report.update(state='cancelled' if isinstance(error,asyncio.CancelledError) else 'failed',generation_ready=False,
            message=str(error) if isinstance(error,NativePipelineStopped) else 'Chuẩn bị đã dừng; chưa gửi tạo video.')
        persist()
        raise


async def validate_receipt(service, report):
    if report.get('preparation_method') == 'cli_reference_pipeline':
        from .flow_video_options import normalize_settings
        try:normalize_settings(report.get('settings'))
        except (ValueError,TypeError) as exc:raise NativePipelineStopped(str(exc)) from None
        if (not getattr(service, 'cli_driver_enabled', False) or
            report.get('native_stage') != 'cli_upload_pending' or report.get('upload_attempted') or
            report.get('project_id') != project_from_url(service.page.url)):
            raise NativePipelineStopped('Đầu vào CLI đã đổi dự án hoặc có upload khác; chưa gửi tạo.')
        await service.assert_ready()
        return
    if (report.get('settings') != DEFAULTS or not report.get('reference_verified') or
        report.get('native_stage') != 'ready' or not UUID.fullmatch(str(report.get('uploaded_media_id', ''))) or
        report.get('uploaded_media_project') != project_from_url(service.page.url) or
        report.get('uploaded_media_source_sha256') != report.get('reference_sha256')):
        raise NativePipelineStopped('Receipt ảnh trực tiếp chưa đầy đủ hoặc khác nguồn/project; chưa gửi tạo.')
    native = NativeProjectSession(service.page, service.assert_ready)
    await native.resolve(report['uploaded_media_project'], report['uploaded_media_id'])
