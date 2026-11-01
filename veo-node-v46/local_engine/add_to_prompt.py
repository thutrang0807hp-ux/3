"""Optional confirmation in a single-image resource dialog; never click globally."""
import asyncio
import re
from .flow_prepare import reference_scope

async def click_add_to_prompt(page,log,check,report):
    dialogs=page.get_by_role('dialog').filter(visible=True)
    report['resource_dialog_count']=await dialogs.count()
    if await dialogs.count()!=1:return False
    dialog=dialogs.first
    photos=dialog.locator('img').filter(visible=True)
    # Multiple library items are ambiguous. Do not choose an arbitrary image.
    count=await photos.count()
    report['resource_dialog_image_count']=count
    if count!=1:return False
    name=re.compile(r'^\s*(Thêm vào câu lệnh|Thêm vào lời nhắc|Thêm vào prompt|Add to prompt)\s*$',re.I)
    action=dialog.get_by_role('button',name=name).or_(dialog.get_by_role('menuitem',name=name)).filter(visible=True)
    if await action.count()!=1 or not await action.is_enabled():return False
    await check()
    await action.click(timeout=3000)
    log('Đã bấm Thêm vào câu lệnh trong hộp tài nguyên một ảnh.')
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
