"""Working 0.4.11 sender/receiver preserved; references extended to an ordered list."""
from pathlib import Path
import json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[2];folder=ROOT/'veo-node-v46/scripts/gemini-native'
original=(folder/'upstream-gemini.mjs').read_text();adapter=(folder/'gemini.mjs').read_text()
def block(s,name):
 a=s.index('function '+name+'(');return s[a:s.index('\n}',a)+2]
for name in ['imageSource','imageInstruction','editorFor','submit','waitForText','waitForImage','downloadImage','downloadFromGemini','copyImagePixels','saveResult']:
 assert block(original,name)==block(adapter,name),name
assert "const references = Array.isArray(path) ? path : [path];" in adapter
assert 'new Function' not in adapter and 'sendKnownFrame' not in adapter and 'prepareImageMode' not in adapter
assert 'await attachReference(page, references)' in adapter
assert 'const answer = await submit(page, editor, instruction)' in adapter
meta=json.loads((ROOT/'veo-node-v46/vendor/gemini-native-node.json').read_text())
archive=ROOT/'veo-node-v46/vendor/gemini-native-node.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==meta['sha256']
with zipfile.ZipFile(archive) as z:
 assert z.read('runtime/gemini.mjs').decode()==adapter
 assert z.read('runtime/upstream-gemini.mjs').decode()==original
 assert z.read('repo_bridge.py')==(folder/'upstream-browser-bridge.py').read_bytes()
 assert json.loads(z.read('runtime/node_modules/playwright-core/package.json'))['version']=='1.62.1'
print('PASS 0.4.11 original 10 helpers, ordered reference list, no legacy sender or model-menu changes, packaged runtime hashes')
