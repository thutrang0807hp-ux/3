"""Build the v46.47 integrated Flow UI engine update on v46.42 or newer.

Reuses the verified unsigned generic launcher; only replaces its embedded ZIP.
No source rewriting, external code, credentials, profiles or models in payload.
Requires dnfile (build-time only).
"""
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile

import dnfile

ROOT = Path(__file__).resolve().parents[3]
VERSION = '2026.11.03.4647'
NAME = 'SceneForge-Update-20261103-v46.47-Flow-UI-Engine.exe'
BASELINE = '8178af48a4db6180eb0fb3ef042b04ea21617c7380ca2e106d8e967990eb0c35'
NAMES = ('simple_flow.py', 'flow_native_reference.py', 'flow_native_pipeline.py', 'flow_task_tracker.py',
         'flow_gflow_adapter.py', 'flow_gflow_runtime.py', 'flow_gflow_worker.py',
         'flow_batch_session.py', 'flow_task_protocol.py', 'flow_pair_generation.py', 'flow_pair_trial.py', 'flow_composer_upload.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    template = ROOT / 'downloads/v46/SceneForge-Update-20261101-v46.exe'
    expected = json.loads(template.with_name('patch-build.json').read_text())['sha256']
    original = template.read_bytes()
    assert sha(original) == expected, 'Template checksum mismatch'
    sources = {'app/local_engine/' + name: ROOT / 'veo-node-v46/local_engine' / name for name in NAMES}
    sources['app/dist/web-demo/workflow.html'] = ROOT / 'workflow.html'
    prior = ROOT / 'downloads/v46-flow-ui-engine-fix/patch-build.json'
    if prior.is_file():
        pinned = json.loads(prior.read_text())
        assert pinned['version'] == VERSION, 'Unexpected release metadata'
        expected_sources = {item['path']: item['sha256'] for item in pinned['files']}
        assert all(expected_sources.get(name) == sha(path.read_bytes()) for name,path in sources.items()), \
            'Source changed since v46.47; use a NEW version, do not overwrite the published EXE'
    manifest = {'version': VERSION, 'supported_payloads': [BASELINE],
                'minimum_patch': '2026.11.02.4642',
                'files': [{'path': name, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())}
                          for name, path in sources.items()]}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr('patch-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.write(Path(__file__).with_name('apply_gflow_update.ps1'), 'apply_update.ps1')
        for name, path in sources.items():
            archive.write(path, 'files/' + name)
    payload = buffer.getvalue()
    pe = dnfile.dnPE(data=original)
    assert not pe.OPTIONAL_HEADER.DATA_DIRECTORY[4].Size, 'Signed launcher cannot be modified'
    resources = list(pe.net.mdtables.ManifestResource)
    assert len(resources) == 1 and str(resources[0].Name) == 'SceneForgePatch.zip'
    offset = pe.get_offset_from_rva(pe.net.struct.ResourcesRva) + resources[0].Offset
    capacity = struct.unpack_from('<I', original, offset)[0]
    assert len(payload) <= capacity, 'Payload exceeds launcher capacity'
    data = bytearray(original)
    data[offset:offset + 4 + capacity] = struct.pack('<I', len(payload)) + payload + bytes(capacity - len(payload))
    assert bytes(data[:offset]) == original[:offset]
    assert bytes(data[offset + 4 + capacity:]) == original[offset + 4 + capacity:]
    verified = dnfile.dnPE(data=bytes(data))
    embedded = next(r.data for r in verified.net.resources if r.name == 'SceneForgePatch.zip')
    assert embedded == payload
    with zipfile.ZipFile(io.BytesIO(embedded)) as archive:
        assert archive.testzip() is None
        assert json.loads(archive.read('patch-manifest.json')) == manifest
        for name, path in sources.items():
            assert archive.read('files/' + name) == path.read_bytes()
    output = ROOT / 'downloads/v46-flow-ui-engine-fix'
    output.mkdir(exist_ok=True)
    exe = output / NAME
    exe.write_bytes(data)
    digest = sha(data)
    exe.with_suffix('.exe.sha256').write_text(digest + '  ' + NAME + '\n')
    report = {'version': VERSION, 'file': NAME, 'bytes': len(data), 'sha256': digest,
              'files': manifest['files'], 'minimum_patch': manifest['minimum_patch'],
              'embedded_files_verified': True, 'launcher_code_unchanged': True,
              'generation_engine': 'gflow-cli-0.92.1-ui_automation', 'runtime_auto_download': True,
              'runtime_archive_sha256': '03ae9541fefa55e4f917f87db794cd2b26f61d5d215a754b333b5dfc3d686292',
              'one_create_action': True, 'reviewed_source_commit': '671be69', 'ledger': 'existing_RequestLedger_only',
              'normal_native_session_only': True, 'automatic_retry': False,
              'live_flow_verified': False, 'windows_installer_tested': False}
    (output / 'patch-build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
