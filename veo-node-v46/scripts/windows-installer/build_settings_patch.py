"""Build scene-prompt preparation with the unchanged v46.19 uploader using the existing unchanged unsigned launcher."""
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile

import dnfile

ROOT = Path(__file__).resolve().parents[3]
VERSION = '2026.11.02.4622'
NAME = 'SceneForge-Update-20261102-v46.22-Reference-Choice.exe'
BASELINE = '8178af48a4db6180eb0fb3ef042b04ea21617c7380ca2e106d8e967990eb0c35'

def main():
    template = ROOT/'downloads/v46/SceneForge-Update-20261101-v46.exe'
    expected = json.loads(template.with_name('patch-build.json').read_text())['sha256']
    original = template.read_bytes()
    assert hashlib.sha256(original).hexdigest() == expected, 'Template checksum mismatch'
    sources = {
        'app/local_engine/simple_flow.py': ROOT/'veo-node-v46/local_engine/simple_flow.py',
        'app/local_engine/simple_flow_upload.py': ROOT/'veo-node-v46/local_engine/simple_flow_upload.py',
        'app/local_engine/flow_prepare.py': ROOT/'veo-node-v46/local_engine/flow_prepare.py',
        'app/local_engine/flow_settings.py': ROOT/'veo-node-v46/local_engine/flow_settings.py',
        'app/dist/web-demo/workflow.html': ROOT/'workflow.html',
    }
    # User supplied and confirmed .19. Never downgrade its uploader again.
    upload19_sha256 = '342e1bde247a0ca3612efe7c363cb0d741c84a1b014a71c35a402d1e6aba5869'
    assert hashlib.sha256(sources['app/local_engine/simple_flow_upload.py'].read_bytes()).hexdigest() == upload19_sha256, 'Uploader differs from user-confirmed v46.19'
    manifest = {'version': VERSION, 'supported_payloads': [BASELINE], 'minimum_patch': '2026.11.01.467',
                'files': [{'path': name, 'bytes': path.stat().st_size,
                           'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for name,path in sources.items()]}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr('patch-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.write(Path(__file__).with_name('apply_update.ps1'), 'apply_update.ps1')
        for name,path in sources.items():
            archive.write(path, 'files/'+name)
    payload = buffer.getvalue()
    pe = dnfile.dnPE(data=original)
    assert not pe.OPTIONAL_HEADER.DATA_DIRECTORY[4].Size, 'Signed launcher must not be modified'
    resources = list(pe.net.mdtables.ManifestResource)
    assert len(resources) == 1 and str(resources[0].Name) == 'SceneForgePatch.zip'
    offset = pe.get_offset_from_rva(pe.net.struct.ResourcesRva) + resources[0].Offset
    capacity = struct.unpack_from('<I', original, offset)[0]
    assert len(payload) <= capacity, 'New payload exceeds launcher capacity'
    data = bytearray(original)
    data[offset:offset+4+capacity] = struct.pack('<I',len(payload))+payload+bytes(capacity-len(payload))
    assert bytes(data[:offset]) == original[:offset] and bytes(data[offset+4+capacity:]) == original[offset+4+capacity:]
    verified = dnfile.dnPE(data=bytes(data))
    embedded = next(r.data for r in verified.net.resources if r.name == 'SceneForgePatch.zip')
    assert embedded == payload
    with zipfile.ZipFile(io.BytesIO(embedded)) as archive:
        assert archive.testzip() is None
        for name,path in sources.items():
            assert archive.read('files/'+name) == path.read_bytes(), name
    output = ROOT/'downloads/v46-settings-link'
    output.mkdir(exist_ok=True)
    exe = output/NAME
    exe.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    exe.with_suffix('.exe.sha256').write_text(digest+'  '+NAME+'\n')
    report = {'version': VERSION, 'file': NAME, 'bytes': len(data), 'sha256': digest, 'files': len(sources),
              'minimum_patch': manifest['minimum_patch'], 'embedded_files_verified': True,
              'duplicate_reference_choice': True, 'scene_prompt_preparation': True, 'prepared_generation_receipt': True,
              'upload_implementation': 'project_upload_v46_19', 'uploader_byte_identical_to_v46_19': True,
              'uploader_sha256': upload19_sha256,
              'launcher_code_unchanged': True, 'live_flow_verified': False, 'windows_installer_tested': False}
    (output/'patch-build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))

if __name__ == '__main__':
    main()
