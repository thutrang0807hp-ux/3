"""Private subprocess entry point. No CLI/user UI, credentials or RPC minting.

Owns the normal headed browser on SceneForge's existing profile. Uses the exact
gflow distribution bundled with GFlow Studio, isolated from SceneForge's Python.
Only allowlisted JSON events go to stdout; library logging never goes there.
"""
import asyncio
import contextlib
import json
from pathlib import Path
import re
import sys
import threading

UPSTREAM_VERSION = '0.92.1'
_OUTPUT = sys.stdout
ERROR_CODES = {'engine_version_mismatch', 'profile_or_image_missing', 'browser_missing',
               'account_identity_unverified'}


def emit(event, **fields):
    _OUTPUT.write(json.dumps({'event': event, **fields}) + '\n')
    _OUTPUT.flush()


async def run(spec):
    from importlib.metadata import version
    if version('gflow-cli') != UPSTREAM_VERSION:
        raise RuntimeError('engine_version_mismatch')
    from gflow_cli.api.client import FlowApiClient
    from gflow_cli.api.video import GenerateVideoRequest, Mode, Aspect, VideoModel
    from gflow_cli.config import Settings

    profile = Path(spec['profile'])
    image = Path(spec['image'])
    output = Path(spec['output'])
    if not profile.is_dir() or not image.is_file():
        raise ValueError('profile_or_image_missing')
    if not Path(spec['browser']).is_file():
        raise ValueError('browser_missing')
    class SceneForgeClient(FlowApiClient):
        async def _preread_flow_session_cookies(self):
            # Windows Chrome reads its own existing profile. No cookie export.
            return None

        async def _ensure_context_session_cookie(self):
            return None

        def _persistent_context_kwargs(self):
            options = super()._persistent_context_kwargs()
            options.pop('channel', None)
            options['executable_path'] = spec['browser']
            return options
    request = GenerateVideoRequest(prompt=spec['prompt'], mode=Mode.R2V,
        aspect=Aspect.PORTRAIT, model=VideoModel.VEO_3_1_LITE,
        duration=8, count=1, reference_images=(image,))
    task = asyncio.current_task()
    loop = asyncio.get_running_loop()
    grants = asyncio.Queue()
    def controls():
        for line in sys.stdin:
            try: command = json.loads(line)
            except ValueError: continue
            if command.get('action') == 'generate':
                loop.call_soon_threadsafe(grants.put_nowait, True)
            elif command.get('action') == 'cancel':
                loop.call_soon_threadsafe(task.cancel)
                return
        try: loop.call_soon_threadsafe(task.cancel)
        except RuntimeError: pass
    threading.Thread(target=controls, daemon=True).start()
    settings = Settings(_env_file=None, headless=False, transport='ui_automation',
                        browser_engine='playwright', concurrency=1, incident_capture=False)
    async with SceneForgeClient(profile_dir=profile, headless=False, settings=settings,
                             transport='ui_automation', out_dir=output) as client:
        actual = await client.page.evaluate("()=>String(window.WIZ_global_data?.oPEP7c||'').trim().toLowerCase()")
        if actual != spec['expected_email'].strip().lower():
            raise ValueError('account_identity_unverified')
        emit('ready', engine_version=UPSTREAM_VERSION)
        await grants.get()  # Parent commits ambiguity boundary BEFORE this grant.
        def started(value):
            emit('started', media_id=value.media_id, project_id=value.project_id,
                 workflow_id=value.workflow_id)
        result = await client.generate_video(req=request, project_id=spec.get('project_id'),
            out_dir=output, poll_timeout_s=600, download=True, on_started=started)
        if not result.status.succeeded or result.local_path is None:
            emit('generation_failed')
            return
        emit('complete', media_id=result.status.media_id, project_id=result.project_id,
             workflow_id=result.workflow_id, file=str(result.local_path))


def main():
    spec = json.loads(sys.stdin.readline())
    try:
        # Third-party logging is private/discarded by the parent, never report JSON.
        with contextlib.redirect_stdout(sys.stderr):
            asyncio.run(run(spec))
    except BaseException as error:
        codes = sorted(set(re.findall(r'\bPUBLIC_ERROR_[A-Z0-9_]{1,100}\b', str(error))))[:8]
        emit('error', error_type=type(error).__name__, public_error_codes=codes,
             error_code=str(error) if str(error) in ERROR_CODES else None)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
