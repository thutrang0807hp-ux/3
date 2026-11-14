"""Build one online installer for a fresh Windows PC, using a verified v2 base.
No user data, cookies or credentials. Requires dnfile at build time.
"""
import argparse,hashlib,io,json,struct,zipfile
from pathlib import Path
import dnfile
ROOT=Path(__file__).resolve().parents[2]
VERSION='2026.11.14.46129'
BASE_SHA='858fae3ee43bc08811e28339f4a84d0cd33ec645c206b1f62ff586d3f76eb6da'
NAME='SceneForge-Setup-Online-20261114-v46.129.exe'
def sha(data):return hashlib.sha256(data).hexdigest()
def embedded(path):
 pe=dnfile.dnPE(str(path));return next(r.data for r in pe.net.resources if r.name=='SceneForgePatch.zip')
def align(v,b):return (v+b-1)//b*b

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);args=ap.parse_args()
 assert sha(args.base.read_bytes())==BASE_SHA,'Wrong base installer'
 base=zipfile.ZipFile(args.base);assert base.testzip() is None
 # v46 contains the latest pre-manifest bootstrap/paths/extension changes.
 initial=ROOT/'downloads/v46/SceneForge-Update-20261101-v46.exe'
 assert sha(initial.read_bytes())==json.loads(initial.with_name('patch-build.json').read_text())['sha256']
 files={}
 with zipfile.ZipFile(io.BytesIO(embedded(initial)))as z:
  for n in z.namelist():
   if n.startswith('files/'):files[n[6:]]=z.read(n)
 # Full current backend, not just the post-.62 patch subset.
 for p in (ROOT/'veo-node-v46/local_engine').glob('*.py'):
  if not p.name.startswith('check_'):files['app/local_engine/'+p.name]=p.read_bytes()
 for name in ['index.html','studio.html','workflow.html','photos.html','batch-design-demo.html','storage-demo.html','native/index.html','icons/SceneForge.ico']:
  files['app/dist/web-demo/'+name]=(ROOT/name).read_bytes()
 files['SceneForge.exe']=(ROOT/'veo-node-v46/windows-desktop/SceneForge.exe').read_bytes()
 for name in ['Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll','WebView2Loader.dll','WEBVIEW2-LICENSE.txt']:
  files[name]=(ROOT/'veo-node-v46/windows-desktop'/name).read_bytes()
 files['app/vendor/gflow_cli-0.98.0-py3-none-any.whl']=(ROOT/'veo-node-v46/vendor/gflow_cli-0.98.0-py3-none-any.whl').read_bytes()
 # Large original private CLI is recovered byte-for-byte from its released patch.
 bundlemeta=ROOT/'downloads/v46-bundled-cli/patch-build.json'
 if not bundlemeta.is_file():
  bundlemeta=next(p for p in ROOT.glob('downloads/*/patch-build.json') if 'app/vendor/gflow-original.zip' in p.read_text())
 row=json.loads(bundlemeta.read_text());binary=bundlemeta.with_name(row['file'])
 assert sha(binary.read_bytes())==row['sha256']
 with zipfile.ZipFile(io.BytesIO(embedded(binary)))as z:files['app/vendor/gflow-original.zip']=z.read('files/app/vendor/gflow-original.zip')
 # Every recorded cumulative update file must be represented by exact latest bytes.
 coverage={}
 for meta in ROOT.glob('downloads/*/patch-build.json'):
  row=json.loads(meta.read_text());v=tuple(int(x)for x in row['version'].split('.'))
  if not isinstance(row.get('files'),list):continue
  for item in row['files']:
   if item['path'] not in coverage or v>coverage[item['path']][0]:coverage[item['path']]=(v,item)
 for name,(_,item)in coverage.items():assert name in files and sha(files[name])==item['sha256'],name
 assert not any(any(k in n.lower() for k in ['cookies','login data','profile/','__pycache__','.pyc'])for n in files)
 manifest={'version':VERSION,'base_installer_sha256':BASE_SHA,'base_payload_sha256':'8178af48a4db6180eb0fb3ef042b04ea21617c7380ca2e106d8e967990eb0c35','files':[{'path':n,'bytes':len(b),'sha256':sha(b)}for n,b in sorted(files.items())]}
 manifest['code_sha256']=sha(json.dumps(manifest['files'],sort_keys=True).encode())
 output=ROOT/'downloads/windows-fresh-129';output.mkdir(exist_ok=True)
 buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
  z.write(Path(__file__).with_name('install.ps1'),'apply_update.ps1')
  z.writestr('fresh-manifest.json',json.dumps(manifest,indent=2))
  for n,b in sorted(files.items()):z.writestr('files/'+n,b)
 payload=buf.getvalue();original=initial.read_bytes();pe=dnfile.dnPE(data=original);last=pe.sections[-1]
 assert not pe.OPTIONAL_HEADER.DATA_DIRECTORY[4].Size
 assert last.PointerToRawData+last.SizeOfRawData==len(original)
 offset=align(len(original),pe.OPTIONAL_HEADER.FileAlignment);rva=last.VirtualAddress+offset-last.PointerToRawData
 blob=struct.pack('<I',len(payload))+payload;data=bytearray(original)+bytes(offset-len(original))+blob
 data.extend(bytes(align(len(data),pe.OPTIONAL_HEADER.FileAlignment)-len(data)))
 changes=[]
 def put(owner,field,value):
  at=owner.get_field_absolute_offset(field);changes.append((at,4));struct.pack_into('<I',data,at,value)
 raw=len(data)-last.PointerToRawData;virtual=offset+len(blob)-last.PointerToRawData
 put(last,'SizeOfRawData',raw);put(last,'Misc_VirtualSize',virtual);put(last,'Characteristics',(last.Characteristics|0x40000040)&~0x02000000)
 put(pe.OPTIONAL_HEADER,'SizeOfImage',align(last.VirtualAddress+virtual,pe.OPTIONAL_HEADER.SectionAlignment))
 put(pe.OPTIONAL_HEADER,'SizeOfInitializedData',pe.OPTIONAL_HEADER.SizeOfInitializedData+raw-last.SizeOfRawData)
 put(pe.net.struct,'ResourcesRva',rva);put(pe.net.struct,'ResourcesSize',len(blob))
 comparison=bytearray(data[:len(original)])
 for at,size in changes:comparison[at:at+size]=original[at:at+size]
 assert comparison==original
 exe=output/NAME;exe.write_bytes(data);assert embedded(exe)==payload
 with zipfile.ZipFile(io.BytesIO(embedded(exe)))as z:
  assert z.testzip() is None
  for n,b in files.items():assert z.read('files/'+n)==b
 # Compile every Python module in the actual fresh-install merged tree.
 merged={n:base.read(n)for n in base.namelist()if n.startswith('app/local_engine/')and n.endswith('.py')}
 merged.update({n:b for n,b in files.items()if n.endswith('.py')})
 for n,b in merged.items():compile(b,n,'exec')
 report={'version':VERSION,'file':NAME,'bytes':len(data),'sha256':sha(data),'code_files':len(files),'all_recorded_update_files_verified':True,'base_installer_verified':True,'base_zip_crc_verified':True,'embedded_zip_verified':True,'python_compile_verified':True,'launcher_code_unchanged':True,'windows_execution_tested':False,'online_account_tested':False,'requires_network':True,'base_download_bytes':args.base.stat().st_size,'base_expanded_bytes':sum(i.file_size for i in base.infolist()),'overlay_expanded_bytes':sum(map(len,files.values())),'code_sha256':manifest['code_sha256']}
 exe.with_suffix('.exe.sha256').write_text(report['sha256']+'  '+NAME+'\n')
 (output/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
 (output/'code-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
