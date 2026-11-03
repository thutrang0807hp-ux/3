import hashlib,io,json,re,subprocess,zipfile
from pathlib import Path
import dnfile
ROOT=Path(__file__).resolve().parents[2]
def sha(data):return hashlib.sha256(data).hexdigest()
base=ROOT/'downloads/v46/SceneForge-Veo-v46-Source.zip'
files={}
with zipfile.ZipFile(base) as z:
 for item in z.infolist():
  if not item.is_dir():files[item.filename]=z.read(item)
releases=[]
for exe in ROOT.glob('downloads/v46*/*.exe'):
 pe=dnfile.dnPE(str(exe))
 if not pe.net:continue
 resource=next((r.data for r in pe.net.resources if r.name=='SceneForgePatch.zip'),None)
 if resource is None:continue
 with zipfile.ZipFile(io.BytesIO(resource)) as z:
  manifest=json.loads(z.read('patch-manifest.json'))
  version=manifest['version'];parts=version.split('.')
  if not parts[3].startswith('46'):continue
  minor=int(parts[3][2:] or (parts[4] if len(parts)>4 else '0'))
  if minor>50:continue
  payload={item['path']:z.read('files/'+item['path']) for item in manifest['files']}
  for item in manifest['files']:assert sha(payload[item['path']])==item['sha256'],(exe,item)
  releases.append((minor,version,exe,sha(exe.read_bytes()),manifest,payload,z.read('apply_update.ps1')))
releases.sort(key=lambda row:(row[0],row[1],str(row[2])))
provenance=[]
for minor,version,exe,digest,manifest,payload,apply in releases:
 for name,data in payload.items():
  if name.startswith('app/'):files[name[4:]]=data
 provenance.append(dict(version=version,exe=str(exe.relative_to(ROOT)),exe_sha256=digest,files=manifest['files']))
 if minor==50:
  files['v50-patch/patch-manifest.json']=json.dumps(manifest,indent=2).encode()
  files['v50-patch/apply_update.ps1']=apply
  for name,data in payload.items():files['v50-patch/files/'+name]=data
  for name,data in payload.items():assert files[name.removeprefix('app/')]==data
assert any(row['version']=='2026.11.03.4650' for row in provenance)
if 'SOURCE-MANIFEST.json' in files:files['provenance/baseline-SOURCE-MANIFEST.json']=files.pop('SOURCE-MANIFEST.json')
if 'README.md' in files:files['provenance/README-baseline-v46.md']=files.pop('README.md')
files['provenance/releases-applied.json']=json.dumps({'baseline_source_zip':str(base.relative_to(ROOT)),'baseline_source_sha256':sha(base.read_bytes()),'source_commit':'8a22596','patches':provenance},indent=2).encode()
for name in ['build_direct_cli_patch.py','apply_cli_update.ps1']:
 path='veo-node-v46/scripts/windows-installer/'+name
 files['scripts/windows-installer/'+name]=subprocess.check_output(['git','show','8a22596:'+path],cwd=ROOT)
files['README.md']='''# SceneForge .50 — mã nguồn nguyên trạng để kiểm tra

Đây là mã nguồn ứng dụng ghép từ Source ZIP v46 đã công bố và các payload cập
nhật v46.0 đến v46.50 đã phát hành. Mỗi tệp vá được lấy từ EXE, kiểm SHA256 rồi
áp vào nguồn nền. Danh sách EXE/phiên bản/hash nằm trong provenance/releases-applied.json.
Không lấy bản sửa mới từ working tree hoặc dữ liệu cá nhân trên máy người dùng.

## Hai tệp của riêng bản .50

- local_engine/simple_flow.py: nhánh nút tạo gọi flow_gflow_cli.generate sau chuẩn bị.
- local_engine/flow_gflow_cli.py: tìm repo trong Downloads, gọi python -m gflow_cli
  video r2v, giữ stdout/stderr, xử lý JSON và nhận video về cảnh.
- v50-patch/: nguyên manifest, apply_update.ps1 và hai tệp trích từ EXE .50.
- scripts/windows-installer/build_direct_cli_patch.py: script đóng gói .50 ở commit 8a22596.

## Lỗi đã thấy — giữ nguyên trong gói này

command() vẫn có '--duration', '8'. Báo cáo người dùng xác nhận CLI ConfigurationError
exit 11 vì tài khoản/model không có điều khiển 8s. Gói này KHÔNG bỏ tham số đó.
Gói này cũng KHÔNG tự coi lượt exit 11 là chưa gửi: mã .50 đánh dấu sent trước
khi gọi CLI nên kết quả nằm unknown. Đây là hành vi nguyên trạng để kiểm tra.

## Phạm vi

Các module worker/SDK cũ có thể vẫn còn từ bản cập nhật trước nhưng nhánh tạo .50
không gọi chúng. CLI và runtime gflow bên ngoài lấy từ bản GFlow trong Downloads;
chúng không được đóng trong EXE .50 và không thuộc source ZIP này. Không chứa
Python/Chrome/model binaries, cookie, tài khoản hoặc dữ liệu dự án người dùng.
Đây không phải ZIP toàn bộ lịch sử repository hay một EXE tự cài mới hoàn chỉnh.
'''.encode()
manifest=[dict(path=name,bytes=len(data),sha256=sha(data)) for name,data in sorted(files.items())]
files['SOURCE-MANIFEST-v50.json']=json.dumps(manifest,indent=2).encode()
output=ROOT/'downloads/v46-flow-cli-direct/SceneForge-v46.50-Full-Source.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,data in sorted(files.items()):z.writestr('SceneForge-v46.50/'+name,data)
with zipfile.ZipFile(output) as z:
 assert z.testzip() is None
 for item in manifest:assert sha(z.read('SceneForge-v46.50/'+item['path']))==item['sha256']
digest=sha(output.read_bytes());output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n')
print(json.dumps(dict(file=output.name,bytes=output.stat().st_size,files=len(files),patch_count=len(releases),sha256=digest)))
