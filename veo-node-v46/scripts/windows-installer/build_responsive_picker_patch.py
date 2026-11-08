"""Build the v46.73 responsive voice picker update on v46.72 or newer.

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
VERSION = '2026.11.08.4673'
NAME = 'SceneForge-Update-20261108-v46.73-Responsive-Picker.exe'
BASELINE = '8178af48a4db6180eb0fb3ef042b04ea21617c7380ca2e106d8e967990eb0c35'
NAMES = ()  # UI-only; preserve .72 warm runtime and installed model.


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    template = ROOT / 'downloads/v46/SceneForge-Update-20261101-v46.exe'
    expected = json.loads(template.with_name('patch-build.json').read_text())['sha256']
    original = template.read_bytes()
    assert sha(original) == expected, 'Template checksum mismatch'
    sources = {'app/local_engine/' + name: ROOT / 'veo-node-v46/local_engine' / name for name in NAMES}
    for name in ('workflow.html','photos.html'):
        sources['app/dist/web-demo/' + name] = ROOT / name
    prior = ROOT / 'downloads/v46-responsive-picker/patch-build.json'
    if prior.is_file():
        pinned = json.loads(prior.read_text())
        assert pinned['version'] == VERSION, 'Unexpected release metadata'
        expected_sources = {item['path']: item['sha256'] for item in pinned['files']}
        assert all(expected_sources.get(name) == sha(path.read_bytes()) for name,path in sources.items()), \
            'Source changed since v46.73; use a NEW version, do not overwrite the published EXE'
    manifest = {'version': VERSION, 'supported_payloads': [BASELINE],
                'minimum_patch': '2026.11.08.4672',
                'files': [{'path': name, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())}
                          for name, path in sources.items()]}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr('patch-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.write(Path(__file__).with_name('apply_bundled_cli_update.ps1'), 'apply_update.ps1')
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
    output = ROOT / 'downloads/v46-responsive-picker'
    output.mkdir(exist_ok=True)
    exe = output / NAME
    exe.write_bytes(data)
    digest = sha(data)
    exe.with_suffix('.exe.sha256').write_text(digest + '  ' + NAME + '\n')
    report = {'version':VERSION,'file':NAME,'bytes':len(data),'sha256':digest,
              'files':manifest['files'],'minimum_patch':manifest['minimum_patch'],
              'embedded_files_verified':True,'launcher_code_unchanged':True,
              'baseline_source_commit':'04522b1','ui_only':True,'windows_voice_alias_compatible':True,'picker_does_not_wait_for_save':True,'independent_sample_pending_state':True,'stale_preview_cannot_autoplay':True,'persistent_private_cpu_worker':True,'idle_release_seconds':180,'audio_controls_preserve_frame_dom':True,'filesystem_checks_off_event_loop':True,'explicit_shared_preparation':True,'single_model_load_for_preview_batch':True,'ready_preview_does_not_synthesize':True,'installed_runtime_preserved':True,
              'compact_searchable_voice_picker':True,'immediate_audio_play':True,'cached_sample_retry':True,
              'fresh_readonly_diagnostic_export':True,'labeled_last_backend_snapshot':True,
              'export_request_store_room_binding_checked':True,'unknown_store_not_treated_as_unsent':True,
              'generation_behavior_unchanged':True,
              'explicit_generation_failure_not_downloaded':True,'legacy_failure_identity_checked':True,
              'error_recovery_controls_reenabled':True,'json_export_separate_from_clip_check':True,
              'original_cli_runtime_unchanged':True,
              'view_navigation_keeps_frames_and_autosave':True,'strict_room_switch_and_checkpoint_guards':True,
              'recent_people_uses_metadata_only':True,'recipe_notifications_use_structural_summary':True,
              'loaded_room_reused_without_duplicate_render':True,'workspace_progress_skips_hidden_home_render':True,
              'legacy_frame_markup_skipped_in_grid':True,
              'database_readiness_barrier':True,'preboot_navigation_deferred':True,
              'recipe_read_failure_can_retry':True,'existing_data_preserved_in_fixture':True,
              'direct_overview_subpage_navigation':True,'batch_form_retained':True,
              'unchanged_markup_skipped_with_mutation_invalidation':True,'offscreen_card_layout_deferred':True,
              'home_date_formatter_reused':True,
              'latest_navigation_click_wins':True,'shared_frame_initialization':True,
              'single_project_startup_read':True,'scene_details_skip_canvas_rebuild':True,
              'hidden_dashboard_render_skipped_on_workspace_navigation':True,
              'lightweight_scanning_status':True,'frame_instances_preserved':True,
              'flush_and_busy_guards_preserved':True,
              'live_flow_verified':False,'windows_installer_tested':False}
    (output / 'patch-build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
