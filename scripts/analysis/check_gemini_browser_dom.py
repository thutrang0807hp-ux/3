"""Execute the actual injected browser function against a controlled Gemini DOM, not a live account."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright()as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page()
 page.set_content('''<rich-textarea><div contenteditable="true" role="textbox"></div></rich-textarea><input type="file" multiple><button class="send-button" aria-label="Send message">Send</button>''')
 page.add_script_tag(path=str(ROOT/'veo-node-v46/scripts/browser-extension/gemini-tab.js'))
 page.evaluate('''()=>{window.sends=0;document.querySelector('input').onchange=e=>{for(const file of e.target.files){const n=document.createElement('div');n.className='file-preview';n.textContent=file.name;document.body.append(n);}};document.querySelector('button').onclick=()=>{sends++;window.sentText=document.querySelector('[contenteditable]').textContent;const node=document.createElement('model-response');const c=document.createElement('canvas');c.width=300;c.height=500;c.getContext('2d').fillRect(0,0,300,500);node.innerHTML='<generated-image><img src="'+c.toDataURL('image/png')+'"></generated-image>';document.body.append(node);};}''')
 assert page.evaluate('sceneForgeGeminiTab({operation:"identity"})')=={'ok':True}
 ref={'mime_type':'image/png','data':'aGVsbG8='}
 result=page.evaluate('(references)=>sceneForgeGeminiTab({operation:"generate",request_id:"original-turn",kind:"image",prompt:"KEEP PRODUCT EXACTLY",references})',[ref,ref])
 assert result['ok']and result['mime']=='image/png'and result['image'].startswith('iVBOR')
 assert page.evaluate('sends===1&&document.querySelector("input").files.length===2&&sentText.includes("KEEP PRODUCT EXACTLY")')
 page.evaluate('''()=>{const extra=document.createElement('model-response');extra.innerHTML='<p>Later unrelated turn</p>';document.body.append(extra);}''')
 recovered=page.evaluate('sceneForgeGeminiTab({operation:"receive",target_job:"original-turn",kind:"image"})');assert recovered['image']==result['image']and page.evaluate('sends')==1
 page.evaluate('''()=>{document.querySelector('button').onclick=()=>{sends++;const r=document.createElement('model-response');r.innerHTML='<message-content>EXACT TEXT RESULT</message-content>';document.body.append(r);};}''')
 text=page.evaluate('sceneForgeGeminiTab({operation:"generate",kind:"text",prompt:"Return text",references:[]})');assert text['ok']and text['text']=='EXACT TEXT RESULT'
 assert page.evaluate('sends')==2
 page.locator('input').evaluate('(e)=>e.remove()')
 failed=page.evaluate('(references)=>sceneForgeGeminiTab({operation:"generate",kind:"image",prompt:"Do not send without refs",references})',[ref])
 assert failed['code']=='GEMINI_BROWSER_ATTACH_FAILED'and failed['accepted']is False and page.evaluate('sends')==2
 # Actual popup must negotiate browser protocol before any cookie-export code.
 import re
 html=(ROOT/'veo-node-v46/scripts/browser-extension/popup.html').read_text();html=re.sub(r'<script[\s\S]*?</script>','',html)
 page.set_content(html)
 page.evaluate('''()=>{window.cookieReads=0;window.pairPosts=[];window.chrome={tabs:{query:async()=>[{id:7,active:true,url:'https://gemini.google.com/app'}]},cookies:{getAll:async()=>{cookieReads++;throw Error('Cookie export forbidden');}},runtime:{sendMessage:async m=>{window.pairMessage=m;return{ok:true};}}};window.fetch=async(url,options)=>{pairPosts.push(JSON.parse(options.body));return{ok:true,json:async()=>url.endsWith('/claim')?{protocol:5,services:['gemini_chat'],service:'gemini_chat',submission:'fixture',relay:{id:'route',browser_key:'key'}}:{accepted:true,state:'checking'}};};}''')
 page.add_script_tag(path=str(ROOT/'veo-node-v46/scripts/browser-extension/popup.js'))
 page.locator('#code').fill('12345678');page.locator('#submit').click();page.wait_for_function('document.querySelector("#connect").hidden')
 assert page.evaluate('cookieReads===0&&pairMessage.type==="pairGemini"&&pairMessage.link.tabId===7&&pairPosts.every(p=>p.protocol===5&&!p.cookies)')
 browser.close()
print('PASS actual browser DOM function: two source/product attachments, one prompt send, image bytes, text result; receive never sends; missing upload control prevents generation')
