"""Call the user's existing gflow CLI. No SDK imports or session overrides."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

# Set to the user's actual existing repo/portable directory once provided.
REPO_DIRECTORY = ''
APP_SHA256 = 'ab86f1fc7687971bf48e312c8f92cff6d1be178dbee836a7dd9e579f1a11cce4'


def is_gflow_repo(folder):
    """Recognize the supplied app or an installed original CLI, without executing it."""
    folder=Path(folder)
    for app in (folder/'app.py',folder/'app/app.py'):
        try:
            if app.stat().st_size>500000:continue
            text=app.read_text(encoding='utf-8-sig')
            if hashlib.sha256(text.encode()).hexdigest()==APP_SHA256:return True
            # Updated portable app: original CLI entry point + actual installed module.
            modules=(folder/'runtime/Lib/site-packages/gflow_cli',folder/'gflow_cli',folder/'src/gflow_cli')
            requirements=folder/'requirements.txt'
            pinned=False
            try:pinned=bool(re.search(r'(?im)^gflow[-_]cli\s*==',requirements.read_text(encoding='utf-8')))
            except (OSError,UnicodeError):pass
            if 'gflow_cli' in text and 'subprocess' in text and (pinned or any((m/'__main__.py').is_file() for m in modules)):
                return True
        except (OSError,UnicodeError):pass
    return False


def find_repo(downloads):
    """Bounded search; app content may change between upstream releases."""
    found=set();pending=[(Path(root),0) for root in dict.fromkeys(downloads)];examined=0;seen=set()
    while pending and examined<3000:
        folder,depth=pending.pop(0)
        try:
            resolved=folder.resolve()
            if resolved in seen:continue
            seen.add(resolved)
            if is_gflow_repo(folder):
                found.add(resolved)
                continue
            examined+=1
            if depth<6:
                children=[item for item in folder.iterdir() if item.is_dir() and not item.is_symlink() and item.name.lower() not in
                    ('runtime','app','data','.data','out','node_modules','.git','.venv','venv','windows','program files','program files (x86)')]
                children.sort(key=lambda p:('gflow' not in p.name.lower() and '5gdfgfd' not in p.name.lower(),p.name.casefold()))
                pending.extend((item,depth+1) for item in children)
        except OSError:pass
    return sorted((path for path in found if not(path.name=='app' and path.parent in found)),key=str)


def downloads_folders():
    values=[Path.home()/'Downloads']
    if os.name=='nt':
        try:
            import winreg
            for subkey in ('User Shell Folders','Shell Folders'):
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Explorer'+ '\\'+subkey) as key:
                        value,_=winreg.QueryValueEx(key,'{374DE290-123F-4565-9164-39C4925E467B}')
                        values.insert(0,Path(os.path.expandvars(value)))
                except OSError:pass
        except ImportError:pass
    for name in ('USERPROFILE','OneDrive','OneDriveConsumer','OneDriveCommercial'):
        if os.environ.get(name):values.append(Path(os.environ[name])/'Downloads')
    values.extend((Path.cwd(),Path(sys.executable).parent,Path.home()/'Desktop'))
    return list(dict.fromkeys(values))


def remembered_repos(service,account):
    """Reuse recorded successful CLI locations, still checking selected email below."""
    values=[]
    try:
        for item in service.ledger.recent():
            if item.get('state')!='done':continue
            meta=service.ledger.metadata(item['id'])
            value=(meta.get('cli') or {}).get('cwd')
            if meta.get('account_id')==account and meta.get('engine')=='gflow-cli-direct' and isinstance(value,str) and value:
                values.append(Path(value))
    except AttributeError:pass  # Minimal test/adaptor ledgers may have no history API.
    return list(dict.fromkeys(values))


def resolve_repo(service,account,email):
    override=REPO_DIRECTORY or os.environ.get('SCENEFORGE_GFLOW_REPO')
    if override:
        candidates=[Path(override)] if Path(override).is_dir() else []
    else:
        # Most recent successful location wins only if its original app and account remain valid.
        for path in remembered_repos(service,account):
            installed=(path/'runtime/python.exe').is_file() and (path/'runtime/Lib/site-packages/gflow_cli/__main__.py').is_file()
            profiles=matching_profile(path,email) if is_gflow_repo(path) or installed else []
            if len(profiles)==1:return path,profiles[0],{'source':'successful_history','candidate_count':1}
        candidates=find_repo(downloads_folders())
    matched=[(path,name) for path in candidates if path.is_dir() for name in matching_profile(path,email)]
    if len(matched)!=1:
        from .simple_flow import SimpleStopped
        reason=('Không tìm thấy thư mục GFlow gốc. Khôi phục/giải nén bản GFlow đã chạy được vào Downloads hoặc đặt SCENEFORGE_GFLOW_REPO tới thư mục đó.' if not candidates else
                'Tìm thấy '+str(len(candidates))+' thư mục GFlow nhưng không xác định duy nhất profile đúng tài khoản đã chọn. Kiểm tra tài khoản trong GFlow gốc.')
        raise SimpleStopped(reason+' Chưa gọi CLI, chưa gửi tạo video.')
    return *matched[0],{'source':'configured_path' if override else 'folder_scan','candidate_count':len(candidates)}


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
    if not python.is_file() and (repo/'python.exe').is_file():python=repo/'python.exe'
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


def confirmed_generation_failure(logs, task, project):
    """A terminal CLI result must match the already associated video and project."""
    try:
        result = video_result(logs.get('stdout', ''))
    except (ValueError, TypeError):
        return None
    if (result.get('succeeded') is not False or
            result.get('generation_status') != 'MEDIA_GENERATION_STATUS_FAILED' or
            not re.fullmatch(r'[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}', str(result.get('media_id'))) or
            not re.fullmatch(r'[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}', str(project)) or
            not task or task.get('association_confirmed') is not True or
            task.get('media_id') != result['media_id'] or task.get('project_id') != project):
        return None
    return result


def record_generation_failure(service, rid, result):
    meta = service.ledger.metadata(rid)
    task = {**(meta.get('provider_task') or {}), 'state': 'failed', 'source': 'gflow_cli_terminal_result'}
    inputs = {**(meta.get('native_inputs') or {}), 'generation_submitted': True,
              'generation_ready': False, 'native_stage': 'generation_failed', 'state': 'failed'}
    message = ('CLI báo Flow tạo video thất bại (MEDIA_GENERATION_STATUS_FAILED). '
               'ID đã cấp không có nghĩa là video đã hoàn tất. Chưa có tệp video để tải; không tự tạo lại.')
    service.ledger.set_metadata(rid, {'provider_task': task, 'native_inputs': inputs,
        'provider_failure_evidence': {'media_id': result['media_id'], 'succeeded': False,
            'generation_status': result['generation_status'], 'source': 'cli_video_result'},
        'message': message, 'phase': 'failed', 'progress': None, 'generation_not_started': False})
    return message


async def generate(service, rid, payload, reference):
    from .simple_flow import SimpleStopped
    binding=service.account_bridge.binding(payload['account_id'])
    if not binding:raise SimpleStopped('Tài khoản đã chọn không còn hợp lệ; chưa gọi CLI.')
    bundled=not(REPO_DIRECTORY or os.environ.get('SCENEFORGE_GFLOW_REPO'))
    cli_home=None
    try:
        if bundled:
            from .flow_cli_bundle import bundled_runtime
            service.phase(rid,'opening','Đang chuẩn bị CLI gốc đi kèm SceneForge.')
            repo=await asyncio.to_thread(bundled_runtime,service.data)
            profile='';discovery={'source':'bundled_offline','candidate_count':1}
        else:
            repo,profile,discovery=await asyncio.to_thread(resolve_repo,service,payload['account_id'],binding['email'])
    except (SimpleStopped,RuntimeError,ValueError,OSError) as exc:
        service.ledger.set_metadata(rid,{'generation_not_started':True,'cli_discovery':{'state':'bundle_unavailable' if bundled else 'not_found_or_ambiguous'},'message':str(exc)})
        raise SimpleStopped(str(exc)) from None
    service.ledger.set_metadata(rid,{'cli_discovery':{'state':'resolved',**discovery}})
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
    if bundled:
        from .flow_cli_bundle import prepare_profile
        try:cli_home,profile=await asyncio.to_thread(prepare_profile,service.data,payload['account_id'],binding)
        except (RuntimeError,OSError) as exc:
            service.ledger.set_metadata(rid,{'generation_not_started':True})
            raise SimpleStopped(str(exc)) from None
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
    env = dict(os.environ, GFLOW_CLI_UPDATE_CHECK='0', NO_COLOR='1', TERM='dumb', PYTHONUTF8='1', PYTHONUNBUFFERED='1', GFLOW_CLI_LOG_LEVEL='INFO', GFLOW_CLI_LOG_FORMAT='json')
    # Same environment as MO-UNG-DUNG.bat when the supplied app is portable.
    if bundled or (repo / 'runtime' / 'python.exe').is_file():
        env.pop('PYTHONHOME', None)
        env.pop('PYTHONPATH', None)
        env['PYTHONNOUSERSITE'] = '1'
        env['GFLOW_CLI_HOME'] = str(cli_home if bundled else repo / 'data' / 'profiles')
    service.ledger.set_metadata(rid, {'engine': 'gflow-cli-direct', 'clicked': True,
        'generation_granted': True, 'cli': {'cwd': str(repo), 'entrypoint': '-m gflow_cli video '+('r2v' if cfg['mode']=='ingredients' else 'i2v'), 'profile': profile, 'bundled':bundled, 'home':str(cli_home) if bundled else None}})
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
        from .flow_cli_progress import CliProgress,communicate_live,ProgressMismatch
        monitor=CliProgress(service,rid,project)
        try:stdout, stderr = await asyncio.wait_for(communicate_live(process,monitor), 1200)
        except ProgressMismatch as exc:raise SimpleStopped(str(exc)) from None
        stdout = stdout.decode('utf-8', errors='replace')
        stderr = stderr.decode('utf-8', errors='replace')
        logs = {'exit_code': process.returncode, 'stdout': safe_log(stdout, payload['prompt']),
                'stderr': safe_log(stderr, payload['prompt'])}
        service.ledger.set_metadata(rid, {'engine_diagnostics': logs})
        failure = confirmed_generation_failure(logs, service.ledger.metadata(rid).get('provider_task'), project)
        if failure:
            from .simple_flow import FlowGenerationFailed
            raise FlowGenerationFailed(record_generation_failure(service, rid, failure))
        if process.returncode:
            media = recovery_media(logs)
            if media:
                if monitor.identity and monitor.identity['media_id']!=media:raise SimpleStopped('ID tải lại khác ID đã theo dõi; chưa nhập clip, không tạo lại.')
                path, identity = await download_existing(service,rid,repo,profile,env,output,media,project,payload['prompt'])
                await finish_video(service,rid,payload,path,identity)
                return
            raise SimpleStopped('CLI gốc dừng, mã thoát '+str(process.returncode)+'. stdout và stderr đã ghi trong báo cáo; không tự tạo lại.')
        try: result = video_result(stdout)
        except ValueError as exc: raise SimpleStopped(str(exc)) from None
        media = result.get('media_id')
        if result.get('succeeded') is not True or not re.fullmatch(r'[a-fA-F0-9-]{36}', str(media)):
            raise SimpleStopped('CLI chưa xác nhận video thành công; không tự tạo lại.')
        if monitor.identity and monitor.identity['media_id']!=media:raise SimpleStopped('ID kết quả khác ID đã theo dõi; chưa nhập clip, không tạo lại.')
        identity = {'media_id': media, 'project_id': project, 'workflow_id': (monitor.identity or {}).get('workflow_id')}
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
    known=service.ledger.metadata(rid).get('provider_task')or{}
    identity = {'media_id': media, 'project_id': project, 'workflow_id': known.get('workflow_id') if known.get('media_id')==media else None}
    inputs = dict(service.ledger.metadata(rid).get('native_inputs') or {})
    inputs.update(generation_submitted=True, generation_ready=False, native_stage='video_ready_downloading', state='submitted')
    service.ledger.set_metadata(rid, {'native_inputs': inputs, 'provider_task': {**identity, 'association_confirmed': True,
        'source': 'gflow_cli_download_error', 'state': 'downloading'}})
    service.phase(rid, 'downloading', 'Video đã tạo xong; đang tải lại đúng ID bằng CLI, không tạo video mới.')
    python = repo / 'runtime' / 'python.exe'
    if not python.is_file() and (repo/'python.exe').is_file():python=repo/'python.exe'
    args = [str(python) if python.is_file() else 'py', '-m', 'gflow_cli', 'data', 'download',
            media, '--profile', profile, '--out', str(output), '--json']
    options = {'creationflags': 0x08000000} if os.name == 'nt' else {}
    download_env=dict(env, GFLOW_CLI_LOG_LEVEL='WARNING')
    process = await asyncio.create_subprocess_exec(*args, cwd=str(repo), env=download_env,
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
        identity['workflow_id'] = values[0].get('workflow_id') or identity['workflow_id']
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
        inputs = meta.get('native_inputs') or {}
        project = inputs.get('project_id') or inputs.get('uploaded_media_project')
        failure = confirmed_generation_failure(meta.get('engine_diagnostics') or {}, meta.get('provider_task'), project)
        if failure:
            message = record_generation_failure(service, rid, failure)
            service.ledger.finish(rid, 'failed')
            service.state, service.message = 'failed', message
            return
        media = (meta.get('provider_task') or {}).get('media_id') or recovery_media(meta.get('engine_diagnostics') or {})
        if not media:return
        selection = service.account_bridge.selection()
        binding = service.account_bridge.binding(meta.get('account_id'))
        if not binding or not selection.get('available') or selection.get('account_id') != meta.get('account_id'):return
        inputs = meta.get('native_inputs') or {}
        project = inputs.get('project_id') or inputs.get('uploaded_media_project')
        repo = Path((meta.get('cli') or {}).get('cwd', ''))
        bundled=(meta.get('cli') or {}).get('bundled') is True
        if bundled:
            from .flow_cli_bundle import existing_profile
            pair=existing_profile(service.data,meta['account_id'],binding,meta['cli'])
            if not pair or not (repo/'python.exe').is_file():return
            cli_home,profile=pair;profiles=[profile]
        else:
            cli_home=repo/'data/profiles'
            profiles=matching_profile(repo,binding['email']) if repo.is_dir() else []
        if len(profiles)!=1 or not re.fullmatch(r'[a-fA-F0-9-]{36}',str(project)):return
        output=(service.root/(rid+'.cli')).resolve();output.mkdir(exist_ok=True)
        env=dict(os.environ,GFLOW_CLI_UPDATE_CHECK='0',NO_COLOR='1',TERM='dumb',PYTHONUTF8='1')
        if bundled or (repo/'runtime/python.exe').is_file():
            env.pop('PYTHONHOME',None);env.pop('PYTHONPATH',None)
            env.update(PYTHONNOUSERSITE='1',GFLOW_CLI_HOME=str(cli_home))
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
