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
    from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
    for row in rows:
        src=urlsplit(row['src'])
        transient={'token','signature','expires','width','height','w','h','sz','t','timestamp'}
        query=[(key,value)for key,value in parse_qsl(src.query,keep_blank_values=True)if key.lower()not in transient and not key.lower().startswith(('x-goog-','x-amz-'))]
        canonical=urlunsplit((src.scheme,src.netloc,src.path,urlencode(sorted(query)),''))if src.scheme in ('http','https')else row['src']
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

async def prompt_composer(page):
    editors=page.locator('textarea,[contenteditable="true"],[contenteditable="plaintext-only"],[role=textbox]').filter(visible=True)
    if await editors.count()!=1:return None,None
    editor=editors.first
    form=editor.locator('xpath=ancestor::form[1]')
    if await form.count()==1:return editor,form
    for depth in range(1,9):
        scope=editor.locator('xpath=ancestor::*['+str(depth)+']')
        if await scope.count()!=1 or await scope.evaluate('(e)=>["BODY","HTML"].includes(e.tagName)'):break
        modes=scope.get_by_role('button',name=re.compile(r'^(Video|Ingredients|Frames|Start|End)(?:\b|\s)',re.I)).filter(visible=True)
        if await modes.count():return editor,scope
    return editor,None

async def prepare_uploaded_prompt(page,asset,reference,prompt,check,report,timeout=10):
    """Bind the exact uploaded library asset to Ingredients, fill text, never Generate."""
    import time,io
    from PIL import Image,ImageOps,ImageChops,ImageStat
    ingredients=re.compile(r'^(Ingredients|Ingredients to Video|Thành phần|Thành phần thành video|Từ thành phần)$',re.I)
    async def fail(message):
        report['preparation_error']=message;return False
    async def ready_mode(scope):
        if scope is None:return False
        controls=scope.get_by_role('button',name=ingredients).or_(scope.get_by_role('tab',name=ingredients)).filter(visible=True)
        selected=await controls.evaluate_all("""xs=>xs.some(e=>{
          if(e.closest('[role=menu],[role=listbox]'))return false;
          if(['aria-selected','aria-pressed','aria-checked'].some(a=>e.getAttribute(a)==='false'))return false;
          if(e.getAttribute('role')==='tab')return e.getAttribute('aria-selected')==='true'||['active','checked'].includes(e.getAttribute('data-state'));
          return true;
        })""")
        if selected:return True
        labels=scope.get_by_text(ingredients).filter(visible=True)
        return await labels.evaluate_all("xs=>xs.length===1&&!xs[0].closest('[aria-selected=false],[aria-pressed=false],[aria-checked=false],[role=menu],[role=listbox]')")
    report['preparation_stage']='close_upload_overlay'
    await check()
    await page.keyboard.press('Escape')
    report['preparation_stage']='find_composer'
    editor,scope=await prompt_composer(page)
    if scope is None:return await fail('Chưa xác định duy nhất vùng nhập prompt. Ảnh đã tải vẫn được giữ.')
    if not await ready_mode(scope):
        # Only explicit mode controls and Ingredients choices are eligible.
        triggers=scope.get_by_role('button',name=re.compile(r'^(Video|Videos|Text to Video|Frames to Video|Frames)(?:\s|[·•]|$)',re.I)).filter(visible=True)
        report['composer_controls']=await scope.locator('button,[role=tab],[role=combobox]').filter(visible=True).evaluate_all("xs=>xs.map(e=>({role:e.getAttribute('role'),name:e.getAttribute('aria-label'),text:(e.innerText||'').slice(0,160),selected:e.getAttribute('aria-selected'),pressed:e.getAttribute('aria-pressed')}))")
        if await triggers.count()!=1:return await fail('Chưa nhận diện duy nhất nút chọn chế độ Ingredients; chưa gắn ảnh hoặc điền prompt.')
        report['preparation_stage']='open_mode_menu'
        report['mode_trigger']=await triggers.evaluate("e=>({name:e.getAttribute('aria-label'),text:(e.innerText||'').slice(0,160)})",timeout=2000)
        # Re-query the live locator; React may replace controls after uploading.
        await triggers.click(timeout=5000)
        report['preparation_stage']='find_ingredients_option'
        options=page.get_by_role('option',name=ingredients).or_(page.get_by_role('menuitem',name=ingredients)).or_(page.get_by_role('tab',name=ingredients)).or_(page.get_by_role('button',name=ingredients)).filter(visible=True)
        try:await options.first.wait_for(state='visible',timeout=2500)
        except Exception:
            report['mode_menu']=await page.locator('[role=menu] button,[role=menuitem],[role=option],[role=tab]').filter(visible=True).all_text_contents()
            return await fail('Menu chưa có lựa chọn Ingredients rõ ràng; chưa dùng Frames thay thế.')
        report['mode_options']=await options.all_text_contents()
        if await options.count()!=1:return await fail('Có nhiều lựa chọn Ingredients; chưa tự chọn bừa.')
        report['preparation_stage']='choose_ingredients'
        await options.click(timeout=3000)
        report['preparation_stage']='verify_ingredients'
        mode_deadline=time.monotonic()+3
        while time.monotonic()<mode_deadline:
            editor,scope=await prompt_composer(page)
            if await ready_mode(scope):break
            await asyncio.sleep(.1)
        else:return await fail('Chưa xác nhận giao diện đã chuyển sang Ingredients.')
    report['preparation_stage']='ingredients'
    # Do not silently delete old references or overwrite an existing prompt.
    existing=scope.locator('img').filter(visible=True)
    if await existing.count():return await fail('Ô tạo đang có ảnh tham khảo khác. Chưa thay ảnh hoặc ghi đè prompt.')
    old_text=await editor.evaluate('(e)=>e.value??e.innerText??""')
    if old_text.strip()and old_text.strip()!=prompt.strip():return await fail('Ô Flow đã có prompt khác; chưa tự ghi đè.')
    report['preparation_stage']='find_uploaded_asset'
    rows=[row for row in await library_images(page)if row['key']==asset['key']and row['loaded']and not row['busy']]
    if len(rows)!=1:return await fail('Ảnh vừa upload không còn nhận diện duy nhất trong dự án; chưa chọn ảnh cũ.')
    image=page.locator('img[data-sf-upload-image="'+rows[0]['token']+'"]')
    report['preparation_stage']='open_asset_menu'
    await check();await image.click(button='right',timeout=3000)
    actions=page.get_by_role('menuitem',name=re.compile(r'^(Add to prompt|Use in prompt|Use as ingredient|Add as ingredient|Add to ingredients|Thêm vào prompt|Dùng làm thành phần|Thêm vào thành phần)$',re.I)).filter(visible=True)
    try:await actions.first.wait_for(state='visible',timeout=2500)
    except Exception:
        report['image_menu']=await page.get_by_role('menuitem').filter(visible=True).all_text_contents()
        return await fail('Đã chọn đúng ảnh mới nhưng chưa nhận diện nút đưa ảnh vào Ingredients; chưa điền prompt.')
    if await actions.count()!=1:return await fail('Không xác định duy nhất thao tác gắn ảnh vào Ingredients.')
    report['preparation_stage']='attach_asset'
    await actions.click(timeout=3000)
    report['preparation_stage']='attaching'
    with Image.open(reference)as original:expected=ImageOps.fit(ImageOps.exif_transpose(original).convert('RGB'),(64,64))
    deadline=time.monotonic()+timeout;attached=False
    while time.monotonic()<deadline:
        await check();editor,scope=await prompt_composer(page)
        if scope is None or not await ready_mode(scope):break
        images=scope.locator('img').filter(visible=True)
        if await images.count()==1 and not await scope.locator('[aria-busy=true],[role=progressbar]').filter(visible=True).count():
            item=images.first
            if await item.evaluate('(e)=>e.complete&&e.naturalWidth>32&&e.naturalHeight>32'):
                with Image.open(io.BytesIO(await item.screenshot(timeout=2000)))as thumb:actual=ImageOps.fit(thumb.convert('RGB'),(64,64))
                error=sum(ImageStat.Stat(ImageChops.difference(expected,actual)).mean)/(3*255)
                if error<=.035:attached=True;break
        await asyncio.sleep(.2)
    if not attached:return await fail('Chưa xác nhận đúng ảnh mới đã gắn vào Ingredients. Chưa điền prompt.')
    # Recheck identity and the selected mode directly before modifying text.
    await check()
    if not await ready_mode(scope):return await fail('Chế độ tạo đã thay đổi; chưa điền prompt.')
    current=await editor.evaluate('(e)=>e.value??e.innerText??""')
    if current.strip()and current.strip()!=prompt.strip():return await fail('Prompt trên Flow đã đổi; chưa ghi đè.')
    report['preparation_stage']='fill_prompt'
    await editor.fill(prompt,timeout=5000)
    report['preparation_stage']='verify_prompt'
    actual=await editor.evaluate('(e)=>e.value??e.innerText??""')
    if actual.strip()!=prompt.strip():return await fail('Chưa xác nhận nội dung prompt sau khi điền.')
    report['attached_asset_key']=asset['key'];report['prompt_sha256']=__import__('hashlib').sha256(prompt.encode()).hexdigest()
    report['preparation_stage']='prompt_ready'
    return True
