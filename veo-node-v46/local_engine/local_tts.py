"""Run the isolated VieNeu SDK with prepared weights; never download during render."""
import asyncio
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import uuid
import wave
from fastapi import HTTPException
from .voice_runtime import RUNTIME
from .voice_worker import validate_beats


def engine_root(data):
    return Path(os.environ.get('SCENEFORGE_VIENEU_DIRECTORY', str(data / 'engines/vieneu')))


def tts_status(data):
    root = engine_root(data)
    python = root / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    try:
        marker = json.loads((root / 'runtime/model-status.json').read_text(encoding='utf-8'))
        probe = root / 'runtime/probe.wav'
        ready = bool(marker.get('model_ready') and probe.is_file() and hashlib.sha256(probe.read_bytes()).hexdigest() == marker.get('probe_sha256'))
        for asset in marker.get('local_assets', []):
            relative = Path(asset['path'])
            if relative.is_absolute() or '..' in relative.parts:
                ready = False
                break
            path = root / 'runtime/offline' / relative
            if not path.is_file() or path.stat().st_size != asset['bytes']:
                ready = False
                break
    except (OSError, ValueError, AttributeError, KeyError, TypeError):
        marker, ready = {}, False
    return {'installed': python.is_file(), 'model_ready': ready and python.is_file(), 'backend': 'onnx-cpu-fp32',
            'voices': marker.get('voices', []) if ready else [], 'phase': marker.get('phase', 'not-prepared'),
            'note': 'Chạy local_engine/install-voice.bat để tải model và thử giọng. Không tự tải khi bấm tạo giọng.'}


async def synthesize_isolated(data, media, beats, voice=None):
    if voice is not None and (not isinstance(voice, str) or len(voice) > 200):
        raise HTTPException(400, 'Tên giọng đọc không hợp lệ.')
    try:
        validate_beats(beats)
    except ValueError as error:
        raise HTTPException(400, str(error))
    state = await asyncio.to_thread(tts_status,data)
    if not state['model_ready']:
        raise HTTPException(409, 'SDK/model VieNeu chưa sẵn sàng. Chạy local_engine/install-voice.bat để tải và thử model; app không tạo giọng giả.')
    if voice is not None and voice not in {v['id'] for v in state['voices']}:
        raise HTTPException(400, 'Giọng đã chọn không có trong model đã chuẩn bị.')
    root = engine_root(data)
    python = root / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    filename = str(uuid.uuid4()) + '.wav'
    output = media / filename
    try:
        with tempfile.TemporaryDirectory(prefix='tts-', dir=data) as temporary:
            request, result = Path(temporary) / 'request.json', Path(temporary) / 'result.json'
            request.write_text(json.dumps({'beats': beats, 'voice': voice}, ensure_ascii=False), encoding='utf-8')
            fingerprint=await asyncio.to_thread(lambda:hashlib.sha256((root/'runtime/model-status.json').read_bytes()).hexdigest())
            try:
                await RUNTIME.execute(python,root/'runtime',(str(root.resolve()),fingerprint),request,output,result)
            except asyncio.CancelledError:raise
            except Exception:raise HTTPException(503,'VieNeu chưa tạo được giọng. Model đã được giải phóng; không tự chạy lại lượt tạo.')
            return await asyncio.to_thread(validated_result,output,result,beats,filename)
    except BaseException:
        output.unlink(missing_ok=True)
        output.with_suffix('.partial').unlink(missing_ok=True)
        raise

def validated_result(output,result,beats,filename):
    payload = json.loads(result.read_text(encoding='utf-8'))
    with wave.open(str(output), 'rb') as wav:
        duration = wav.getnframes() / wav.getframerate()
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or not math.isfinite(duration) or not 0 < duration <= 1800:
            raise ValueError('invalid audio')
    if abs(duration - payload['duration']) > .01 or len(payload['segments']) != len(beats):
        raise ValueError('invalid timing')
    cursor = 0
    for beat, segment in zip(beats, payload['segments']):
        if segment.get('id') != beat['id'] or abs(segment['start'] - cursor) > .001 or not segment['end'] > cursor:
            raise ValueError('invalid segment')
        cursor = segment['end']
    if abs(cursor - duration) > .01 or hashlib.sha256(output.read_bytes()).hexdigest() != payload['sha256']:
        raise ValueError('invalid result integrity')
    return {'url': '/local-api/media/' + filename, 'duration': duration, 'segments': payload['segments'], 'sha256': payload['sha256'], 'cost': 0,
            'cost_note': 'Tạo giọng trên CPU, không gọi API trả phí.'}

