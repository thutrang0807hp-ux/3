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


def command(repo, reference, prompt, project, output, profile='default', settings=None):
    from .flow_video_options import normalize_settings, MODELS
    cfg=normalize_settings(settings)
    repo=Path(repo);python=repo/'runtime/python.exe'
    mode='r2v' if cfg['mode']=='ingredients' else 'i2v'
    args=[str(python) if python.is_file() else 'py','-m','gflow_cli','video',mode]
    if mode=='r2v':args+=['--ref',str(reference)]
    args+=['--aspect',cfg['ratio'],'--model',MODELS[cfg['model']],'--count','1',
           '--project',project,'--profile',profile,'--out-dir',str(output),'--json','--']
    if mode=='i2v':args.append(str(reference))
    return args+[prompt]


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
        if isinstance(value, dict) and value.get('command') in ('video r2v','video i2v') and 'succeeded' in value:
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
    project = prepared.get('project_id') or prepared.get('uploaded_media_project')
    source_hash = prepared.get('reference_sha256') if prepared.get('preparation_method') == 'cli_reference_pipeline' else prepared.get('uploaded_media_source_sha256')
    if (prepared.get('request_id') != payload.get('prepared_request_id') or
            not re.fullmatch(r'[a-fA-F0-9-]{36}', str(project)) or
            source_hash != hashlib.sha256(reference.read_bytes()).hexdigest()):
        raise SimpleStopped('Ảnh/dự án đã chuẩn bị không khớp; chưa gọi CLI.')
    await service.assert_ready()
    await service.disconnect_browser()
    output = (service.root / (rid + '.cli')).resolve()
    output.mkdir(exist_ok=True)
    # CLI R2V uploads this single local reference; no native pre-upload.
    image = output / (prepared['request_id'] + reference.suffix)
    shutil.copyfile(reference, image)
    from .flow_video_options import request_settings
    cfg=request_settings(payload)
    if prepared.get('preparation_method')=='cli_reference_pipeline' and prepared.get('settings')!=cfg:
        raise SimpleStopped('Cấu hình đã đổi sau chuẩn bị; chưa gửi CLI.')
    args = command(repo, image, payload['prompt'], project, output, profile, cfg)
    env = dict(os.environ, GFLOW_CLI_UPDATE_CHECK='0', NO_COLOR='1', TERM='dumb', PYTHONUTF8='1')
    # Same environment as MO-UNG-DUNG.bat when the supplied app is portable.
    if (repo / 'runtime' / 'python.exe').is_file():
        env.pop('PYTHONHOME', None)
        env.pop('PYTHONPATH', None)
        env['PYTHONNOUSERSITE'] = '1'
        env['GFLOW_CLI_HOME'] = str(repo / 'data' / 'profiles')
    service.ledger.set_metadata(rid, {'engine': 'gflow-cli-direct', 'clicked': True,
        'generation_granted': True, 'cli': {'cwd': str(repo), 'entrypoint': '-m gflow_cli video '+('r2v' if cfg['mode']=='ingredients' else 'i2v'), 'profile': profile}})
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
            media = recovery_media(logs)
            if media:
                path, identity = await download_existing(service,rid,repo,profile,env,output,media,project,payload['prompt'])
                await finish_video(service,rid,payload,path,identity)
                return
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
        await finish_video(service,rid,payload,path,identity)
    finally:
        if process.returncode is None:
            process.kill()
            await process.communicate()


def recovery_media(logs):
    """Only the CLI's download-error recommendation identifies a recoverable clip."""
    if logs.get('exit_code') != 6:
        return None
    text = str(logs.get('stdout', '')) + '\n' + str(logs.get('stderr', ''))
    if 'MediaDownloadError' not in text:
        return None
    found = set(re.findall(r'gflow\s+data\s+download\s+([a-fA-F0-9]{8}-(?:[a-fA-F0-9]{4}-){3}[a-fA-F0-9]{12})(?![a-fA-F0-9-])', text))
    return next(iter(found)).lower() if len(found) == 1 else None


async def download_existing(service, rid, repo, profile, env, output, media, project, prompt):
    from .simple_flow import SimpleStopped
    identity = {'media_id': media, 'project_id': project, 'workflow_id': None}
    inputs = dict(service.ledger.metadata(rid).get('native_inputs') or {})
    inputs.update(generation_submitted=True, generation_ready=False, native_stage='video_ready_downloading', state='submitted')
    service.ledger.set_metadata(rid, {'native_inputs': inputs, 'provider_task': {**identity, 'association_confirmed': True,
        'source': 'gflow_cli_download_error', 'state': 'downloading'}})
    service.phase(rid, 'downloading', 'Video đã tạo xong; đang tải lại đúng ID bằng CLI, không tạo video mới.')
    python = repo / 'runtime' / 'python.exe'
    args = [str(python) if python.is_file() else 'py', '-m', 'gflow_cli', 'data', 'download',
            media, '--profile', profile, '--out', str(output), '--json']
    options = {'creationflags': 0x08000000} if os.name == 'nt' else {}
    process = await asyncio.create_subprocess_exec(*args, cwd=str(repo), env=env,
        stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, **options)
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), 180)
        text = stdout.decode('utf-8', errors='replace')
        service.ledger.set_metadata(rid, {'cli_download_diagnostics': {'exit_code': process.returncode,
            'stdout': safe_log(text, prompt), 'stderr': safe_log(stderr.decode('utf-8', errors='replace'), prompt)}})
        if process.returncode:
            raise SimpleStopped('Video đã có ID nhưng CLI tải lại vẫn lỗi '+str(process.returncode)+'. Không tạo lại video; có thể kiểm tra tải clip cũ.')
        values = []
        for match in re.finditer(r'(?m)^\s*\{', text):
            try: value, _ = json.JSONDecoder().raw_decode(text[match.end()-1:])
            except ValueError: continue
            if isinstance(value, dict) and 'path' in value and 'media_id' in value:values.append(value)
        if len(values) != 1 or values[0].get('media_id') != media or values[0].get('project_id') != project or values[0].get('profile') != profile:
            raise SimpleStopped('Kết quả tải CLI không khớp video/dự án/tài khoản cũ; chưa nhập.')
        path = Path(values[0]['path']).resolve()
        if not path.is_relative_to(output.resolve()) or not path.is_file():
            raise SimpleStopped('Đường dẫn clip tải lại không hợp lệ.')
        identity['workflow_id'] = values[0].get('workflow_id')
        return path, identity
    finally:
        if process.returncode is None:
            process.kill();await process.communicate()


async def finish_video(service, rid, payload, path, identity):
    from .simple_flow import SimpleStopped
    from .flow_video_options import request_settings
    output = (service.root / (rid + '.cli')).resolve()
    if not path.is_file() or not path.resolve().is_relative_to(output):
        raise SimpleStopped('Tệp CLI trả về không nằm trong thư mục kết quả của lượt này.')
    path = await service.validate_video(rid, path, path.suffix)
    saved = {'file': path.name, 'mime_type': 'video/webm' if path.suffix == '.webm' else 'video/mp4',
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size,
        'kind': 'video', 'model': payload['model'], 'settings': request_settings(payload), 'origin': 'flow', 'cost': None,
        'provider_identity': identity, **{key: payload[key] for key in ('account_id','room_id','scene_id','part')}}
    inputs = dict(service.ledger.metadata(rid).get('native_inputs') or {})
    inputs.update(generation_submitted=True, generation_ready=False, native_stage='generation_completed', state='completed')
    if inputs.get('preparation_method') == 'cli_reference_pipeline':
        inputs.update(delivered=True, reference_verified=True, reference_evidence='cli_single_reference_completed')
    service.ledger.set_metadata(rid, {'native_inputs': inputs, 'provider_task': {**identity, 'association_confirmed': True, 'source': 'gflow_cli', 'state': 'complete'}})
    service.phase(rid, 'complete', 'Đã nhận video về đúng cảnh.')
    service.ledger.finish(rid, 'done', saved)
    try: service.vault.set_secret('gflow-cli-verified', True)
    except Exception: pass
    service.state = 'ready';service.message = 'Đã nhận video từ CLI gốc.'


async def recover_existing(service, rid):
    """Existing report/check action may download an old clip; never calls video r2v."""
    from .simple_flow import SimpleStopped
    async with service.gate:
        meta = service.ledger.metadata(rid)
        if service.busy() or service.lookup(rid)['state'] != 'unknown' or meta.get('engine') != 'gflow-cli-direct':return
        media = (meta.get('provider_task') or {}).get('media_id') or recovery_media(meta.get('engine_diagnostics') or {})
        if not media:return
        selection = service.account_bridge.selection()
        binding = service.account_bridge.binding(meta.get('account_id'))
        if not binding or not selection.get('available') or selection.get('account_id') != meta.get('account_id'):return
        inputs = meta.get('native_inputs') or {}
        project = inputs.get('project_id') or inputs.get('uploaded_media_project')
        repo = Path((meta.get('cli') or {}).get('cwd', ''))
        profiles = matching_profile(repo, binding['email']) if repo.is_dir() else []
        if len(profiles) != 1 or not re.fullmatch(r'[a-fA-F0-9-]{36}', str(project)):return
        output = (service.root / (rid + '.cli')).resolve();output.mkdir(exist_ok=True)
        env = dict(os.environ, GFLOW_CLI_UPDATE_CHECK='0', NO_COLOR='1', TERM='dumb', PYTHONUTF8='1')
        if (repo/'runtime/python.exe').is_file():
            env.pop('PYTHONHOME', None);env.pop('PYTHONPATH', None)
            env.update(PYTHONNOUSERSITE='1', GFLOW_CLI_HOME=str(repo/'data/profiles'))
        old_task, old_active = service.task, service.active
        service.task = asyncio.current_task();service.active = rid
        try:
            await service.disconnect_browser()
            path, identity = await download_existing(service,rid,repo,profiles[0],env,output,media,project,meta.get('prompt',''))
            await finish_video(service,rid,meta,path,identity)
        except Exception as exc:
            message = str(exc) if isinstance(exc,SimpleStopped) else 'Tải clip cũ dừng: '+type(exc).__name__+'. Không tạo lại.'
            service.ledger.set_metadata(rid,{'message':message});service.state='unknown';service.message=message
        finally:
            service.task, service.active = old_task, old_active
