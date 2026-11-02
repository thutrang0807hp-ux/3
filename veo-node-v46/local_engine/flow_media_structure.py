"""Bounded DOM inspection of media ancestors, frames and open shadow roots.

No clicks, downloads, navigation, ledger writes or video attribution.
"""
import asyncio
import time
from urllib.parse import urlsplit

STRUCTURE = r'''() => {
    const visible = e => {
        const r=e.getBoundingClientRect();
        const s=getComputedStyle(e);
        return r.width>0 && r.height>0 && s.visibility!=='hidden' && s.display!=='none';
    };
    const nodes=[],roots=[document];let rootCount=0,truncated=false;
    while(roots.length && nodes.length<12000 && rootCount<24){
        const root=roots.shift();rootCount++;
        for(const e of root.querySelectorAll('*')){
            if(nodes.length>=12000){truncated=true;break;}
            nodes.push(e);
            if(e.shadowRoot)roots.push(e.shadowRoot);
        }
    }
    if(roots.length)truncated=true;
    const mediaSelector='img,video,[data-media-id],[data-generation-id],[data-asset-id],[role="progressbar"]';
    const percent=e=>['SPAN','DIV'].includes(e.tagName)&&/^\s*\d{1,3}\s*%\s*$/.test(e.innerText||'');
    const all=nodes.filter(e=>visible(e)&&(e.matches(mediaSelector)||percent(e)));
    // Prioritize videos/progress over static image thumbnails.
    const prioritized=[...all.filter(e=>e.matches('video,[role="progressbar"]')||percent(e)),...all.filter(e=>!e.matches('video,[role="progressbar"]')&&!percent(e))];
    const parent=e=>e.parentElement || e.getRootNode()?.host || null;
    const attrs=e=>Object.fromEntries([...e.attributes].filter(a=>
        /^(id|class|role|aria-label|aria-valuenow|aria-valuemax|data-media-id|data-asset-id|data-generation-id|data-media-type|data-mime-type|data-kind|data-state)$/.test(a.name)
    ).map(a=>[a.name,a.value.slice(0,240)]));
    const describe=e=>{
        const editor=!!e.querySelector('textarea,[contenteditable="true"],[role="textbox"]');
        const mediaCount=e.querySelectorAll('[data-media-id],[data-asset-id],[data-generation-id]').length;
        const controls=[...e.querySelectorAll('button,[role="button"],a,[role="menuitem"]')]
            .filter(visible).slice(0,12).map(b=>({tag:b.tagName.toLowerCase(),role:b.getAttribute('role'),
                name:(b.getAttribute('aria-label')||b.innerText||'').trim().slice(0,160)}));
        return {tag:e.tagName.toLowerCase(),attributes:attrs(e),
            text:editor?'':(e.innerText||'').slice(0,500),editor_present:editor,
            nested_media_ids:mediaCount,images:e.querySelectorAll('img').length,
            videos:e.querySelectorAll('video').length,controls};
    };
    return {root_count:rootCount,node_count:nodes.length,truncated,
        visible_media_nodes:all.length,
        media:prioritized.slice(0,60).map(e=>{
            const ancestors=[];let p=parent(e);
            for(let depth=0;p&&depth<6&&!['BODY','HTML'].includes(p.tagName);depth++,p=parent(p)){
                const details=describe(p);ancestors.push(details);
                if(details.editor_present || details.nested_media_ids>2)break;
            }
            return {element:describe(e),in_shadow_root:e.getRootNode()!==document,ancestors};
        })};
}'''

async def collect_media_structure(page, *, budget=3.0):
    """Return a bounded snapshot for each observed frame; preserve per-frame failures."""
    deadline=asyncio.get_running_loop().time()+budget
    frames=list(page.frames)
    entries=[]
    for index,frame in enumerate(frames[:12]):
        # Never include paths/query strings, which may contain signed URLs.
        try:
            parsed=urlsplit(frame.url)
            origin=(parsed.scheme+'://'+(parsed.hostname or '')) if parsed.netloc else parsed.scheme
        except ValueError:
            origin='unavailable'
        entry={'index':index,'main_frame':frame is page.main_frame,'origin':origin}
        entries.append(entry)
        remaining=deadline-asyncio.get_running_loop().time()
        if remaining<=0:
            entry['inspection']='budget_exhausted';continue
        try:
            if frame is not page.main_frame:
                element=await asyncio.wait_for(frame.frame_element(),min(.3,remaining))
                remaining=deadline-asyncio.get_running_loop().time()
                if remaining<=0:
                    entry['inspection']='budget_exhausted';continue
                shown=await asyncio.wait_for(element.is_visible(),min(.3,remaining))
                entry['iframe_visible']=shown
                if not shown:
                    entry['inspection']='hidden_frame_metadata_only';continue
            remaining=deadline-asyncio.get_running_loop().time()
            if remaining<=0:
                entry['inspection']='budget_exhausted';continue
            entry['structure']=await asyncio.wait_for(frame.evaluate(STRUCTURE),min(1.2,remaining))
            entry['inspection']='read'
        except Exception as exc:
            entry['inspection']='unavailable';entry['error_type']=type(exc).__name__
    return {'checked_at':time.time(),'frame_count':len(frames),'frames_truncated':len(frames)>12,
            'frames':entries,'read_only':True,'video_attribution_confirmed':False}
