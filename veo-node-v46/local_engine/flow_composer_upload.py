"""Direct composer upload trial. No library search or Generate."""
import asyncio
import hashlib
import re
from pathlib import Path
from .flow_prepare import reference_scope, editor_text
from .add_to_prompt import click_add_to_prompt, wait_for_composer_attachment

async def upload_into_composer_and_fill(page,image_path,prompt,check,*,report=None):
    report={} if report is None else report
    report.update(state='running',delivered=False,image_attached=False,prompt_filled=False,
                  prompt_verified=False,generation_submitted=False,upload_uncertain=False,
                  upload_implementation='composer_filechooser_v46_31',add_to_prompt_clicked=False)
    report.setdefault('logs',[]);report.setdefault('errors',{})
    reference=Path(image_path)
    if not reference.is_file() or not 0<reference.stat().st_size<=6*1024**2:
        raise ValueError('Ảnh không tồn tại hoặc vượt 6 MB.')
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>20000:
        raise ValueError('Prompt trống hoặc quá dài.')
    report.update(reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),prompt_expected=prompt)
    def log(text):report['logs'].append(text)
    def error(step,exc):
        report['errors'][step]={'type':type(exc).__name__,'message':str(exc)}
        log(step+': '+type(exc).__name__)
    async def scope():
        await check()
        editor,area=await reference_scope(page)
        if editor is None or area is None:raise RuntimeError('Chưa xác định được composer.')
        return editor,area
    async def chips():
        _,area=await scope()
        return await area.locator('img').evaluate_all('''xs=>xs.filter(e=>{const r=e.getBoundingClientRect();return r.width>=20&&r.height>=20}).map(e=>e.currentSrc||e.src)''')
    async def attach():
        report['attachment_stage']='check_empty_composer'
        if await chips():raise RuntimeError('Composer đang có ảnh; chưa thay hoặc thêm ảnh khác.')
        _,area=await scope()
        add=area.get_by_role('button',name=re.compile(r'^\s*(Add ingredients to the prompt box|Add ingredients|Thêm thành phần vào ô lời nhắc|Thêm thành phần)\s*$',re.I)).filter(visible=True)
        if await add.count()!=1:raise RuntimeError('Chưa tìm duy nhất nút + thành phần trong composer.')
        report['attachment_stage']='open_composer_media'
        await check();await add.click(timeout=4000)
        log('Đã mở dấu + trong composer, không dùng thanh trên.')
        name=re.compile(r'^\s*(Upload media|Tải nội dung nghe nhìn lên|Tải phương tiện lên)\s*$',re.I)
        upload=page.get_by_role('button',name=name).or_(page.get_by_role('menuitem',name=name)).filter(visible=True)
        report['attachment_stage']='find_upload_media'
        await upload.first.wait_for(state='visible',timeout=5000)
        if await upload.count()!=1:raise RuntimeError('Chưa có duy nhất Upload media.')
        report['attachment_stage']='deliver_composer_file'
        future=asyncio.get_running_loop().create_future()
        def on_chooser(chooser):
            if not future.done():future.set_result(chooser)
        page.on('filechooser',on_chooser)
        try:
            await check();await upload.click(timeout=4000)
            chooser=await asyncio.wait_for(asyncio.shield(future),5)
            await check()
            report['file_delivery_attempted']=True
            await chooser.set_files(str(reference.resolve()),timeout=10000)
            report['delivered']=True
            log('Đã giao tệp qua Upload media của composer.')
        finally:
            page.remove_listener('filechooser',on_chooser)
            if not future.done():future.cancel()
        report['attachment_stage']='find_add_to_prompt_or_chip'
        deadline=asyncio.get_running_loop().time()+10
        while asyncio.get_running_loop().time()<deadline:
            current=await chips()
            if len(current)==1:
                report.update(image_attached=True,attachment_evidence='empty_composer_then_single_chip_after_direct_upload')
                log('Đã thấy một chip ảnh sau upload trực tiếp.')
                return
            if len(current)>1:raise RuntimeError('Composer xuất hiện nhiều ảnh; chưa xác nhận gắn ảnh.')
            clicked=await click_add_to_prompt(page,log,check,report)
            if clicked:
                report['add_to_prompt_clicked']=True
                report['attachment_stage']='wait_chip_after_add_to_prompt'
                try:
                    report['image_attached']=await asyncio.wait_for(wait_for_composer_attachment(page,check),timeout=10)
                except asyncio.TimeoutError:
                    report['image_attached']=False
                    log('Đã bấm Thêm vào câu lệnh nhưng chưa thấy chip trong composer.')
                if report['image_attached']:
                    report['attachment_evidence']='single_chip_after_direct_upload_and_add_to_prompt'
                return
            await asyncio.sleep(.2)
        log('Chưa thấy chip hoặc nút Thêm vào câu lệnh đủ rõ; vẫn điền prompt.')
    async def fill():
        editor,_=await scope()
        current=await editor_text(editor)
        normalize=lambda value:re.sub(r'\s+',' ',str(value)).strip()
        inline=await editor.locator('img,[data-media-id],[data-asset-id]').count()
        if inline:
            if normalize(current)==normalize(prompt):pass
            elif not normalize(current):
                await editor.focus();await editor.press('Control+End');await page.keyboard.insert_text(prompt)
            else:raise RuntimeError('Editor có ảnh inline và prompt khác; chưa thay nội dung làm mất ảnh.')
        else:await editor.fill(prompt,timeout=8000)
        report['prompt_filled']=True
        log('Đã điền prompt.')
        for _ in range(5):
            try:actual=await editor_text(editor)
            except Exception as exc:error('prompt_readback',exc);return
            report['prompt_actual']=actual
            if normalize(actual)==normalize(prompt):
                report['prompt_verified']=True;break
            await asyncio.sleep(.15)
        log('Đọc lại prompt khớp.' if report['prompt_verified'] else 'Đọc lại chưa khớp; xem prompt_actual.')
    try:
        await check()
        from .flow_native_reference import UploadMediaCapture
        capture=None
        try:
            capture=UploadMediaCapture(page,reference,report)
            capture.start()
        except ValueError:
            report['uploaded_media_capture_error']='unsupported_project_origin'
        try:await asyncio.wait_for(attach(),45)
        except Exception as exc:
            report['upload_uncertain']=bool(report.get('file_delivery_attempted') and not report['delivered'])
            error('attachment',exc)
        finally:
            if capture:await capture.close()
        await check()
        # Escape dismisses the media popover before filling; no resubmission.
        try:await asyncio.wait_for(page.keyboard.press('Escape'),timeout=2)
        except Exception as exc:error('close_media_menu',exc)
        await check()
        try:await asyncio.wait_for(fill(),12)
        except Exception as exc:error('prompt',exc)
        await check()
        complete=report['delivered'] and report['prompt_filled']
        report.update(state='inputs_sent' if complete else 'partial',phase='complete',message=(
            'Đã giao tệp và điền prompt. ' if complete else 'Chưa xác nhận đủ giao tệp và điền prompt. ')+(
            'Đã ghi nhận chip ảnh trong composer.' if report['image_attached'] else 'Chưa xác nhận chip ảnh trong composer.')+' Chưa tạo video.')
    except asyncio.CancelledError:
        report.update(state='cancelled',message='Đã dừng lượt thử; chưa tạo video.');raise
    except Exception as exc:
        error('workflow',exc);report.update(state='failed',message='Đã dừng lượt thử; chưa tạo video.')
    finally:
        report['generation_submitted']=False
        log(f"Kết quả: delivered={report['delivered']}, prompt_filled={report['prompt_filled']}, prompt_verified={report['prompt_verified']}, image_attached={report['image_attached']}")
    return report
