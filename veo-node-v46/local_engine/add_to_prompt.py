"""Optional confirmation in a single-image resource dialog; never click globally."""
import asyncio
import re
import secrets
from .flow_prepare import reference_scope

async def click_add_to_prompt(page,log,check,report):
    """Discover exact actions, but only click inside a qualified image-detail region."""
    name=re.compile(r'^\s*(Thêm vào câu lệnh|Thêm vào lời nhắc|Thêm vào prompt|Add to prompt)\s*$',re.I)
    actions=page.get_by_role('button',name=name).or_(page.get_by_role('menuitem',name=name)).filter(visible=True)
    report['detail_action_count']=await actions.count()
    report['detail_regions']=[]
    regions=[]
    # Looking up text globally is discovery only, never permission to click.
    for action in (await actions.all())[:20]:
        for depth in range(1,9):
            region=action.locator('xpath=ancestor::*['+str(depth)+']')
            if not await region.count():break
            probe=await region.evaluate("""e=>{
                const visible=x=>{const r=x.getBoundingClientRect();return r.width>0&&r.height>0&&getComputedStyle(x).visibility!=='hidden'};
                const tag=e.tagName.toLowerCase(), role=e.getAttribute('role');
                const style=getComputedStyle(e);
                const images=[...e.querySelectorAll('img')].filter(visible).length;
                const editor=[...e.querySelectorAll('textarea,[contenteditable="true"],[role="textbox"]')].some(visible);
                const close=[...e.querySelectorAll('button,[role="button"]')].filter(visible).some(b=>/^(close|dismiss|đóng|đóng ảnh|close image|close preview|×|✕)$/i.test((b.getAttribute('aria-label')||b.innerText||'').trim()));
                const boundary=['body','html'].includes(tag);
                const detail=role==='dialog'||(['fixed','absolute'].includes(style.position)&&close);
                return {tag,role,position:style.position,images,editor,close,boundary,qualified:!boundary&&!editor&&images===1&&detail};
            }""")
            report['detail_regions'].append(probe)
            if probe['boundary']:break
            if probe['qualified']:
                # A marker identifies this actual DOM node; no guessed Flow classes.
                marker='data-sf-detail-'+secrets.token_hex(8)
                existing=await region.get_attribute('data-sf-detail-key')
                if not existing:
                    await region.evaluate('(e,key)=>e.setAttribute("data-sf-detail-key",key)',marker)
                    existing=marker
                if existing not in [key for key,_ in regions]:regions.append((existing,region))
                break
    report['qualified_detail_region_count']=len(regions)
    if len(regions)!=1:return False
    key,region=regions[0]
    scoped=region.get_by_role('button',name=name).or_(region.get_by_role('menuitem',name=name)).filter(visible=True)
    if await scoped.count()!=1 or not await scoped.is_enabled():return False
    await check()
    await scoped.click(timeout=3000)
    report['detail_region_method']='single_image_dialog_or_positioned_detail_with_close'
    log('Đã bấm Thêm vào câu lệnh trong vùng chi tiết một ảnh; tiếp tục chờ chip.')
    return True

async def wait_for_composer_attachment(page,check):
    while True:
        await check()
        _,scope=await reference_scope(page)
        if scope is not None:
            count=await scope.locator('img').evaluate_all('''xs=>xs.filter(e=>{const r=e.getBoundingClientRect();return r.width>=20&&r.height>=20}).length''')
            if count==1:return True
            if count>1:raise RuntimeError('Composer xuất hiện nhiều ảnh; chưa xác nhận gắn ảnh.')
        await asyncio.sleep(.2)
