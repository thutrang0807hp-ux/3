"""Build .119 as a one-module update; preserve every installed UI/Flow change."""
import hashlib,io,json,struct,zipfile
from pathlib import Path
import dnfile
ROOT=Path(__file__).resolve().parents[3]
VERSION='2026.11.12.46119'
NAME='SceneForge-Update-20261112-v46.119-Video-Link-Audio.exe'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 template=ROOT/'downloads/v46/SceneForge-Update-20261101-v46.exe'
 original=template.read_bytes()
 assert sha(original)==json.loads(template.with_name('patch-build.json').read_text())['sha256']
 source=ROOT/'veo-node-v46/local_engine/video_import.py';name='app/local_engine/video_import.py'
 manifest={'version':VERSION,'supported_payloads':['8178af48a4db6180eb0fb3ef042b04ea21617c7380ca2e106d8e967990eb0c35'],'minimum_patch':'2026.11.04.4662','files':[{'path':name,'bytes':source.stat().st_size,'sha256':sha(source.read_bytes())}]}
 output=ROOT/'downloads/v46-video-link-audio';output.mkdir(exist_ok=True)
 pinned=output/'patch-build.json'
 if pinned.exists():assert json.loads(pinned.read_text())['files']==manifest['files'],'Published release source changed; increment version'
 buffer=io.BytesIO()
 with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('patch-manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
  z.write(Path(__file__).with_name('apply_video_import_merge.ps1'),'apply_update.ps1')
  z.write(source,'files/'+name)
 payload=buffer.getvalue();pe=dnfile.dnPE(data=original)
 assert not pe.OPTIONAL_HEADER.DATA_DIRECTORY[4].Size
 resources=list(pe.net.mdtables.ManifestResource);assert len(resources)==1 and str(resources[0].Name)=='SceneForgePatch.zip'
 offset=pe.get_offset_from_rva(pe.net.struct.ResourcesRva)+resources[0].Offset
 capacity=struct.unpack_from('<I',original,offset)[0];assert len(payload)<=capacity
 data=bytearray(original);data[offset:offset+4+capacity]=struct.pack('<I',len(payload))+payload+bytes(capacity-len(payload))
 assert data[:offset]==original[:offset] and data[offset+4+capacity:]==original[offset+4+capacity:]
 embedded=next(r.data for r in dnfile.dnPE(data=bytes(data)).net.resources if r.name=='SceneForgePatch.zip');assert embedded==payload
 with zipfile.ZipFile(io.BytesIO(embedded)) as z:
  assert z.testzip() is None and z.read('files/'+name)==source.read_bytes()
  assert json.loads(z.read('patch-manifest.json'))==manifest
 exe=output/NAME;exe.write_bytes(data);digest=sha(data)
 exe.with_suffix('.exe.sha256').write_text(digest+'  '+NAME+'\n')
 report={'version':VERSION,'file':NAME,'bytes':len(data),'sha256':digest,'files':manifest['files'],'minimum_patch':manifest['minimum_patch'],'embedded_files_verified':True,'launcher_code_unchanged':True,'real_ffmpeg_split_audio_merge_tested':True,'live_youtube_tested':False,'windows_installer_tested':False}
 pinned.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
