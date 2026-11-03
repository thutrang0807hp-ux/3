"""Call the user's existing gflow CLI. No SDK imports or session overrides."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

# Set to the user's actual existing repo/portable directory once provided.
REPO_DIRECTORY = ''
APP_SHA256 = 'ab86f1fc7687971bf48e312c8f92cff6d1be178dbee836a7dd9e579f1a11cce4'


def find_repo(downloads):
    """Find the supplied application, not an arbitrary executable in Downloads."""
    found = set()
    pending = [(Path(root), 0) for root in downloads]
    examined = 0
    while pending and examined < 500:
        folder, depth = pending.pop(0)
        examined += 1
        for app in (folder / 'app.py', folder / 'app' / 'app.py'):
            try:
                if app.stat().st_size < 200000 and hashlib.sha256(app.read_text(encoding='utf-8-sig').encode()).hexdigest() == APP_SHA256:
                    found.add(folder.resolve())
            except (OSError, UnicodeError):
                pass
        if depth < 3:
            try:
                pending.extend((item, depth+1) for item in folder.iterdir()
                    if item.is_dir() and not item.is_symlink() and item.name.lower() not in
                    ('runtime', 'app', 'data', '.data', 'out', 'node_modules', '.git', '.venv'))
            except OSError:
                pass
    # app/app.py also appears as a root candidate; use the portable root.
    return sorted((path for path in found if not (path.name == 'app' and path.parent in found)), key=str)


def downloads_folders():
    values = [Path.home() / 'Downloads']
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
                value, _ = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')
                values.insert(0, Path(os.path.expandvars(value)))
        except OSError:
            pass
    return values


def matching_profile(repo, email):
    if (repo / 'runtime' / 'python.exe').is_file():
        home = repo / 'data' / 'profiles'
    else:
        home = Path(os.environ.get('GFLOW_CLI_HOME') or str(Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'ffroliva' / 'gflow-cli'))
    matches = []
    for folder in home.glob('profile_*'):
        try: actual = (folder / '.gflow_account').read_text(encoding='utf-8').strip().casefold()
        except (OSError, UnicodeError): continue
        if actual == email.casefold():
            name = folder.name[len('profile_'):]
            if re.fullmatch(r'[A-Za-z0-9_-]{1,64}', name): matches.append(name)
    return matches


def command(repo, reference, prompt, project, output, profile='default'):
    repo = Path(repo)
    python = repo / 'runtime' / 'python.exe'
    return [str(python) if python.is_file() else 'py', '-m', 'gflow_cli',
            'video', 'r2v', '--ref', str(reference), '--aspect', '9:16',
            '--model', 'veo-lite', '--count', '1',
            '--project', project, '--profile', profile, '--out-dir', str(output), '--json', '--', prompt]


def safe_log(value, prompt):
    value = value.replace(prompt, '<prompt>') if prompt else value
    value = re.sub(r'(?i)\b(?:Bearer|SAPISIDHASH)\s+\S+', '<secret>', value)
    value = re.sub(r'(?im)^.*(?:cookie|authorization|recaptcha|access_token|refresh_token|session.token).*$', '<secret>', value)
    value = re.sub(r'(?i)https?://\S+', '<url>', value)
    return value[-16000:]


def video_result(stdout):
    decoder = json.JSONDecoder()
    matches = []
    for match in re.finditer(r'(?m)^\s*\{', stdout):
        try: value, _ = decoder.raw_decode(stdout[match.end()-1:])
        except ValueError: continue
        if isinstance(value, dict) and value.get('command') == 'video r2v' and 'succeeded' in value:
            matches.append(value)
    if len(matches) != 1:
        raise ValueError('CLI did not return exactly one video result')
    return matches[0]


async def generate(service, rid, payload, reference):
    from .simple_flow import SimpleStopped
    repo_value = REPO_DIRECTORY or os.environ.get('SCENEFORGE_GFLOW_REPO')
    candidates = [Path(repo_value)] if repo_value else await asyncio.to_thread(find_repo, downloads_folders())
    binding = service.account_bridge.binding(payload['account_id'])
    if not binding: raise SimpleStopped('Tài khoản đã chọn không còn hợp lệ; chưa gọi CLI.')
    matched = [(path, name) for path in candidates if path.is_dir() for name in matching_profile(path, binding['email'])]
    if len(matched) != 1:
        raise SimpleStopped('Tìm thấy '+str(len(candidates))+' bản GFlow trong Downloads nhưng chưa xác định duy nhất phiên đúng tài khoản đã chọn. Chưa gọi CLI.')
    repo, profile = matched[0]
    repo = repo.resolve()
    prepared = service.pair_report or {}
    project = prepared.get('uploaded_media_project')
    if (prepared.get('request_id') != payload.get('prepared_request_id') or
            not re.fullmatch(r'[a-fA-F0-9-]{36}', str(project)) or
            prepared.get('uploaded_media_source_sha256') != hashlib.sha256(reference.read_bytes()).hexdigest()):
        raise SimpleStopped('Ảnh/dự án đã chuẩn bị không khớp; chưa gọi CLI.')
    await service.assert_ready()
    await service.disconnect_browser()
    output = (service.root / (rid + '.cli')).resolve()
    output.mkdir(exist_ok=True)
    # Match the filename already uploaded, letting the original CLI reuse it.
    image = output / (prepared['request_id'] + reference.suffix)
    shutil.copyfile(reference, image)
    args = command(repo, image, payload['prompt'], project, output, profile)
    env = dict(os.environ, GFLOW_CLI_UPDATE_CHECK='0', NO_COLOR='1', TERM='dumb', PYTHONUTF8='1')
    # Same environment as MO-UNG-DUNG.bat when the supplied app is portable.
    if (repo / 'runtime' / 'python.exe').is_file():
        env.pop('PYTHONHOME', None)
        env.pop('PYTHONPATH', None)
        env['PYTHONNOUSERSITE'] = '1'
        env['GFLOW_CLI_HOME'] = str(repo / 'data' / 'profiles')
    service.ledger.set_metadata(rid, {'engine': 'gflow-cli-direct', 'clicked': True,
        'generation_granted': True, 'cli': {'cwd': str(repo), 'entrypoint': '-m gflow_cli video r2v'}})
    service.sent = True
    service.phase(rid, 'submitting', 'Đang chạy CLI gốc để tạo video, chờ và tải kết quả.')
    options = {'creationflags': 0x08000000} if os.name == 'nt' else {}
    try:
        process = await asyncio.create_subprocess_exec(*args, cwd=str(repo), env=env,
            stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, **options)
    except OSError as exc:
        service.sent = False
        service.ledger.set_metadata(rid, {'clicked': False, 'generation_granted': False,
            'engine_diagnostics': {'error_type': type(exc).__name__, 'detail': safe_log(str(exc), payload['prompt'])}})
        raise SimpleStopped('Không khởi chạy được CLI gốc: '+type(exc).__name__+'. Chưa gửi tạo.') from None
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), 1200)
        stdout = stdout.decode('utf-8', errors='replace')
        stderr = stderr.decode('utf-8', errors='replace')
        logs = {'exit_code': process.returncode, 'stdout': safe_log(stdout, payload['prompt']),
                'stderr': safe_log(stderr, payload['prompt'])}
        service.ledger.set_metadata(rid, {'engine_diagnostics': logs})
        if process.returncode:
            raise SimpleStopped('CLI gốc dừng, mã thoát '+str(process.returncode)+'. stdout và stderr đã ghi trong báo cáo; không tự tạo lại.')
        try: result = video_result(stdout)
        except ValueError as exc: raise SimpleStopped(str(exc)) from None
        media = result.get('media_id')
        if result.get('succeeded') is not True or not re.fullmatch(r'[a-fA-F0-9-]{36}', str(media)):
            raise SimpleStopped('CLI chưa xác nhận video thành công; không tự tạo lại.')
        identity = {'media_id': media, 'project_id': project, 'workflow_id': None}
        service.ledger.set_metadata(rid, {'provider_task': {**identity, 'association_confirmed': True, 'source': 'gflow_cli'}})
        prepared.update(generation_submitted=True, generation_ready=False, native_stage='generation_completed', state='completed')
        service.ledger.set_metadata(rid, {'native_inputs': dict(prepared)})
        path = Path(result.get('local_path') or '').resolve()
        if not path.is_file() or not path.is_relative_to(output):
            raise SimpleStopped('Tệp CLI trả về không nằm trong thư mục kết quả của lượt này.')
        path = await service.validate_video(rid, path, path.suffix)
        saved = {'file': path.name, 'mime_type': 'video/webm' if path.suffix == '.webm' else 'video/mp4',
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size,
            'kind': 'video', 'model': payload['model'], 'origin': 'flow', 'cost': None,
            'provider_identity': identity, **{key: payload[key] for key in ('account_id','room_id','scene_id','part')}}
        service.phase(rid, 'complete', 'CLI đã trả video về đúng cảnh.')
        service.ledger.finish(rid, 'done', saved)
        try: service.vault.set_secret('gflow-cli-verified', True)
        except Exception: pass
        service.state = 'ready'
        service.message = 'Đã nhận video từ CLI gốc.'
    finally:
        if process.returncode is None:
            process.kill()
            await process.communicate()
