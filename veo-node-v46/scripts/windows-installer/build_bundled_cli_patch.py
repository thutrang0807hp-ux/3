"""Build offline v46.60 updater; append managed resources without changing launcher code.

Usage: PYTHONPATH=<dnfile> python build_bundled_cli_patch.py --archive <pinned upstream zip>
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile
import dnfile

ROOT=Path(__file__).resolve().parents[3]
VERSION='2026.11.04.4660'
NAME='SceneForge-Update-20261104-v46.60-Bundled-Original-CLI.exe'
UPSTREAM='03ae9541fefa55e4f917f87db794cd2b26f61d5d215a754b333b5dfc3d686292'
REVISION='09ab05b190ddad0b3bbed80439ecbc6739d5abce'
BASELINE='8178af48a4db6180eb0fb3ef042b04ea21617c7380ca2e106d8e967990eb0c35'
NAMES=('simple_flow.py','flow_gflow_cli.py','flow_native_pipeline.py','flow_pair_generation.py','flow_video_options.py','flow_cli_progress.py','flow_gflow_runtime.py','flow_cli_bundle.py')
def sha(data):return hashlib.sha256(data).hexdigest()
def align(value,boundary):return (value+boundary-1)//boundary*boundary

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--archive',required=True,type=Path);args=parser.parse_args()
 assert sha(args.archive.read_bytes())==UPSTREAM,'Original upstream archive mismatch'
 with zipfile.ZipFile(args.archive) as upstream:
  assert upstream.testzip() is None
  expected={'DOC-TRUOC.txt','MO-UNG-DUNG.bat','app/app.py','app/static/app.js','app/static/index.html','app/static/style.css','app/windows_background.py','SHA256SUMS.txt'}
  nonruntime={n.removeprefix('GFlow-Studio-Portable/') for n in upstream.namelist() if '/runtime/' not in n}
  assert nonruntime==expected,'Unexpected non-runtime/account content'
 sources={'app/local_engine/'+name:ROOT/'veo-node-v46/local_engine'/name for name in NAMES}
 sources['app/dist/web-demo/workflow.html']=ROOT/'workflow.html'
 sources['app/vendor/gflow-original.zip']=args.archive
 output=ROOT/'downloads/v46-bundled-cli';output.mkdir(exist_ok=True)
 files=[dict(path=name,bytes=path.stat().st_size,sha256=sha(path.read_bytes())) for name,path in sources.items()]
 if (output/'patch-build.json').exists():assert json.loads((output/'patch-build.json').read_text())['files']==files,'Published source changed; use a new version'
 manifest=dict(version=VERSION,supported_payloads=[BASELINE],minimum_patch='2026.11.03.4652',files=files)
 buffer=io.BytesIO()
 with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr('patch-manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
  z.write(Path(__file__).with_name('apply_bundled_cli_update.ps1'),'apply_update.ps1')
  for name,path in sources.items():z.write(path,'files/'+name,compress_type=zipfile.ZIP_STORED if name.endswith('.zip') else zipfile.ZIP_DEFLATED)
 payload=buffer.getvalue()
 template=ROOT/'downloads/v46/SceneForge-Update-20261101-v46.exe';original=template.read_bytes()
 assert sha(original)==json.loads(template.with_name('patch-build.json').read_text())['sha256']
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
 with zipfile.ZipFile(io.BytesIO(embedded)) as z:
  assert z.testzip() is None and json.loads(z.read('patch-manifest.json'))==manifest
  for item in files:assert sha(z.read('files/'+item['path']))==item['sha256']
 assert len(data)<100*1024**2,'GitHub artifact limit'
 exe=output/NAME;exe.write_bytes(data);digest=sha(data)
 exe.with_suffix('.exe.sha256').write_text(digest+'  '+NAME+'\n')
 report=dict(version=VERSION,file=NAME,bytes=len(data),sha256=digest,files=files,minimum_patch=manifest['minimum_patch'],
  reviewed_source_commit='bf63704',upstream_revision=REVISION,upstream_archive_sha256=UPSTREAM,cli_version='0.92.1',
  embedded_files_verified=True,launcher_code_unchanged=True,launcher_resource_relocated=True,original_repo_cli=True,
  runtime_bundled=True,runtime_auto_download=False,downloads_discovery_required=False,managed_profile_alias=True,
  sdk_session_overrides=False,automatic_retry=False,live_flow_verified=False,windows_installer_tested=False)
 (output/'patch-build.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='files'}))
if __name__=='__main__':main()
