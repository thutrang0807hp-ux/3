"""One ledger grant -> one private UI worker. Never falls back to direct RPC."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import sys


async def generate(service, rid, payload, reference):
    from .simple_flow import SimpleStopped
    from .google_login import flow_profile_path, installed_browser
    from .flow_gflow_runtime import ensure_runtime
    prepared = getattr(service, 'pair_report', None) or {}
    project = prepared.get('uploaded_media_project')
    if (prepared.get('request_id') != payload.get('prepared_request_id') or
            any(prepared.get(key) != payload.get(key) for key in ('room_id', 'scene_id', 'part', 'account_id')) or
            prepared.get('preparation_method') != 'native_reference_pipeline' or
            prepared.get('native_stage') != 'ready' or not prepared.get('reference_verified') or
            prepared.get('uploaded_media_source_sha256') != hashlib.sha256(reference.read_bytes()).hexdigest() or
            prepared.get('prompt_sha256') != hashlib.sha256(payload['prompt'].strip().encode()).hexdigest() or
            not isinstance(project, str) or not re.fullmatch(r'[a-fA-F0-9-]{36}', project)):
        raise SimpleStopped('Đầu vào đã chuẩn bị không khớp lượt tạo; chưa gửi video.')
    if sys.platform != 'win32':
        raise SimpleStopped('Engine Flow tích hợp hiện chỉ hỗ trợ bản Windows.')
    bridge = service.account_bridge
    binding = bridge.binding(payload['account_id']) if bridge else None
    if not binding:
        raise SimpleStopped('Phiên tài khoản Flow đã chọn không còn dùng được; chưa gửi tạo.')
    profile = flow_profile_path(service.data, binding.get('profile_key')).resolve()
    if not profile.is_dir():
        raise SimpleStopped('Không tìm thấy profile Flow đã đăng nhập; chưa gửi tạo.')
    def check_binding():
        current = bridge.binding(payload['account_id'])
        selected = bridge.selection()
        if (not current or not selected.get('available') or selected.get('account_id') != payload['account_id']
                or current.get('profile_key') != binding.get('profile_key') or current['email'] != binding['email']):
            raise SimpleStopped('Tài khoản Flow đã thay đổi; dừng lượt và không tự gửi lại.')
    check_binding()
    service.phase(rid, 'engine_setup', 'Đang chuẩn bị engine Flow tích hợp; lần đầu tự tải thành phần cần thiết.')
    python = await asyncio.to_thread(ensure_runtime, service.data)
    check_binding()
    # Release our old owner before the private worker opens this same profile.
    await service.disconnect_browser()
    output = service.root / (rid + '.engine')
    output.mkdir(exist_ok=True)
    spec = {'profile': str(profile), 'browser': str(installed_browser()),
            'expected_email': binding['email'], 'image': str(reference.resolve()),
            'output': str(output.resolve()), 'prompt': payload['prompt'],
            'project_id': project, 'reference_name': prepared['request_id'] + reference.suffix}
    worker = Path(__file__).with_name('flow_gflow_worker.py')
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('PYTHON', 'GFLOW_', 'VEO3_'))}
    home = service.data / 'flow-engine' / 'state'
    home.mkdir(parents=True, exist_ok=True)
    env.update(PYTHONNOUSERSITE='1', PYTHONUTF8='1', GFLOW_CLI_BROWSER_ENGINE='playwright',
               GFLOW_CLI_HOME=str(home.resolve()), GFLOW_CLI_INCIDENT_CAPTURE='false',
               GFLOW_CLI_TRANSPORT='ui_automation')
    process = await asyncio.create_subprocess_exec(str(python), str(worker),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL, env=env, limit=65536,
        creationflags=0x08000000, cwd=str(home.resolve()))
    async def command(value):
        process.stdin.write((json.dumps(value) + '\n').encode())
        await process.stdin.drain()
    identity = None
    granted = False
    complete = None
    def ids(event):
        values = {key: event.get(key) for key in ('media_id', 'project_id', 'workflow_id')}
        if any(value is not None and (not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_./:-]{1,512}', value)) for value in values.values()):
            raise SimpleStopped('Engine trả định danh không hợp lệ; giữ lượt để kiểm tra.')
        if not values['media_id'] or values['project_id'] != project:
            raise SimpleStopped('Engine chưa ghi đủ định danh clip; không tự tạo lại.')
        return values
    try:
        await command(spec)
        service.phase(rid, 'opening', 'Đang mở Flow bằng tài khoản đã chọn trong SceneForge.')
        async with asyncio.timeout(900):
            while line := await process.stdout.readline():
                event = json.loads(line)
                check_binding()
                kind = event.get('event')
                if kind == 'ready':
                    if granted or event.get('engine_version') != '0.92.1':
                        raise SimpleStopped('Sai trạng thái engine Flow; không gửi lại.')
                    # Durable ambiguity boundary must succeed BEFORE granting the worker.
                    service.ledger.set_metadata(rid, {'clicked': True, 'engine': 'gflow-ui-0.92.1', 'generation_granted': True})
                    service.sent = True
                    granted = True
                    prepared.update(generation_submitted=True, generation_ready=False,
                                    native_stage='generation_granted', state='submitted')
                    service.ledger.set_metadata(rid, {'native_inputs': dict(prepared)})
                    service.phase(rid, 'submitting', 'Đang tải ảnh và gửi một lượt tạo qua giao diện Flow.')
                    await command({'action': 'generate'})
                elif kind == 'started':
                    if not granted or identity is not None:
                        raise SimpleStopped('Sai thứ tự tác vụ Flow; không tự gửi lại.')
                    identity = ids(event)
                    service.ledger.set_metadata(rid, {'provider_task': {**identity, 'association_confirmed': True, 'source': 'gflow_ui'}})
                    service.phase(rid, 'waiting', 'Flow đã trả ID video; đang chờ kết quả và tải về cảnh.')
                elif kind == 'complete':
                    if not granted or identity is None or ids(event) != identity:
                        raise SimpleStopped('Kết quả không khớp tác vụ đã ghi nhận; không tạo lại.')
                    candidate = Path(event['file']).resolve()
                    if not candidate.is_relative_to(output.resolve()) or not candidate.is_file():
                        raise SimpleStopped('Đường dẫn kết quả Flow không hợp lệ.')
                    complete = candidate
                elif kind in ('error', 'generation_failed'):
                    codes = event.get('public_error_codes', [])
                    safe = [code for code in codes if isinstance(code, str) and re.fullmatch(r'PUBLIC_ERROR_[A-Z0-9_]{1,100}', code)]
                    reason = {'engine_version_mismatch': 'Sai phiên bản engine Flow.',
                              'profile_or_image_missing': 'Thiếu profile hoặc ảnh đầu vào.',
                              'browser_missing': 'Không tìm thấy trình duyệt đã cài.',
                              'account_identity_unverified': 'Chưa xác minh được đúng tài khoản Flow đã chọn.'}.get(event.get('error_code'), 'Engine Flow dừng.')
                    raise SimpleStopped(reason + (' ' + ', '.join(safe) if safe else '') + ' Không tự gửi lại.')
                else:
                    raise SimpleStopped('Phản hồi engine Flow không hợp lệ.')
            if await process.wait() != 0 or complete is None:
                raise SimpleStopped('Engine Flow kết thúc trước khi xác minh được video. Không tự gửi lại.')
        path = await service.validate_video(rid, complete, complete.suffix)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        result = {'file': path.name, 'mime_type': 'video/webm' if path.suffix == '.webm' else 'video/mp4',
                  'sha256': digest, 'bytes': path.stat().st_size, 'model': payload['model'],
                  'kind': 'video', 'origin': 'flow', 'cost': None, 'provider_identity': identity,
                  **{key: payload[key] for key in ('account_id', 'room_id', 'scene_id', 'part')}}
        service.phase(rid, 'complete', 'Đã nhận video về đúng cảnh.')
        service.ledger.finish(rid, 'done', result)
        try:
            service.vault.set_secret('gflow-ui-verified', True)
        except Exception:
            pass  # Optional capability badge cannot invalidate a saved result.
        service.state = 'ready'
        service.message = 'Đã lưu video; node sẽ nhận về đúng cảnh.'
    finally:
        if process.returncode is None:
            try:
                await command({'action': 'cancel'})
                await asyncio.wait_for(process.wait(), 10)
            except (BrokenPipeError, ConnectionResetError, asyncio.TimeoutError):
                if process.returncode is None:
                    process.kill()
                await process.wait()
        if process.stdin:
            process.stdin.close()
