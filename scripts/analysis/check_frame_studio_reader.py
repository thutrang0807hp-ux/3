"""Actual unmodified upstream sender + attachment adapter: same-turn receive never sends again."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright()as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=b.new_page();p.set_content('<rich-textarea><div contenteditable="true" role="textbox"></div></rich-textarea><button class="send-button" aria-label="Send message">Send</button>')
 p.add_script_tag(path=str(ROOT/'veo-node-v46/scripts/browser-extension/studio-gemini-original.js'));p.add_script_tag(path=str(ROOT/'veo-node-v46/scripts/browser-extension/frame-studio-tab.js'))
 p.evaluate('''()=>{window.sends=0;const c=document.createElement('canvas');c.width=300;c.height=500;window.png=c.toDataURL();document.querySelector('button').onclick=()=>{sends++;const n=document.createElement('model-response');n.innerHTML='<generated-image><img src="'+png+'"></generated-image>';document.body.append(n);};}''')
 result=p.evaluate("SFStudioBridge.run({operation:'generate',kind:'image',prompt:'KEEP EXISTING PROMPT',request_id:'own',references:[]})");assert result['ok']and result['prompt']=='KEEP EXISTING PROMPT'and p.evaluate('sends')==1
 p.add_script_tag(path=str(ROOT/'veo-node-v46/scripts/browser-extension/frame-studio-tab.js'))
 received=p.evaluate("SFStudioBridge.run({operation:'receive',kind:'image',target_job:'own'})");assert received['image']==result['image']and p.evaluate('sends')==1
 p.evaluate('SFStudioTurn.result={}')
 read=p.evaluate("SFStudioBridge.run({operation:'receive',kind:'image',target_job:'own'})");assert read['ok']and read['image']==result['image']and p.evaluate('sends')==1
 wrong=p.evaluate("SFStudioBridge.run({operation:'receive',kind:'image',target_job:'another-scene'})");assert not wrong['ok']and p.evaluate('sends')==1
 b.close()
print('PASS exact upstream generator, prompt retained, cached and sole-turn receive use original image, cross-scene read rejected, one send only')
