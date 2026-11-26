"""Reproducible input pins; bundle the upstream Node/CDP connector without a Python port."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 node=Path('/tmp/sf-node-windows.zip');assert sha(node.read_bytes())=='4a191082e9706866830379d577d2cc8a50c776fcd9436a8d061b063ed0d9a0e3'
 runtime=ROOT/'veo-node-v46/scripts/gemini-native';modules=Path('/tmp/sf-gemini-node/node_modules');out=ROOT/'veo-node-v46/vendor/gemini-native-node.zip'
 assert json.loads((modules/'playwright-core/package.json').read_text())['version']=='1.62.1'
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
  with zipfile.ZipFile(node)as n:
   for name in ('node.exe','LICENSE'):z.writestr(name if name=='node.exe'else'NODE-LICENSE.txt',n.read('node-v22.23.5-win-x64/'+name))
  for f in sorted(runtime.iterdir()):
   if f.is_file():z.write(f,f.name)
  for f in sorted(modules.rglob('*')):
   if f.is_file():z.write(f,'node_modules/'+str(f.relative_to(modules)))
 meta={'sha256':sha(out.read_bytes()),'node':'22.23.5','node_archive_sha256':sha(node.read_bytes()),'playwright_core':'1.62.1','upstream_repository':'https://github.com/thutrang0807hp-ux/test-gemoni-chat','upstream_commit':'75f43c9','upstream_gemini_sha256':sha((runtime/'upstream-gemini.mjs').read_bytes()),'adapter_sha256':sha((runtime/'gemini.mjs').read_bytes())}
 out.with_suffix('.json').write_text(json.dumps(meta,indent=2));print('Packaged',out.stat().st_size,meta['sha256'])
if __name__=='__main__':main()
