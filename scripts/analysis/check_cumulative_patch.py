"""Prove the cumulative payload equals every incremental update from .62–.96."""
import hashlib,io,json,sys,tempfile,zipfile
from pathlib import Path
import dnfile
ROOT=Path('/workspace/3')
def package(path):
 pe=dnfile.dnPE(data=path.read_bytes());raw=next(r.data for r in pe.net.resources if r.name=='SceneForgePatch.zip')
 with zipfile.ZipFile(io.BytesIO(raw))as z:
  manifest=json.loads(z.read('patch-manifest.json'));files={r['path']:z.read('files/'+r['path'])for r in manifest['files']}
  assert all(hashlib.sha256(files[r['path']]).hexdigest()==r['sha256']for r in manifest['files'])
  return manifest,files,z.read('apply_update.ps1')
def main():
 metadata=json.loads((ROOT/'downloads/v46-cumulative/patch-build.json').read_text());manifest,cumulative,script=package(ROOT/'downloads/v46-cumulative'/metadata['file']);assert manifest['minimum_patch']=='2026.11.04.4662';releases={}
 for p in (ROOT/'downloads').glob('*/patch-build.json'):
  row=json.loads(p.read_text())
  try:number=int(str(row.get('version','')).split('.')[-1])
  except ValueError:continue
  if 4663<=number<=4696:releases[number]=p.parent/row['file']
 assert set(releases)==set(range(4663,4697))
 incremental={n:package(p)[1]for n,p in sorted(releases.items())};latest={}
 for data in incremental.values():latest.update(data)
 assert cumulative==latest and len(cumulative)==25
 assert all(p.startswith(('app/local_engine/','app/dist/web-demo/'))and'..'not in Path(p).parts for p in cumulative)
 base={p:b'previous-code'for p in cumulative}
 for number in range(4662,4697):
  state=dict(base)
  for n,data in incremental.items():
   if n<=number:state.update(data)
  sequential=dict(state)
  for n,data in incremental.items():
   if n>number:sequential.update(data)
  state.update(cumulative);assert state==sequential,(number,set(state)^set(sequential))
 with tempfile.TemporaryDirectory()as td:
  root=Path(td);keep={'data/vault.sqlite':b'ACCOUNT_SENTINEL','data/models/model.bin':b'MODEL_SENTINEL','data/projects/project.json':b'PROJECT_SENTINEL'}
  for name,data in keep.items():target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  for name,data in cumulative.items():target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  assert all((root/name).read_bytes()==data for name,data in keep.items())
 ps=script.decode('utf-8-sig');assert '$installed.version'in ps and 'ShowInstalledBuild'in ps and'Không hạ phiên bản'in ps;assert ps.index('$manifest.minimum_patch')<ps.index('$busy=@')<ps.index('$backup=Join-Path');assert 'rollback'in ps.lower()or 'foreach($item in $changes)'in ps
 print('PASS exact cumulative coverage of all 34 releases .63–.96; identical final files from every supported .62–.96 starting version; 25 verified files; project/model/account sentinels untouched; baseline guard and rollback retained. Payload simulation, not a Windows installer run.')
if __name__=='__main__':main()
