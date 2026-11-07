"""Isolated CPU synthesis worker; model downloads only with --prepare."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import uuid
import wave

V3_FILES = ('vieneu_prefill.onnx', 'vieneu_decode_step.onnx', 'vieneu_acoustic_cached.onnx',
            'vieneu_backbone_shared.data', 'vieneu_v3_heads.npz', 'config.json', 'tokenizer.json')
CODEC_FILES = ('moss_audio_tokenizer_decode_full.onnx', 'moss_audio_tokenizer_decode_shared.data',
               'moss_audio_tokenizer_decode_step.onnx', 'codec_browser_onnx_meta.json',
               'moss_audio_tokenizer_encode.onnx', 'moss_audio_tokenizer_encode.data')


def local_assets(runtime):
    base = Path(runtime) / 'offline'
    expected = [('vieneu', name) for name in V3_FILES] + [('codec', name) for name in CODEC_FILES]
    return base, [str(Path(folder) / name) for folder, name in expected if not (base / folder / name).is_file()]


def load_model(runtime):
    """Use user-supplied ONNX files directly, without fabricating a Hub cache revision."""
    from vieneu import Vieneu
    base, missing = local_assets(runtime)
    if missing:
        if any((base / folder).exists() for folder in ('vieneu', 'codec')):
            raise RuntimeError('Bộ model offline chưa đủ: ' + ', '.join(missing))
        return Vieneu(mode='v3turbo', backend='onnx', device='cpu', precision='fp32', threads=2)
    # The pinned SDK forwards onnx_dir but not codec_dir. Scope the codec override
    # to this constructor call in this isolated worker; do not edit third-party code.
    from vieneu._v3_turbo_engine import onnx_runtime_lite
    original = onnx_runtime_lite.OnnxV3LiteEngine
    class LocalCodecEngine(original):
        def __init__(self, *args, **kwargs):
            kwargs['codec_dir'] = str(base / 'codec')
            super().__init__(*args, **kwargs)
    onnx_runtime_lite.OnnxV3LiteEngine = LocalCodecEngine
    try:
        return Vieneu(mode='v3turbo', backend='onnx', device='cpu', precision='fp32', threads=2,
                      backbone_repo=str(base / 'vieneu'), onnx_dir=str(base / 'vieneu'))
    finally:
        onnx_runtime_lite.OnnxV3LiteEngine = original


def validate_beats(beats):
    if not isinstance(beats, list) or not 1 <= len(beats) <= 60:
        raise ValueError('Cần 1–60 nhịp.')
    if any(not isinstance(b, dict) or not isinstance(b.get('id'), str) or not isinstance(b.get('text'), str) or not b['text'].strip() or len(b['text']) > 5000 for b in beats):
        raise ValueError('Mỗi nhịp cần id và lời đọc không trống, tối đa 5.000 ký tự.')
    if len({b['id'] for b in beats}) != len(beats) or sum(len(b['text']) for b in beats) > 15000:
        raise ValueError('Nhịp trùng id hoặc tổng lời quá 15.000 ký tự.')
    return beats


def synthesize(model, beats, voice, output, workdir=None):
    """One voice per request, exact accumulated timing, bounded output."""
    validate_beats(beats)
    preset = model.get_preset_voice(voice or None)
    parts, segments, cursor, params = [], [], 0, None
    output = Path(output)
    for beat in beats:
        temp = Path(workdir or output.parent) / (str(uuid.uuid4()) + '.wav')
        try:
            audio = model.infer(beat['text'].strip(), voice=preset)
            model.save(audio, str(temp))
            with wave.open(str(temp), 'rb') as wav:
                current = (wav.getnchannels(), wav.getsampwidth(), wav.getframerate())
                seconds = wav.getnframes() / wav.getframerate()
                frames = wav.readframes(wav.getnframes())
            if current[0] != 1 or current[1] != 2 or not 8000 <= current[2] <= 96000 or not math.isfinite(seconds) or not 0 < seconds <= 600:
                raise ValueError('Đầu ra WAV không hợp lệ.')
            if params is not None and params != current:
                raise ValueError('Các nhịp khác định dạng âm thanh.')
            params = current
            if cursor + seconds > 1800 or sum(map(len, parts)) + len(frames) > 200 * 1024**2:
                raise ValueError('Giọng đọc vượt 30 phút hoặc 200 MB.')
            parts.append(frames)
            segments.append({'id': beat['id'], 'start': cursor, 'end': cursor + seconds})
            cursor += seconds
        finally:
            temp.unlink(missing_ok=True)
    partial = output.with_suffix('.partial')
    try:
        with wave.open(str(partial), 'wb') as wav:
            wav.setparams((*params, 0, 'NONE', 'not compressed'))
            wav.writeframes(b''.join(parts))
        os.replace(partial, output)
    finally:
        partial.unlink(missing_ok=True)
    return {'segments': segments, 'duration': cursor, 'sample_rate': params[2], 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    args.runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.environ.setdefault('HF_HOME',str(args.runtime / 'hf-cache'))
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '0' if args.prepare else '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '0' if args.prepare else '1'
    model = load_model(args.runtime)
    data = json.loads(args.request.read_text(encoding='utf-8')) if args.request else {'beats': [{'id': 'probe', 'text': 'Xin chào, đây là giọng đọc thử của SceneForge.'}]}
    result = synthesize(model, data['beats'], data.get('voice'), args.output, args.request.parent if args.request else None)
    result['voices'] = [{'label': label, 'id': voice_id} for label, voice_id in model.list_preset_voices()]
    args.result.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    print('VieNeu CPU synthesis completed; WAV and timing saved.')


if __name__ == '__main__':
    main()
