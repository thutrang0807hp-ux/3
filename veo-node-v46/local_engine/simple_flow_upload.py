"""Unmodified upload_reference from rtrtr4 db5aa529c5203bee37cd05d4925b622419616b02."""
from pathlib import Path
import asyncio,re

async def upload_reference(page, reference, log):
    """Handle existing inputs, lazy upload menus and native file choosers."""
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    reference = Path(reference).resolve()
    chooser_tasks = set()
    delivered = asyncio.Event()
    async def fill_chooser(chooser):
        try:
            await chooser.set_files(str(reference))
            delivered.set()
        except Exception as error:
            log('Hộp chọn tệp chưa nhận ảnh: ' + str(error))
    def on_chooser(chooser):
        task = asyncio.create_task(fill_chooser(chooser))
        chooser_tasks.add(task)
        task.add_done_callback(chooser_tasks.discard)
    async def fill_input():
        inputs = page.locator('input[type="file"]')
        candidates = []
        explicit_images = []
        for index in range(await inputs.count()):
            item = inputs.nth(index)
            accept = (await item.get_attribute('accept') or '').lower()
            if not accept or 'image' in accept or any(ext in accept for ext in ('.png', '.jpg', '.jpeg', '.webp')):
                candidates.append(item)
                if accept:
                    explicit_images.append(item)
        selected = explicit_images if explicit_images else candidates
        if len(selected) != 1:
            return False
        try:
            await selected[0].set_input_files(str(reference), timeout=5000)
            delivered.set()
            return True
        except Exception as error:
            log('Ô tải ảnh chưa nhận tệp: ' + str(error))
            return False
    page.on('filechooser', on_chooser)
    try:
        if await fill_input():
            return True
        editors = page.locator('textarea, [contenteditable="true"], [role="textbox"]').filter(visible=True)
        scope = page
        if await editors.count() == 1:
            composer = editors.locator('xpath=ancestor::*[.//button][1]')
            if await composer.count() == 1:
                scope = composer
        add_name = re.compile(r'^(\+|add|add image|add media|add reference|attach|attach file|upload|upload image|upload media|thêm|thêm ảnh|tải ảnh lên|tải lên)$', re.I)
        buttons = scope.get_by_role('button', name=add_name).filter(visible=True)
        if await buttons.count() != 1:
            buttons = scope.locator('button').filter(has_text=re.compile(r'^\s*(add|add_photo_alternate|attach_file|upload|\+)\s*$', re.I)).filter(visible=True)
        if await buttons.count() == 1:
            await buttons.click(timeout=5000)
            log('Đã mở nút thêm tệp trong vùng nhập prompt.')
        # A chooser or input may be created after opening the menu.
        for _ in range(12):
            if delivered.is_set() or await fill_input():
                return True
            upload_name = re.compile(r'^(upload|upload image|upload media|upload file|from computer|from device|choose file|tải lên|tải ảnh lên|tải tệp lên|từ máy tính)(\s.*)?$', re.I)
            choices = page.get_by_role('menuitem', name=upload_name).or_(page.get_by_role('button', name=upload_name)).filter(visible=True)
            if await choices.count() == 1:
                await choices.click(timeout=3000)
                break
            await asyncio.sleep(.2)
        for _ in range(15):
            if delivered.is_set() or await fill_input():
                return True
            await asyncio.sleep(.2)
        return False
    except PlaywrightTimeoutError:
        log('Nút tải ảnh chưa sẵn sàng. Có thể mở nút + thủ công rồi thử lại.')
        return False
    finally:
        page.remove_listener('filechooser', on_chooser)
        if chooser_tasks:
            await asyncio.gather(*list(chooser_tasks), return_exceptions=True)


async def upload_to_project(page,reference,log,report):
    """Open the project toolbar's Add menu before calling the unchanged uploader."""
    images=page.locator('input[type=file][accept*="image"]')
    if await images.count()==1:
        return await upload_reference(page,reference,log)
    controls=await page.locator('button,[role=button]').evaluate_all(r"""xs=>xs.map((e,i)=>{
      const r=e.getBoundingClientRect();if(!r.width||!r.height)return null;
      const labels=[e.getAttribute('aria-label'),e.getAttribute('title'),e.innerText].filter(Boolean).map(x=>x.trim());
      const icons=[...e.querySelectorAll('i,[class*=symbol],[class*=material]')].map(x=>x.textContent.trim());
      const add=[...labels,...icons].some(x=>/^(?:\+|add|add_2|add_circle|add_photo_alternate|add to project|add media|add image|upload|upload media|thêm|thêm vào dự án)$/i.test(x));
      const toolbar=r.top>=0&&r.top<Math.min(100,innerHeight*.2)&&r.left>innerWidth*.5&&r.left<innerWidth*.9;
      const symbolic=labels.every(x=>/^[\s\uE000-\uF8FF+]*$/.test(x));
      const screenshotSlot=innerWidth>=1000&&toolbar&&(r.left+r.width/2)/innerWidth>.72&&(r.left+r.width/2)/innerWidth<.78&&r.width<=64&&r.height<=64&&symbolic;
      return {index:i,labels:labels.map(x=>x.slice(0,100)),icons:icons.map(x=>x.slice(0,50)),top:r.top,left:r.left,width:r.width,height:r.height,toolbar,add,screenshotSlot,enabled:!e.disabled};
    }).filter(Boolean)""")
    report['toolbar_controls']=[x for x in controls if x['toolbar']]
    candidates=[x for x in controls if x['add']]
    report['add_controls']=candidates
    toolbar=[x for x in candidates if x['toolbar']and x['enabled']]
    if len(toolbar)==0:
        toolbar=[x for x in controls if x['screenshotSlot']and x['enabled']]
        if len(toolbar)==1:report['selection_method']='unlabelled_button_in_supplied_screenshot_slot'
    if len(toolbar)!=1:
        log('Chưa xác định duy nhất nút thêm ảnh; đã ghi danh sách nút thanh công cụ vào báo cáo.')
        return await upload_reference(page,reference,log)
    report['selected_control']=toolbar[0]
    delivered=asyncio.Event();tasks=set()
    async def choose(chooser):
        await chooser.set_files(str(Path(reference).resolve()));delivered.set()
    def on_chooser(chooser):
        task=asyncio.create_task(choose(chooser));tasks.add(task)
    page.on('filechooser',on_chooser)
    try:
        await page.locator('button,[role=button]').nth(toolbar[0]['index']).click(timeout=5000)
        log('Đã mở nút + ở thanh trên của dự án, không phải cạnh prompt.')
        await asyncio.sleep(.2)
        try:
            await page.screenshot(path=str(Path(reference).with_suffix('.menu.png')),timeout=5000)
        except Exception:pass
        if tasks:
            await asyncio.gather(*tasks)
        if delivered.is_set():return True
    finally:
        page.remove_listener('filechooser',on_chooser)
    # Menu Upload/image input is now open; source function remains untouched.
    return await upload_reference(page,reference,log)

async def library_images(page):
    """Read image identities from the project library, excluding upload dialogs/composers."""
    import hashlib
    rows=await page.locator('img').evaluate_all(r'''xs=>xs.map((e,i)=>{
      const r=e.getBoundingClientRect();if(!r.width||!r.height||e.closest('form,[role=dialog]'))return null;
      const editor=e.closest('[data-testid*=composer]');if(editor)return null;
      const card=e.closest('[data-media-id],[data-asset-id],article,[role=listitem]')||e.parentElement;
      const id=card?.getAttribute('data-media-id')||card?.getAttribute('data-asset-id')||'';
      const src=e.currentSrc||e.src||'';
      const visible=x=>!!x.getClientRects().length;
      const busy=card?.getAttribute('aria-busy')==='true'||/^(uploading|loading|pending)$/.test(card?.getAttribute('data-state')||'')||[...(card?.querySelectorAll('[role=progressbar],[aria-busy=true]')||[])].some(visible);
      e.setAttribute('data-sf-upload-image',String(i));
      return {token:String(i),id,src,name:[e.alt,e.title,card?.getAttribute('title')].filter(Boolean).join(' '),loaded:e.complete&&e.naturalWidth>32&&e.naturalHeight>32,busy,width:e.naturalWidth,height:e.naturalHeight};
    }).filter(Boolean)''')
    from urllib.parse import urlsplit,urlunsplit
    for row in rows:
        src=urlsplit(row['src'])
        canonical=urlunsplit((src.scheme,src.netloc,src.path,'',''))if src.scheme in ('http','https')else row['src']
        row['key']=hashlib.sha256((row['id']or canonical).encode()).hexdigest()
    return rows

async def wait_uploaded_image(page,before,reference,check,report,timeout=60):
    """Confirm one NEW loaded library image matching the submitted picture; never pick an old tile."""
    import time,io
    from PIL import Image,ImageOps,ImageChops,ImageStat
    with Image.open(reference)as original:
        expected=ImageOps.fit(ImageOps.exif_transpose(original).convert('RGB'),(64,64))
    baseline={row['key']for row in before};deadline=time.monotonic()+timeout
    stable_key=None;stable_since=None
    while time.monotonic()<deadline:
        await check()
        rows=await library_images(page);matches=[]
        report['image_check']={'visible_images':len(rows),'new_images':len([x for x in rows if x['key']not in baseline]),'matching_images':0}
        for row in rows:
            if row['key']in baseline or not row['loaded']or row['busy']:continue
            # A local upload preview alone is not evidence of a completed library asset.
            if not row['id']and not row['src'].startswith(('https://','http://')):continue
            item=page.locator('img[data-sf-upload-image="'+row['token']+'"]')
            try:
                screenshot=await item.screenshot(timeout=1500)
                with Image.open(io.BytesIO(screenshot))as thumbnail:
                    actual=ImageOps.fit(thumbnail.convert('RGB'),(64,64))
                error=sum(ImageStat.Stat(ImageChops.difference(expected,actual)).mean)/(3*255)
            except Exception:continue
            if error<=.035:matches.append({**row,'visual_difference':round(error,5)})
        matches=list({row['key']:row for row in matches}.values())
        report['image_check']['matching_images']=len(matches)
        if len(matches)==1:
            match=matches[0]
            if stable_key!=match['key']:stable_key=match['key'];stable_since=time.monotonic()
            elif time.monotonic()-stable_since>=.75:
                return {'key':match['key'],'media_id':match['id']or None,'name':match['name'][:160],'width':match['width'],'height':match['height'],'visual_difference':match['visual_difference']}
        else:stable_key=None;stable_since=None
        await asyncio.sleep(.25)
    return None
