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
    """One project upload path; never reopen the composer's Add menu."""
    report.update(upload_implementation='project_upload_v46_18',phase='inspect_file_input',steps=[])
    tasks=[];delivered=asyncio.Event();chooser_seen=asyncio.Event()
    def phase(name):
        report['phase']=name;report['steps'].append(name)
    async def choose(chooser):
        try:
            phase('deliver_filechooser')
            await chooser.set_files(str(Path(reference).resolve()),timeout=10000)
            report['delivery_method']='filechooser';delivered.set()
        except Exception as exc:
            report['chooser_error']={'type':type(exc).__name__,'detail':str(exc)[:1500]}
    def on_chooser(chooser):
        chooser_seen.set();tasks.append(asyncio.create_task(choose(chooser)))
    async def fill_input():
        inputs=page.locator('input[type=file]');explicit=[];generic=[]
        for i in range(await inputs.count()):
            item=inputs.nth(i);accept=(await item.get_attribute('accept')or'').lower()
            if 'image' in accept or any(x in accept for x in ('.png','.jpg','.jpeg','.webp')):explicit.append(item)
            elif not accept:generic.append(item)
        candidates=explicit or generic
        report['file_inputs']={'total':await inputs.count(),'image':len(explicit),'generic':len(generic)}
        if len(candidates)!=1:return False
        phase('deliver_file_input')
        await candidates[0].set_input_files(str(Path(reference).resolve()),timeout=10000)
        report['delivery_method']='file_input';delivered.set();return True
    async def snapshot():
        try:
            report['visible_upload_controls']=await page.locator('button,[role=menuitem],[role=button],input[type=file]').evaluate_all("""xs=>xs.filter(e=>e.type==='file'||e.getBoundingClientRect().width).slice(0,100).map(e=>({tag:e.tagName,role:e.getAttribute('role'),label:(e.getAttribute('aria-label')||e.innerText||'').slice(0,150),accept:e.getAttribute('accept'),disabled:!!e.disabled}))""")
        except Exception:pass
    page.on('filechooser',on_chooser)
    try:
        if await fill_input():return True
        phase('open_project_add')
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
        named=[x for x in controls if 'Add media menu' in x['labels'] and x['enabled']]
        toolbar=named or [x for x in candidates if x['toolbar']and x['enabled']]
        if len(toolbar)==0:
            toolbar=[x for x in controls if x['screenshotSlot']and x['enabled']]
            if len(toolbar)==1:report['selection_method']='unlabelled_button_in_supplied_screenshot_slot'
        if len(toolbar)!=1:
            log('Chưa xác định duy nhất nút thêm ảnh; đã ghi danh sách nút thanh công cụ vào báo cáo.')
            raise RuntimeError('Không xác định duy nhất nút Add media menu trên thanh trên.')
        report['selected_control']=toolbar[0]
        await page.locator('button,[role=button]').nth(toolbar[0]['index']).click(timeout=5000)
        log('Đã bấm Add media menu trên thanh trên.')
        phase('find_upload_menu_item')
        upload_name=re.compile(r'^\s*(?:(?:file_upload|upload_file|upload)\s+)?(?:upload|upload image|upload media|upload file|from computer|from device|tải lên|tải ảnh lên|tải tệp lên)\s*$',re.I)
        deadline=asyncio.get_running_loop().time()+8
        choice=None
        while asyncio.get_running_loop().time()<deadline:
            if chooser_seen.is_set():break
            if await fill_input():return True
            choices=page.get_by_role('menuitem',name=upload_name).or_(page.get_by_role('button',name=upload_name)).filter(visible=True)
            count=await choices.count()
            if count==0:
                choices=page.get_by_text(upload_name,exact=True).filter(visible=True);count=await choices.count()
            report['upload_menu_matches']=count
            if count==1:choice=choices;break
            await asyncio.sleep(.1)
        if choice is not None:
            phase('click_upload_menu_item')
            await choice.click(timeout=5000)
            log('Đã bấm Upload; đang giao tệp ảnh.')
        elif not chooser_seen.is_set():
            raise RuntimeError('Không tìm thấy duy nhất mục Upload sau khi mở Add media menu.')
        phase('wait_file_receiver')
        deadline=asyncio.get_running_loop().time()+10
        while asyncio.get_running_loop().time()<deadline:
            if chooser_seen.is_set():
                await asyncio.gather(*tasks)
                if delivered.is_set():return True
                raise RuntimeError('Hộp chọn tệp đã mở nhưng chưa nhận được ảnh.')
            if await fill_input():return True
            await asyncio.sleep(.1)
        raise RuntimeError('Đã bấm Upload nhưng chưa xuất hiện ô tải hoặc hộp chọn tệp.')
    except Exception as exc:
        # A click can time out after opening a chooser. Finish delivery before
        # deciding failure, so caller cannot delete a file still being handed off.
        if tasks:await asyncio.gather(*tasks,return_exceptions=True)
        if delivered.is_set():return True
        report['failed_phase']=report['phase']
        report['upload_error']={'type':type(exc).__name__,'detail':str(exc)[:1500]}
        log('Dừng ở bước '+report['phase']+': '+str(exc)[:400])
        await snapshot()
        return False
    finally:
        page.remove_listener('filechooser',on_chooser)
        if tasks:await asyncio.gather(*tasks,return_exceptions=True)
        if delivered.is_set():phase('file_delivered')
