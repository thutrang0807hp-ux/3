"""Build the v46.120 cumulative application update on v46.62 or newer.

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
VERSION = '2026.11.14.46120'
NAME = 'SceneForge-Update-20261114-v46.120-Omni-Prompt-Layers.exe'
BASELINE = '8178af48a4db6180eb0fb3ef042b04ea21617c7380ca2e106d8e967990eb0c35'
NAMES = ('browser_profiles.py', 'desktop_icon.py', 'export_save_as.py', 'fingerprints.py', 'flow_background_session.py', 'flow_gflow_cli.py', 'gemini_chat.py', 'google_login.py', 'local_tts.py', 'monitoring.py', 'server.py', 'storage_jobs.py', 'timeline_export.py', 'voice_previews.py', 'voice_previews_worker.py', 'voice_runtime.py', 'voice_runtime_worker.py', 'voice_worker.py', 'web_images.py','profile_cache.py','simple_flow.py','flow_credit.py','script_library.py','script_composer.py','flow_video_options.py','flow_settings.py','flow_cli_bundle.py','flow_omni_runtime.py')


def align(value,boundary):
    return (value+boundary-1)//boundary*boundary


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
    sources['app/vendor/gflow_cli-0.98.0-py3-none-any.whl']=ROOT/'veo-node-v46/vendor/gflow_cli-0.98.0-py3-none-any.whl'
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
    assert set(coverage) <= set(sources), 'Cumulative payload must cover every intermediate updated file'
    assert all(name in ('app/local_engine/flow_gflow_cli.py','app/local_engine/flow_video_options.py','app/local_engine/flow_settings.py','app/local_engine/flow_cli_bundle.py','app/local_engine/flow_omni_runtime.py','app/vendor/gflow_cli-0.98.0-py3-none-any.whl','app/local_engine/script_library.py','app/local_engine/script_composer.py','app/local_engine/flow_credit.py','app/local_engine/profile_cache.py','app/local_engine/simple_flow.py','app/local_engine/browser_profiles.py','app/local_engine/google_login.py','app/local_engine/flow_background_session.py','app/local_engine/server.py','SceneForge.exe','app/dist/web-demo/index.html','app/dist/web-demo/studio.html','app/dist/web-demo/workflow.html','app/dist/web-demo/photos.html','app/dist/web-demo/native/index.html') or sha(path.read_bytes()) == coverage[name][1] for name,path in sources.items()), 'Current sources differ from released latest content'
    for name,identifier,pages in [('veo_lifecycle.js','veo-lifecycle-v113',['workflow.html','photos.html']),('photo_veo.js','photo-veo-v113',['photos.html'])]:
        module=(ROOT/'scripts/ui'/name).read_text()
        assert all('<script id="'+identifier+'">'+module+'</script>' in (ROOT/page).read_text() for page in pages)
    layers=(ROOT/'scripts/ui/prompt_layers.js').read_text()
    assert '<script id="prompt-layers-v120">'+layers+'</script>' in (ROOT/'workflow.html').read_text()
    reorder=(ROOT/'scripts/ui/merge_order.js').read_text()
    assert '<script id="merge-order-v117">'+reorder+'</script>' in (ROOT/'workflow.html').read_text()
    accounts=(ROOT/'scripts/ui/batch_accounts.js').read_text()
    assert all('<script id="batch-accounts-v116">'+accounts+'</script>' in (ROOT/page).read_text() for page in ['index.html','studio.html'])
    batch=(ROOT/'scripts/ui/batch_source.js').read_text()
    assert all('<script id="batch-source-v115">'+batch+'</script>' in (ROOT/page).read_text() for page in ['index.html','studio.html'])
    frame=(ROOT/'scripts/ui/frame_identity.js').read_text()
    assert '<script id="frame-identity-v112">'+frame+'</script>' in (ROOT/'workflow.html').read_text()
    guide=(ROOT/'scripts/ui/storyboard_guide.js').read_text()
    assert '<script id="storyboard-guide-v111">'+guide+'</script>' in (ROOT/'photos.html').read_text()
    ui = (ROOT / 'scripts/ui/script_composer.js').read_text()
    assert all('<script id="script-composer-v108">' + ui + '</script>' in (ROOT/name).read_text() for name in ('index.html','studio.html')), 'Embedded UI differs from reviewed source'
    prior = ROOT / 'downloads/v46-omni-prompt-layers/patch-build.json'
    if prior.is_file():
        pinned = json.loads(prior.read_text())
        assert pinned['version'] == VERSION, 'Unexpected release metadata'
        expected_sources = {item['path']: item['sha256'] for item in pinned['files']}
        assert all(expected_sources.get(name) == sha(path.read_bytes()) for name,path in sources.items()), \
            'Source changed since v46.120; use a NEW version, do not overwrite the published EXE'
    manifest = {'version': VERSION, 'supported_payloads': [BASELINE],
                'minimum_patch': '2026.11.04.4662',
                'files': [{'path': name, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())}
                          for name, path in sources.items()]}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr('patch-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.write(Path(__file__).with_name('apply_omni_prompt_layers.ps1'), 'apply_update.ps1')
        for name, path in sources.items():
            archive.write(path, 'files/' + name)
    payload = buffer.getvalue()
    pe=dnfile.dnPE(data=original);last=pe.sections[-1]
    assert not pe.OPTIONAL_HEADER.DATA_DIRECTORY[4].Size
    resources=list(pe.net.mdtables.ManifestResource);assert len(resources)==1 and str(resources[0].Name)=='SceneForgePatch.zip' and resources[0].Offset==0
    assert last.PointerToRawData+last.SizeOfRawData==len(original)
    # Append readable initialized data to the final section; all prior RVAs/code remain stable.
    resource_offset=align(len(original),pe.OPTIONAL_HEADER.FileAlignment)
    resource_rva=last.VirtualAddress+resource_offset-last.PointerToRawData
    blob=struct.pack('<I',len(payload))+payload
    data=bytearray(original)+bytes(resource_offset-len(original))+blob
    data.extend(bytes(align(len(data),pe.OPTIONAL_HEADER.FileAlignment)-len(data)))
    changes=[]
    def put(owner,field,value):
     offset=owner.get_field_absolute_offset(field);changes.append((offset,4));struct.pack_into('<I',data,offset,value)
    raw_size=len(data)-last.PointerToRawData;virtual_size=resource_offset+len(blob)-last.PointerToRawData
    put(last,'SizeOfRawData',raw_size);put(last,'Misc_VirtualSize',virtual_size)
    put(last,'Characteristics',(last.Characteristics|0x40000040)&~0x02000000)
    put(pe.OPTIONAL_HEADER,'SizeOfImage',align(last.VirtualAddress+virtual_size,pe.OPTIONAL_HEADER.SectionAlignment))
    put(pe.OPTIONAL_HEADER,'SizeOfInitializedData',pe.OPTIONAL_HEADER.SizeOfInitializedData+raw_size-last.SizeOfRawData)
    put(pe.net.struct,'ResourcesRva',resource_rva);put(pe.net.struct,'ResourcesSize',len(blob))
    comparison=bytearray(data[:len(original)])
    for offset,size in changes:comparison[offset:offset+size]=original[offset:offset+size]
    assert bytes(comparison)==original,'Launcher code/metadata changed'
    verified=dnfile.dnPE(data=bytes(data));embedded=next(r.data for r in verified.net.resources if r.name=='SceneForgePatch.zip')
    assert embedded==payload
    with zipfile.ZipFile(io.BytesIO(embedded)) as archive:
        assert archive.testzip() is None
        assert json.loads(archive.read('patch-manifest.json')) == manifest
        for name, path in sources.items():
            assert archive.read('files/' + name) == path.read_bytes()
    output = ROOT / 'downloads/v46-omni-prompt-layers'
    output.mkdir(exist_ok=True)
    exe = output / NAME
    exe.write_bytes(data)
    digest = sha(data)
    exe.with_suffix('.exe.sha256').write_text(digest + '  ' + NAME + '\n')
    report = {'version':VERSION,'file':NAME,'bytes':len(data),'sha256':digest,
              'files':manifest['files'],'minimum_patch':manifest['minimum_patch'],
              'embedded_files_verified':True,'launcher_code_unchanged':True,
              'baseline_source_commit':'5b43cca','cumulative_from':'2026.11.04.4662',
              'covers_patch_numbers':[63,96],'all_intermediate_file_updates_covered':True,
              'file_count':len(sources),'model_and_account_data_not_in_payload':True,
              'installed_version_shown':True,'downgrade_blocked':True,
              'explicit_taskbar_identity':True,'local_ctrl_wheel_zoom':True,'shared_storyboard_art_direction':True,'sample_frame_identity_anchor':True,'photo_veo_shared_lifecycle':True,'responsive_flow_settings_dialog':True,'batch_real_source_default':True,'batch_shared_settings_accounts':True,'merge_clip_drag_order':True,'assembly_preview_order_button':True,'photo_flow_native_dispatch':True,'no_added_model':True,'startup_count_only_presence':True,'vietnamese_script_workbench':True,'three_variants_single_request':True,'photo_script_node_unchanged':True,'real_gemini_generation_tested':False,'selected_flow_credit_toolbar':True,'read_only_visible_balance_refresh':True,'real_flow_account_checked':False,'compact_manual_save_progress':True,'immutable_workflow_media_reuse':True,'stable_generation_hash_promotion':True,'closed_profile_cache_cleanup':True,'cookie_fingerprint_preserved':True,'website_storage_removed_when_idle':True,'retention_mode':'cookie-fingerprint','cache_args_all_launches':True,'windows_cleanup_run':False,'save_in_workspace_toolbar':True,'manual_durable_save':True,'ctrl_s_in_frames':True,'no_repeat_checkpoint_after_clean_save':True,'native_loading_card':True,'native_windows_run':False,'static_loading_card':True,'native_bounded_sha256':True,'native_binary_compare':True,'incremental_dirty_key_reads':True,'visible_close_error':True,'windows_installer_tested':False}
    (output / 'patch-build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
