"""The source-proven send/read/download functions must not be rewritten."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[2];folder=ROOT/'veo-node-v46/scripts/gemini-native'
original=(folder/'upstream-gemini.mjs').read_text();assert hashlib.sha256(original.encode()).hexdigest()=='d024a7fda7df7e2b315cd0507d6409c498531117c3df839780fc195f58763a48';adapter=(folder/'gemini.mjs').read_text()
def block(text,name):
 start=text.index('function '+name+'(');return text[start:text.index('\n}',start)+2]
for name in ['imageSource','imageInstruction','editorFor','submit','waitForText','waitForImage','downloadImage','downloadFromGemini','copyImagePixels','saveResult']:assert block(original,name)==block(adapter,name),name+' was changed'
assert 'chromium.connectOverCDP("http://127.0.0.1:" + port' in adapter
meta=json.loads((ROOT/'veo-node-v46/vendor/gemini-native-node.json').read_text());data=(ROOT/'veo-node-v46/vendor/gemini-native-node.zip').read_bytes();assert hashlib.sha256(data).hexdigest()==meta['sha256']
with zipfile.ZipFile(ROOT/'veo-node-v46/vendor/gemini-native-node.zip')as z:
 assert z.read('gemini.mjs').decode()==adapter
 assert z.read('upstream-gemini.mjs').decode()==original
 assert json.loads(z.read('node_modules/playwright-core/package.json'))['version']=='1.62.1'
print('PASS exact original send/read/download functions, Node/CDP, playwright-core 1.62.1 and runtime checksum')
