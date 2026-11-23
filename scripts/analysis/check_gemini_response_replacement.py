"""Actual injected function must survive Gemini replacing its streaming response DOM."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright()as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=browser.new_page()
 p.set_content('<rich-textarea><div contenteditable="true" role="textbox"></div></rich-textarea><button class="send-button">Send</button>')
 p.add_script_tag(path=str(ROOT/'veo-node-v46/scripts/browser-extension/gemini-tab.js'))
 p.evaluate('''()=>{window.sends=0;const c=document.createElement('canvas');c.width=300;c.height=500;c.getContext('2d').fillRect(0,0,300,500);window.png=c.toDataURL();document.querySelector('button').onclick=()=>{sends++;const query=document.createElement('user-query');query.textContent='Original prompt';document.body.append(query);const placeholder=document.createElement('model-response');placeholder.textContent='Creating image';document.body.append(placeholder);setTimeout(()=>{const final=document.createElement('model-response');final.innerHTML='<generated-image><img src="'+png+'"></generated-image>';placeholder.replaceWith(final);},600);};}''')
 p.evaluate('''()=>{window.promise=sceneForgeGeminiTab({operation:'generate',kind:'image',prompt:'Original prompt',request_id:'owned'}).then(r=>window.result=r);}''')
 p.wait_for_function('window.result?.ok',timeout=5000)
 assert p.evaluate('sends')==1
 # Replacement after completion loses the marker. Recovery still owns the sole dedicated response.
 p.evaluate('''()=>{const old=document.querySelector('model-response');const replacement=old.cloneNode(true);replacement.removeAttribute('data-sf-gemini-turn');old.replaceWith(replacement);}''')
 result=p.evaluate("sceneForgeGeminiTab({operation:'receive',kind:'image',target_job:'owned'})")
 assert result['ok']and p.evaluate('sends')==1
 # Legacy .162 receipt: marker was attached to the removed placeholder, with no root-owner metadata.
 p.evaluate('''()=>{document.documentElement.removeAttribute('data-sf-gemini-owner');document.documentElement.removeAttribute('data-sf-gemini-response-index');}''')
 legacy=p.evaluate("sceneForgeGeminiTab({operation:'receive',kind:'image',target_job:'legacy',owned_single_turn:true})")
 assert legacy['ok']and p.evaluate('sends')==1
 # A generated image below the viewport must be activated before naturalWidth becomes available.
 p.evaluate('''()=>{document.querySelectorAll('user-query,model-response').forEach(n=>n.remove());document.querySelector('button').onclick=()=>{sends++;const n=document.createElement('model-response');n.innerHTML='<generated-image><img loading="lazy" data-src="'+png+'"></generated-image>';document.body.append(n);};const original=Element.prototype.scrollIntoView;Element.prototype.scrollIntoView=function(...args){if(this.matches('generated-image img')&&this.dataset.src)this.src=this.dataset.src;return original.apply(this,args);};}''')
 lazy=p.evaluate("sceneForgeGeminiTab({operation:'generate',kind:'image',prompt:'Lazy image',request_id:'lazy'})")
 assert lazy['ok']and p.evaluate('sends')==2
 browser.close()
print('PASS actual DOM: streaming placeholder replacement returns image; replacement after completion can be received; legacy sole-turn receipt recovered without sending another prompt')
