"""Build the v46.101 cumulative application update on v46.62 or newer.

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
VERSION = '2026.11.10.46101'
NAME = 'SceneForge-Update-20261110-v46.101-Native-Startup.exe'
BASELINE = '8178af48a4db6180eb0fb3ef042b04ea21617c7380ca2e106d8e967990eb0c35'
NAMES = ('browser_profiles.py', 'desktop_icon.py', 'export_save_as.py', 'fingerprints.py', 'flow_background_session.py', 'flow_gflow_cli.py', 'gemini_chat.py', 'google_login.py', 'local_tts.py', 'monitoring.py', 'server.py', 'storage_jobs.py', 'timeline_export.py', 'voice_previews.py', 'voice_previews_worker.py', 'voice_runtime.py', 'voice_runtime_worker.py', 'voice_worker.py', 'web_images.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    template = ROOT / 'downloads/v46/SceneForge-Update-20261101-v46.exe'
    expected = json.loads(template.with_name('patch-build.json').read_text())['sha256']
    original = template.read_bytes()
    assert sha(original) == expected, 'Template checksum mismatch'
    sources = {'app/local_engine/' + name: ROOT / 'veo-node-v46/local_engine' / name for name in NAMES}
    for name in ('index.html','studio.html','workflow.html','photos.html','native/index.html','icons/SceneForge.ico'):
        sources['app/dist/web-demo/' + name] = ROOT / name
    sources['SceneForge.exe'] = ROOT / 'veo-node-v46/windows-desktop/SceneForge.exe'
    coverage = {}
    for metadata in ROOT.glob('downloads/*/patch-build.json'):
        row = json.loads(metadata.read_text())
        try: number = int(str(row.get('version','')).split('.')[-1])
        except ValueError: continue
        if 4663 <= number <= 4696:
            for item in row.get('files',[]):
                old = coverage.get(item['path'])
                if old is None or old[0] < number: coverage[item['path']] = (number,item['sha256'])
    assert set(sources)-{'SceneForge.exe'} == set(coverage), 'Cumulative payload must cover every file updated after .62'
    assert all(name in ('SceneForge.exe','app/dist/web-demo/index.html','app/dist/web-demo/studio.html') or sha(path.read_bytes()) == coverage[name][1] for name,path in sources.items()), 'Current sources differ from released latest content'
    prior = ROOT / 'downloads/v46-native-startup/patch-build.json'
    if prior.is_file():
        pinned = json.loads(prior.read_text())
        assert pinned['version'] == VERSION, 'Unexpected release metadata'
        expected_sources = {item['path']: item['sha256'] for item in pinned['files']}
        assert all(expected_sources.get(name) == sha(path.read_bytes()) for name,path in sources.items()), \
            'Source changed since v46.101; use a NEW version, do not overwrite the published EXE'
    manifest = {'version': VERSION, 'supported_payloads': [BASELINE],
                'minimum_patch': '2026.11.04.4662',
                'files': [{'path': name, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())}
                          for name, path in sources.items()]}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr('patch-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.write(Path(__file__).with_name('apply_native_startup.ps1'), 'apply_update.ps1')
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
    output = ROOT / 'downloads/v46-native-startup'
    output.mkdir(exist_ok=True)
    exe = output / NAME
    exe.write_bytes(data)
    digest = sha(data)
    exe.with_suffix('.exe.sha256').write_text(digest + '  ' + NAME + '\n')
    report = {'version':VERSION,'file':NAME,'bytes':len(data),'sha256':digest,
              'files':manifest['files'],'minimum_patch':manifest['minimum_patch'],
              'embedded_files_verified':True,'launcher_code_unchanged':True,
              'baseline_source_commit':'2440eba','cumulative_from':'2026.11.04.4662',
              'covers_patch_numbers':[63,96],'all_intermediate_file_updates_covered':True,
              'file_count':len(sources),'model_and_account_data_not_in_payload':True,
              'installed_version_shown':True,'downgrade_blocked':True,
              'startup_count_only_presence':True,'native_loading_card':True,'native_windows_run':False,'static_loading_card':True,'native_bounded_sha256':True,'native_binary_compare':True,'incremental_dirty_key_reads':True,'visible_close_error':True,'windows_installer_tested':False}
    (output / 'patch-build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
