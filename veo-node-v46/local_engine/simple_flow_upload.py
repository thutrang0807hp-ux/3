"""Adapted from user-supplied SimpleFlow db5aa529 upload path; no browser launch."""
from pathlib import Path
import asyncio,re

async def upload_reference(page, reference, log):
    """Handle existing inputs, lazy upload menus and native file choosers."""
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    reference = Path(reference).resolve()
    chooser_tasks = set()
    opened_upload = False
    original_inputs = set(await page.locator('input[type="file"]').evaluate_all("xs=>xs.map((e,i)=>{e.dataset.sfUploadId=String(i);return e.dataset.sfUploadId})"))
    log('Đang tìm ô tải ảnh trong Ingredients.')
    delivered = asyncio.Event()
    async def fill_chooser(chooser):
        try:
            await chooser.set_files(str(reference))
            delivered.set()
            log('Hộp chọn tệp đã nhận ảnh; đang chờ gắn vào Ingredients.')
        except Exception as error:
            log('Hộp chọn tệp chưa nhận ảnh: ' + str(error))
    def on_chooser(chooser):
        task = asyncio.create_task(fill_chooser(chooser))
        chooser_tasks.add(task)
        task.add_done_callback(chooser_tasks.discard)
    async def fill_input():
        if chooser_tasks:
            return False
        from .simple_flow_dom import composer
        _, scope = await composer(page)
        dialogs = page.get_by_role('dialog').filter(visible=True)
        if await dialogs.count() > 1:
            return False
        target = dialogs if await dialogs.count() == 1 else scope
        inputs = (target or page).locator('input[type="file"]')
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
        # Match the working rtrtr4 flow_engine.py path: Flow may already have
        # its hidden upload input outside the composer before + is clicked.
        if not selected:
            images = []
            for item in await page.locator('input[type="file"]').all():
                accept = (await item.get_attribute('accept') or '').lower()
                if ('image' in accept or any(ext in accept for ext in ('.png','.jpg','.jpeg','.webp'))) and await item.is_enabled():
                    images.append(item)
            selected = images
        # Flow can mount its hidden input in a portal outside the composer.
        # Only inputs created by our own upload action are eligible here.
        if len(selected)!=1 and opened_upload:
            portal = []
            for item in await page.locator('input[type="file"]').all():
                token = await item.get_attribute('data-sf-upload-id')
                accept = (await item.get_attribute('accept') or '').lower()
                if token not in original_inputs and ('image' in accept or any(ext in accept for ext in ('.png','.jpg','.jpeg','.webp'))) and await item.is_enabled():
                    portal.append(item)
            selected = portal
        if len(selected) != 1:
            return False
        try:
            await selected[0].set_input_files(str(reference), timeout=5000)
            delivered.set()
            log('Ô tải tệp đã nhận ảnh; đang chờ gắn vào Ingredients.')
            return True
        except Exception as error:
            log('Ô tải ảnh chưa nhận tệp: ' + str(error))
            return False
    page.on('filechooser', on_chooser)
    try:
        if await fill_input():
            return True
        from .simple_flow_dom import composer
        _, scope = await composer(page)
        if scope is None:
            # Upload can be available before the full Generate composer.
            # Keep rtrtr4's narrow + lookup independent of submit controls.
            editors = page.locator('textarea,[contenteditable="true"],[role="textbox"]').filter(visible=True)
            scope = page
            if await editors.count()==1:
                nearby = editors.locator('xpath=ancestor::*[.//button][1]')
                if await nearby.count()==1:
                    scope = nearby
        add_name = re.compile(r'^(\+|add|add image|add media|add reference|attach|attach file|upload|upload image|upload media|thêm|thêm ảnh|tải ảnh lên|tải lên)$', re.I)
        buttons = scope.get_by_role('button', name=add_name).filter(visible=True)
        if await buttons.count() != 1:
            buttons = scope.locator('button').filter(has_text=re.compile(r'^\s*(add|add_photo_alternate|add_2|add_circle|add_circle_outline|attach_file|upload|\+)\s*$', re.I)).filter(visible=True)
        if await buttons.count() == 1:
            opened_upload = True
            await buttons.click(timeout=5000)
            log('Đã mở nút thêm tệp trong vùng nhập prompt.')
        # A chooser or input may be created after opening the menu.
        for _ in range(12):
            if delivered.is_set() or await fill_input():
                return True
            upload_name = re.compile(r'^(upload|upload image|upload media|upload file|from computer|from device|choose file|tải lên|tải ảnh lên|tải tệp lên|từ máy tính)(\s.*)?$', re.I)
            choices = page.get_by_role('menuitem', name=upload_name).or_(page.get_by_role('button', name=upload_name)).filter(visible=True)
            if await choices.count() == 1:
                opened_upload = True
                await choices.click(timeout=3000)
                break
            await asyncio.sleep(.2)
        for _ in range(15):
            if delivered.is_set() or await fill_input():
                return True
            await asyncio.sleep(.2)
        log('Chưa tìm được ô tải ảnh hoặc hộp chọn tệp sau khi mở nút thêm ảnh.')
        return False
    except PlaywrightTimeoutError:
        log('Nút tải ảnh chưa sẵn sàng; chưa xác nhận gắn ảnh.')
        return False
    finally:
        page.remove_listener('filechooser', on_chooser)
        if chooser_tasks:
            await asyncio.gather(*list(chooser_tasks), return_exceptions=True)

