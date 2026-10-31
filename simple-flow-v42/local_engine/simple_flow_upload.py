"""Adapted from user-supplied SimpleFlow db5aa529 upload path; no browser launch."""
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

