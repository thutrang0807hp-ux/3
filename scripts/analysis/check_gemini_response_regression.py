"""Compare released .162 and the fix against the identical replacing Gemini response DOM."""
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
old=subprocess.check_output(['git','show','459cc13:veo-node-v46/scripts/browser-extension/gemini-tab.js'],cwd=ROOT,text=True)
new=(ROOT/'veo-node-v46/scripts/browser-extension/gemini-tab.js').read_text()
fixture='''()=>{window.sends=0;const c=document.createElement('canvas');c.width=300;c.height=500;window.png=c.toDataURL();document.querySelector('button').onclick=()=>{sends++;const q=document.createElement('user-query');q.textContent='Original';document.body.append(q);const placeholder=document.createElement('model-response');placeholder.textContent='Creating';document.body.append(placeholder);setTimeout(()=>{const output=document.createElement('model-response');output.innerHTML='<generated-image><img src="'+png+'"></generated-image>';placeholder.replaceWith(output);},400);};}'''
with sync_playwright()as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for source,expected in [(old,False),(new,True)]:
  p=b.new_page();p.set_content('<rich-textarea><div contenteditable="true" role="textbox"></div></rich-textarea><button class="send-button">Send</button>');p.add_script_tag(content=source);p.evaluate(fixture)
  p.evaluate("()=>{sceneForgeGeminiTab({operation:'generate',kind:'image',prompt:'Original',request_id:'regression'}).then(r=>window.result=r);}")
  p.wait_for_timeout(2000);assert p.evaluate('!!document.querySelector("generated-image img")?.naturalWidth')
  assert p.evaluate('!!window.result?.ok')is expected
  assert p.evaluate('sends')==1;p.close()
 b.close()
print('PROVED .162 fails to read an already-visible generated image after response replacement; fixed source receives it from identical DOM with one prompt send')
