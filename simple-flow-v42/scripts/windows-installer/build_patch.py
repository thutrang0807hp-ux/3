"""Small, self-extracting update for the verified v2 baseline; no models/runtime reinstall."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,tempfile,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
VERSION='2026.10.31.42'
BASELINE='8178af48a4db6180eb0fb3ef042b04ea21617c7380ca2e106d8e967990eb0c35'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--desktop',type=Path,required=True);ap.add_argument('--launcher-template',type=Path,help='Reuse the generic managed launcher from a prior update; requires dnfile');ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='sf-patch-')as tmp:
  stage=Path(tmp);files=stage/'files';files.mkdir()
  for p in args.desktop.iterdir():
   if p.is_file():shutil.copy2(p,files/p.name)
  for name in ['windows_bootstrap.py','paths.py']:
   target=files/'app'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/name,target)
  for name in ['__init__.py','__main__.py','quiet_process.py','flow_account_engine.py','google_login.py','simple_flow.py','simple_flow_upload.py','flow_web_login.py','flow_ui_session.py','flow_ui_driver.py','flow_extension_driver.py','flow_managed_driver.py','flow_browser_probe.py','gemini_chat.py','gemini_chat_worker.py','gemini_conversations.py','server.py','cpu_worker.py','proxy_frames.py','browser_bridge.py','frame_quality.py','flow_accounts.py','account_pool.py','flow_provider.py','flow_connection.py','flow_import_trace.py','flow_browser_context.py','flow_browser_relay.py','flow_native_transport.py','image_transport.py','flow_projects.py','flow_task_journal.py']:
   target=files/'app/local_engine'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'local_engine'/name,target)
  for name in ['index.html','studio.html','workflow.html','photos.html','native/index.html','storage-demo.html','batch-design-demo.html']:
   target=files/'app/dist/web-demo'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'dist/web-demo'/name,target)
  for p in (ROOT/'scripts/browser-extension').iterdir():
   if p.is_file():
    target=files/'app/scripts/browser-extension'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
  target=files/'app/scripts/browser-extension-package.zip';shutil.copy2(ROOT/'scripts/browser-extension-package.zip',target)
  manifest={'version':VERSION,'supported_payloads':[BASELINE],'minimum_patch':'2026.10.29.14','files':[{'path':p.relative_to(files).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(files.rglob('*'))if p.is_file()]}
  (stage/'patch-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');shutil.copy2(HERE/'apply_update.ps1',stage/'apply_update.ps1')
  archive=args.output/'SceneForge-update-payload.zip'
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
   for p in sorted(stage.rglob('*')):
    if p.is_file():z.write(p,p.relative_to(stage).as_posix())
  exe=args.output/'SceneForge-Update-20261031-v42.exe'
  if args.launcher_template:
   import dnfile,struct
   original=args.launcher_template.read_bytes();pe=dnfile.dnPE(data=original)
   if pe.OPTIONAL_HEADER.DATA_DIRECTORY[4].Size:raise ValueError('Do not modify a signed launcher')
   resources=list(pe.net.mdtables.ManifestResource)
   if len(resources)!=1 or str(resources[0].Name)!='SceneForgePatch.zip':raise ValueError('Unexpected launcher resources')
   offset=pe.get_offset_from_rva(pe.net.struct.ResourcesRva)+resources[0].Offset
   capacity=struct.unpack_from('<I',original,offset)[0];payload=archive.read_bytes()
   if len(payload)>capacity:raise ValueError('Payload exceeds existing launcher capacity; compile on Windows')
   # Only replace the embedded ZIP; preserve launcher IL/metadata and all other PE data.
   data=bytearray(original);data[offset:offset+4+capacity]=struct.pack('<I',len(payload))+payload+bytes(capacity-len(payload))
   exe.write_bytes(data)
   check=dnfile.dnPE(str(exe));actual=next(r.data for r in check.net.resources if r.name=='SceneForgePatch.zip')
   if actual!=payload:raise ValueError('Embedded payload verification failed')
  else:
   compiler=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
   subprocess.run([str(compiler),'/nologo','/target:winexe','/platform:x64','/optimize+',f'/out:{exe}','/reference:System.Windows.Forms.dll','/reference:System.IO.Compression.dll',f'/resource:{archive},SceneForgePatch.zip',str(HERE/'UpdateLauncher.cs')],check=True)
  report={'version':VERSION,'file':exe.name,'bytes':exe.stat().st_size,'sha256':sha(exe),'files':len(manifest['files']),'models_included':False,'baseline_payload_sha256':BASELINE}
  exe.with_suffix('.exe.sha256').write_text(report['sha256']+'  '+exe.name+'\n');(args.output/'patch-build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
