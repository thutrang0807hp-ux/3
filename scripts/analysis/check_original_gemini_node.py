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
 assert z.read('runtime/gemini.mjs').decode()==adapter
 assert z.read('runtime/upstream-gemini.mjs').decode()==original
 assert json.loads(z.read('runtime/node_modules/playwright-core/package.json'))['version']=='1.62.1'
print('PASS exact original send/read/download functions, Node/CDP, playwright-core 1.62.1 and runtime checksum')

# Entire run() path equals upstream after removing exactly the two allowed insertions.
extra='      await attachReferences(page, request.references);\n      if (request.action === "text") {\n        return {text:await waitForText(page,await submit(page,editor,request.prompt))};\n      }\n'
def runpart(text):return text[text.index('async function run('):text.index('async function main(')]
assert runpart(adapter).replace(extra,'')==runpart(original)
with zipfile.ZipFile(ROOT/'veo-node-v46/vendor/gemini-native-node.zip')as z:
 assert z.read('repo_bridge.py')==(folder/'upstream-browser-bridge.py').read_bytes()
print('PASS whole upstream run/start/request/create_image path retained, with only reference attachment and raw-text insertion')

assert hashlib.sha256((folder/'upstream-browser-bridge.py').read_bytes()).hexdigest()=='a861ddfc4ec841fcbac0adccde9b779bece38caa2ee3327e57bbaf40a71592fa'
