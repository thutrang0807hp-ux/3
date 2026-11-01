"""Bind a previously uploaded reference to its scene prompt; never submit here."""
import asyncio
import base64
import copy
import hashlib
import io
import json
import secrets
from pathlib import Path
import re

from fastapi import HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageChops, ImageOps, ImageStat

from .flow_settings import DEFAULTS, apply_settings, settings_panel, read_settings, control, exact, validate_settings
from .simple_flow_dom import composer


class PrepareStopped(RuntimeError):
    pass


def prompt_text(value):
    return str(value).replace('\r\n', '\n').strip()


async def editor_text(editor):
    return await editor.evaluate("e=>e.matches('input,textarea')?e.value:e.innerText")


def image_error(raw, expected, crop=False):
    with Image.open(io.BytesIO(raw)) as image:
        image = ImageOps.exif_transpose(image).convert('RGB')
        source = ImageOps.fit(expected, image.size) if crop else expected
        left = source.resize((48,48), Image.Resampling.LANCZOS)
        right = image.resize((48,48), Image.Resampling.LANCZOS)
        return sum(ImageStat.Stat(ImageChops.difference(left,right)).mean)/3


async def reference_images(scope, expected, report=None):
    images = scope.locator('img').filter(visible=True)
    if await images.count() > 80:
        raise PrepareStopped('Có quá nhiều ảnh để đối chiếu an toàn. Thu gọn thư viện Flow rồi thử lại.')
    matches=[];candidates=[]
    for index in range(await images.count()):
        item=images.nth(index)
        details=await item.evaluate('''e=>({ready:e.complete&&e.naturalWidth>32&&e.naturalHeight>32,
            composer:!!e.closest('[data-sf-flow-composer]'),src:e.currentSrc||e.src,
            media:e.closest('[data-media-id],[data-asset-id]')?.getAttribute('data-media-id')||e.closest('[data-asset-id]')?.getAttribute('data-asset-id')||null})''')
        if not details['ready']:continue
        try:
            encoded=await item.evaluate('''e=>{try{const c=document.createElement('canvas'),scale=Math.min(1,256/Math.max(e.naturalWidth,e.naturalHeight));c.width=Math.max(1,Math.round(e.naturalWidth*scale));c.height=Math.max(1,Math.round(e.naturalHeight*scale));c.getContext('2d').drawImage(e,0,0,c.width,c.height);return c.toDataURL('image/png').split(',')[1]}catch{return null}}''')
            raw=base64.b64decode(encoded) if encoded else await item.screenshot(timeout=3000)
            score=image_error(raw,expected,crop=not bool(encoded))
        except Exception:
            continue
        candidates.append({'index':index,'error':round(score,3),'composer':details['composer'],
                           'media_id':details['media'],'source_hash':hashlib.sha256(details['src'].encode()).hexdigest()})
        if score <= 4:
            matches.append({'item':item,'error':round(score,3),'composer':details['composer'],
                            'media_id':details['media'],'source_hash':hashlib.sha256(details['src'].encode()).hexdigest()})
    if report is not None:
        report['image_matches']=[{k:v for k,v in m.items() if k!='item'} for m in matches]
        report['image_candidates']=sorted(candidates,key=lambda x:x['error'])[:20]
    return matches


async def attached_reference(page, expected):
    editor,scope=await composer(page)
    if editor is None or scope is None:return False
    images=scope.locator('img').filter(visible=True)
    usable=[]
    for item in await images.all():
        if await item.evaluate('e=>e.complete&&e.naturalWidth>32&&e.naturalHeight>32'):usable.append(item)
    if len(usable)!=1:return False
    if await scope.locator('[role=progressbar],[aria-busy=true],[role=alert]').filter(visible=True).count():return False
    return len(await reference_images(scope,expected))==1


async def prepare_composer(page, reference, prompt, settings, check, report):
    phase=lambda value:report.update(phase=value)
    with Image.open(reference) as image:expected=ImageOps.exif_transpose(image).convert('RGB')
    phase('apply_settings')
    config={}
    if not await apply_settings(page,settings,check,config):
        report['settings_report']=config
        raise PrepareStopped('Chưa đọc lại được cấu hình Flow. Chưa gắn ảnh, điền prompt hoặc tạo video.')
    report['settings_report']=config
    await page.keyboard.press('Escape')
    phase('locate_composer')
    await check()
    editor,scope=await composer(page)
    if editor is None or scope is None:raise PrepareStopped('Chưa nhận diện duy nhất ô tạo Flow.')
    await scope.evaluate("e=>e.setAttribute('data-sf-flow-composer','true')")
    current=prompt_text(await editor_text(editor))
    if current and current!=prompt_text(prompt):
        raise PrepareStopped('Ô Flow đang có prompt khác. Kiểm tra và dọn ô tạo trước; chưa ghi đè.')
    if not await attached_reference(page,expected):
        existing=scope.locator('img').filter(visible=True)
        for item in await existing.all():
            if await item.evaluate('e=>e.complete&&e.naturalWidth>32&&e.naturalHeight>32'):
                raise PrepareStopped('Ô tạo đang gắn ảnh khác hoặc nhiều ảnh. Chưa thay hoặc xóa ảnh.')
        phase('match_library_reference')
        deadline=asyncio.get_running_loop().time()+20
        matches=[]
        for _ in range(40):
            await check()
            remaining=deadline-asyncio.get_running_loop().time()
            if remaining<=0:break
            try:
                found=await asyncio.wait_for(reference_images(page,expected,report),timeout=remaining)
            except asyncio.TimeoutError:
                raise PrepareStopped('Đối chiếu thumbnail chưa hoàn tất sau 20 giây. Chưa chọn ảnh hoặc gửi tạo.')from None
            matches=[m for m in found if not m['composer']]
            if matches:break
            await asyncio.sleep(.5)
        if len(matches)!=1:
            raise PrepareStopped('Chưa xác định duy nhất đúng ảnh đã upload trong thư viện (khớp '+str(len(matches))+'). Không chọn ảnh gần giống hoặc ảnh đầu danh sách.')
        match=matches[0];report['matched_reference']={k:v for k,v in match.items() if k not in ('item','composer')}
        await match['item'].hover()
        phase('open_reference_menu')
        more=None
        for depth in range(1,9):
            card=match['item'].locator('xpath=ancestor::*['+str(depth)+']')
            if not await card.count() or await card.evaluate("e=>['BODY','HTML'].includes(e.tagName)"):break
            if await card.locator('img').count()!=1:break
            button=await control(card,exact(r'More options|More|Tùy chọn khác|Tuỳ chọn khác'))
            if await button.count()==1:
                more=button;break
        if more is None:raise PrepareStopped('Đã khớp ảnh nhưng chưa tìm duy nhất menu ⋮ của chính ảnh đó.')
        await check();await more.click(timeout=5000)
        phase('add_reference_to_prompt')
        action=await control(page,exact(r'Add to prompt|Thêm vào câu lệnh|Thêm vào lời nhắc|Thêm vào prompt'))
        for _ in range(30):
            action=await control(page,exact(r'Add to prompt|Thêm vào câu lệnh|Thêm vào lời nhắc|Thêm vào prompt'))
            if await action.count()==1:break
            await asyncio.sleep(.1)
        if await action.count()!=1:raise PrepareStopped('Chưa có duy nhất Add to prompt cho ảnh đã chọn. Không bấm Animate.')
        await check();await action.click(timeout=5000)
        # Some layouts show an Image submenu after Add to prompt.
        for _ in range(40):
            await check()
            if await attached_reference(page,expected):break
            option=page.get_by_role('menuitem',name=re.compile(r'^(Image|Hình ảnh)$',re.I)).or_(page.get_by_role('option',name=re.compile(r'^(Image|Hình ảnh)$',re.I))).filter(visible=True)
            if await option.count()==1:await option.click(timeout=5000)
            await asyncio.sleep(.15)
        else:raise PrepareStopped('Đã bấm Add to prompt nhưng chưa đối chiếu được đúng ảnh trong ô tạo.')
    phase('fill_scene_prompt')
    await check()
    editor,scope=await composer(page)
    await editor.fill(prompt,timeout=5000)
    if prompt_text(await editor_text(editor))!=prompt_text(prompt):raise PrepareStopped('Prompt đọc lại không khớp nguyên nội dung của cảnh.')
    if not await attached_reference(page,expected):raise PrepareStopped('Ảnh trong ô tạo đã đổi trước khi xác nhận prompt.')
    phase('ready_for_review')
    report['prompt_sha256']=hashlib.sha256(prompt.encode()).hexdigest()
    report['reference_sha256']=hashlib.sha256(Path(reference).read_bytes()).hexdigest()


async def validate_prepared(service, payload, raw):
    report=service.prepare_report
    if not report or report['state']!='ready' or payload.get('prepared_request_id')!=report['request_id']:
        raise PrepareStopped('Lượt gắn ảnh/prompt không còn sẵn sàng. Chuẩn bị lại, chưa gửi tạo.')
    if report['settings']!=DEFAULTS:
        raise PrepareStopped('Bước thử tạo một clip hiện chỉ hỗ trợ Ingredients · Veo 3.1 Lite · 9:16 · x1.')
    selection=service.account_bridge.selection()
    if not selection['available'] or selection['account_id']!=report['account_id']:
        raise PrepareStopped('Tài khoản đang chọn đã đổi sau bước chuẩn bị. Chưa gửi tạo.')
    for key in ('room_id','scene_id','part','account_id'):
        if payload.get(key)!=report.get(key):raise PrepareStopped('Ảnh/prompt thuộc phòng, cảnh hoặc tài khoản khác. Chưa gửi tạo.')
    if hashlib.sha256(raw).hexdigest()!=report['reference_sha256'] or hashlib.sha256(payload['prompt'].encode()).hexdigest()!=report['prompt_sha256']:
        raise PrepareStopped('Ảnh hoặc prompt đã đổi sau bước chuẩn bị. Chưa gửi tạo.')
    if service.page is not service.prepared_page or service.page.is_closed():raise PrepareStopped('Phiên Flow đã đổi; cần gắn lại ảnh/prompt, chưa gửi tạo.')
    await service.assert_ready()
    panel=await settings_panel(service.page)
    actual=await read_settings(panel)
    await service.page.keyboard.press('Escape')
    if actual!=report['settings']:raise PrepareStopped('Cấu hình Flow đã đổi sau bước chuẩn bị. Chưa gửi tạo.')
    with Image.open(service.prepared_reference) as image:expected=ImageOps.exif_transpose(image).convert('RGB')
    editor,_=await composer(service.page)
    if editor is None or prompt_text(await editor_text(editor))!=prompt_text(payload['prompt']) or not await attached_reference(service.page,expected):
        raise PrepareStopped('Ảnh hoặc prompt thực tế trong Flow không còn khớp. Chưa gửi tạo.')


def register_prepare_routes(app, service):
    service.prepare_report=None;service.prepared_page=None;service.prepared_reference=None
    def status(rid):
        report=service.prepare_report
        if not report or report['request_id']!=rid:raise HTTPException(404,'Không có lượt chuẩn bị này trong phiên hiện tại.')
        return copy.deepcopy(report)
    async def run(report, reference, token):
        async def check():
            selection=service.account_bridge.selection()
            if not selection['available'] or selection['account_id']!=report['account_id'] or selection['token']!=token:raise PrepareStopped('Tài khoản đã đổi; dừng trước khi gửi tạo.')
            await service.assert_ready()
        try:
            await prepare_composer(service.page,reference,report.pop('_prompt'),report['settings'],check,report)
            service.prepared_page=service.page;service.prepared_reference=reference
            report.update(state='ready',message='Đã đối chiếu đúng ảnh và prompt trong ô tạo. Xem ảnh kiểm tra trước khi tạo một lần.')
        except asyncio.CancelledError:
            report.update(state='failed',message='Đã dừng chuẩn bị; chưa gửi tạo video.');raise
        except Exception as error:
            report.update(state='failed',message=(str(error) if isinstance(error,PrepareStopped) else 'Chưa chuẩn bị được Flow: '+type(error).__name__)+ ' Chưa gửi tạo video.',error={'type':type(error).__name__,'detail':str(error)[:1500]})
        finally:
            report.pop('_prompt',None)
            try:
                if service.page and not service.page.is_closed():
                    await service.page.screenshot(path=str(service.root/(report['request_id']+'.prepare.png')),timeout=5000);report['has_preview']=True
            except Exception:pass
            (service.root/(report['request_id']+'.prepare.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            service.active=None
    @app.post('/local-api/flow/simple/prepare')
    async def start(body:dict):
        settings=validate_settings(body.get('settings'))
        if settings['mode']!='ingredients':raise HTTPException(400,'Bước thử gắn ảnh hiện cần Thành phần (Ingredients).')
        prompt=body.get('prompt')
        if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>20000:raise HTTPException(400,'Prompt trống hoặc quá dài.')
        for key in ('room_id','scene_id','part'):
            if not isinstance(body.get(key),str) or not body[key] or len(body[key])>100:raise HTTPException(400,'Thiếu định danh cảnh: '+key)
        async with service.gate:
            if service.busy() or service.unresolved():raise HTTPException(409,'Flow còn tác vụ hoặc lượt chưa rõ kết quả; chưa chuẩn bị lượt mới.')
            if not service.account_bridge:raise HTTPException(409,'Chọn tài khoản Flow tại tab Tài khoản.')
            selection=service.account_bridge.selection()
            if not selection['available'] or body.get('selection_token')!=selection['token']:raise HTTPException(409,'Tài khoản đã đổi hoặc chưa sẵn sàng.')
            upload=service.upload_report
            if not upload or not upload['delivered'] or upload.get('reference_sha256')!=body.get('reference_sha256'):raise HTTPException(409,'Tải đúng ảnh của cảnh lên dự án Flow trước bằng nút upload hiện có.')
            if not service.connected or not service.page or service.page.is_closed() or service.pinned_room!=body['room_id'] or service.pinned_account!=selection['account_id']:raise HTTPException(409,'Cần giữ đúng phiên dự án sau upload; upload lại ảnh của cảnh trong phòng hiện tại.')
            paths=[service.root/(upload['request_id']+ext) for ext in ('.png','.jpg','.webp')]
            paths=[p for p in paths if p.is_file()]
            if len(paths)!=1 or hashlib.sha256(paths[0].read_bytes()).hexdigest()!=body['reference_sha256']:raise HTTPException(409,'Không còn tệp ảnh gốc đã upload. Upload lại trước khi gắn prompt.')
            rid='flow-prepare-'+secrets.token_hex(12)
            report={'request_id':rid,'state':'running','message':'Đang đối chiếu ảnh, gắn vào ô tạo và điền prompt; chưa gửi tạo.', 'settings':settings,'account_id':selection['account_id'],'room_id':body['room_id'],'scene_id':body['scene_id'],'part':body['part'],'has_preview':False,'_prompt':prompt}
            service.prepare_report=report;service.active=rid;service.sent=False
            service.task=asyncio.create_task(run(report,paths[0],selection['token']))
            receipt=status(rid);receipt.pop('_prompt',None);return receipt
    @app.get('/local-api/flow/simple/prepare/{rid}')
    async def get_status(rid:str):
        report=status(rid);report.pop('_prompt',None);return report
    @app.get('/local-api/flow/simple/prepare/{rid}/preview')
    async def preview(rid:str):
        report=status(rid)
        if not report['has_preview']:raise HTTPException(404,'Chưa có ảnh kiểm tra prompt.')
        return FileResponse(service.root/(rid+'.prepare.png'),media_type='image/png',headers={'Cache-Control':'no-store'})
