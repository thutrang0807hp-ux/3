"""Rebuild boundaries: exact upstream sender, unchanged prompt construction, one image owner."""
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
upstream=(ROOT/'veo-node-v46/vendor/studio-gemini-0.2.2/gemini.js').read_text()
assert (ROOT/'veo-node-v46/scripts/browser-extension/studio-gemini-original.js').read_text()==upstream.replace('export async function generateInGemini','async function generateInGemini',1)
adapter=(ROOT/'veo-node-v46/scripts/browser-extension/frame-studio-tab.js').read_text()
assert "generateInGemini(request.prompt,request.ratio||'9:16',false)"in adapter
assert upstream[upstream.index('  async function readImage(image) {'):upstream.index('\n  let revised')]in adapter
old=subprocess.check_output(['git','show','379ca83:scripts/ui/frame_direct_prompt.js'],cwd=ROOT,text=True)
new=(ROOT/'scripts/ui/frame_direct_prompt.js').read_text()
assert new==old.replace("j.sceneId===s.id&&j.kind==='image'","j.frameStudioVersion===164&&j.sceneId===s.id&&j.kind==='image'",1)
html=(ROOT/'workflow.html').read_text();before=subprocess.check_output(['git','show','379ca83:workflow.html'],cwd=ROOT,text=True)
for prefix in ['async function generationRefs(','imageFramePrompt=function(s,lang=', 'function imageBindings(']:
 assert next(l for l in html.splitlines()if l.startswith(prefix))==next(l for l in before.splitlines()if l.startswith(prefix))
assert (ROOT/'scripts/ui/frame_image_flow.js').read_text()in html
assert (ROOT/'scripts/ui/frame_studio_node.js').read_text()in html
assert "if(kind==='image')return processFrameImage"in html
assert "j.frameStudioVersion!==164"in html
print('PASS exact upstream generator (export removed only), exact upstream image decoder, prompt recipe/reference packing unchanged, one new image owner and legacy importer exclusion')
