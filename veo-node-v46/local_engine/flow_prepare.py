"""Bind a previously uploaded reference to its scene prompt; never submit here."""
import asyncio
import base64
import copy
import hashlib
import io
import json
import math
import secrets
from pathlib import Path
import re

from fastapi import HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageStat

from .flow_settings import DEFAULTS, apply_settings, settings_panel, read_settings, control, exact, validate_settings
from .simple_flow_dom import composer


class PrepareStopped(RuntimeError):
    pass


class ReferenceChoiceNeeded(PrepareStopped):
    def __init__(self, matches):
        super().__init__('Có nhiều ảnh khớp trong thư viện. Chọn một thumbnail để tiếp tục; chưa điền prompt hoặc gửi tạo.')
        self.matches=matches


def prompt_text(value):
    return str(value).replace('\r\n', '\n').strip()


async def editor_text(editor):
    return await editor.evaluate("e=>e.matches('input,textarea')?e.value:e.innerText")


def rendered_reference_error(image, expected, render):
    """Reproduce the img content box and CSS crop when canvas reads are blocked."""
    scale_x=image.width/max(1,render['width']);scale_y=image.height/max(1,render['height'])
    insets=render.get('insets',[0,0,0,0])
    content=(math.ceil(insets[0]*scale_x),math.ceil(insets[1]*scale_y),
             image.width-math.ceil(insets[2]*scale_x),image.height-math.ceil(insets[3]*scale_y))
    if content[2]<=content[0] or content[3]<=content[1]:return 255.0
    image=image.crop(content);width,height=image.size
    nw,nh=render['natural_width'],render['natural_height'];fit=render['object_fit']
    if fit=='fill':draw_w,draw_h=width,height
    else:
        factor=max(width/nw,height/nh) if fit=='cover' else min(width/nw,height/nh)
        if fit=='none':factor=(scale_x+scale_y)/2
        if fit=='scale-down':factor=min((scale_x+scale_y)/2,factor)
        draw_w,draw_h=nw*factor,nh*factor
    positions=render['object_position'].split()
    if len(positions)!=2:positions=['50%','50%']
    def offset(value,free,pixel_scale):
        try:
            if value.endswith('%'):return float(value[:-1])*free/100
            if value.endswith('px'):return float(value[:-2])*pixel_scale
        except ValueError:pass
        return {'left':0,'top':0,'right':free,'bottom':free,'center':free/2}.get(value,free/2)
    x=offset(positions[0],width-draw_w,scale_x);y=offset(positions[1],height-draw_h,scale_y)
    visible=(max(0,math.ceil(x)),max(0,math.ceil(y)),min(width,math.floor(x+draw_w)),min(height,math.floor(y+draw_h)))
    if visible[2]-visible[0]<8 or visible[3]-visible[1]<8:return 255.0
    source_box=(max(0,(visible[0]-x)*expected.width/draw_w),max(0,(visible[1]-y)*expected.height/draw_h),
                min(expected.width,(visible[2]-x)*expected.width/draw_w),min(expected.height,(visible[3]-y)*expected.height/draw_h))
    mask=Image.new('L',(width,height),0)
    radii=re.findall(r'\d+(?:\.\d+)?(?:px|%)?',render.get('border_radius','0'))
    radius=max([float(x[:-1])*min(width,height)/100 if x.endswith('%') else float(x.removesuffix('px'))*(scale_x+scale_y)/2 for x in radii]or[0])
    radius=min(min(width,height)/2,max(0,radius))
    ImageDraw.Draw(mask).rounded_rectangle((1,1,width-2,height-2),radius=max(0,radius-1),fill=255)
    mask=mask.crop(visible)
    image=image.crop(visible)
    source=expected.resize(image.size,Image.Resampling.LANCZOS,box=source_box)
    # Exclude only borders and clipped corners, retaining the visible edge detail.
    size=(min(48,image.width),min(48,image.height))
    left=source.resize(size,Image.Resampling.LANCZOS)
    right=image.resize(size,Image.Resampling.LANCZOS)
    mask=mask.resize(size,Image.Resampling.NEAREST)
    if not mask.getbbox():return 255.0
    return sum(ImageStat.Stat(ImageChops.difference(left,right),mask=mask).mean)/3


def image_error(raw, expected, crop=False, small=False, render=None):
    with Image.open(io.BytesIO(raw)) as image:
        image = ImageOps.exif_transpose(image).convert('RGB')
        if render is not None:return rendered_reference_error(image,expected,render)
        source = ImageOps.fit(expected, image.size) if crop else expected
        size=(min(48,image.width),min(48,image.height)) if small else (48,48)
        left = source.resize(size, Image.Resampling.LANCZOS)
        right = image.resize(size, Image.Resampling.LANCZOS)
        return sum(ImageStat.Stat(ImageChops.difference(left,right)).mean)/3


async def reference_images(scope, expected, report=None, small=False):
    images = scope.locator('img').filter(visible=True)
    if await images.count() > 80:
        raise PrepareStopped('Có quá nhiều ảnh để đối chiếu an toàn. Thu gọn thư viện Flow rồi thử lại.')
    matches=[];candidates=[]
    for index in range(await images.count()):
        item=await images.nth(index).element_handle()
        if item is None:continue
        details=await item.evaluate('''(e,small)=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e),n=k=>parseFloat(s[k])||0;return {ready:e.complete&&e.naturalWidth>=(small?8:33)&&e.naturalHeight>=(small?8:33)&&(!small||(r.width>=20&&r.height>=20)),
            composer:!!e.closest('[data-sf-flow-composer]'),src:e.currentSrc||e.src,
            width:r.width,height:r.height,natural_width:e.naturalWidth,natural_height:e.naturalHeight,
            object_fit:s.objectFit,object_position:s.objectPosition,border_radius:s.borderRadius,
            insets:[n('borderLeftWidth')+n('paddingLeft'),n('borderTopWidth')+n('paddingTop'),n('borderRightWidth')+n('paddingRight'),n('borderBottomWidth')+n('paddingBottom')],
            media:e.closest('[data-media-id],[data-asset-id]')?.getAttribute('data-media-id')||e.closest('[data-asset-id]')?.getAttribute('data-asset-id')||null}}''',small)
        if not details['ready']:continue
        try:
            encoded=await item.evaluate('''e=>{try{const c=document.createElement('canvas'),scale=Math.min(1,256/Math.max(e.naturalWidth,e.naturalHeight));c.width=Math.max(1,Math.round(e.naturalWidth*scale));c.height=Math.max(1,Math.round(e.naturalHeight*scale));c.getContext('2d').drawImage(e,0,0,c.width,c.height);return c.toDataURL('image/png').split(',')[1]}catch{return null}}''')
            raw=base64.b64decode(encoded) if encoded else await item.screenshot(timeout=3000)
            score=image_error(raw,expected,crop=small or not bool(encoded),small=small,render=details if small and not encoded else None)
        except Exception:
            continue
        candidates.append({'index':index,'error':round(score,3),'composer':details['composer'],
                           'media_id':details['media'],'source_hash':hashlib.sha256(details['src'].encode()).hexdigest(),
                           'capture_method':'canvas' if encoded else 'screenshot',
                           **{k:details[k] for k in ('object_fit','object_position','border_radius','natural_width','natural_height','width','height')}})
        if score <= 4:
            marker='data-sf-reference-'+secrets.token_hex(10)
            stable=await item.evaluate('''(e,{src,marker})=>{
                if(!e.isConnected||(e.currentSrc||e.src)!==src)return false;
                e.setAttribute(marker,'');return true;
            }''',{'src':details['src'],'marker':marker})
            if not stable:continue
            pinned=scope.locator('img['+marker+']')
            matches.append({'item':pinned,'error':round(score,3),'composer':details['composer'],
                            'media_id':details['media'],'source_hash':hashlib.sha256(details['src'].encode()).hexdigest()})
    if report is not None:
        report['image_matches']=[{k:v for k,v in m.items() if k!='item'} for m in matches]
        report['image_candidates']=sorted(candidates,key=lambda x:x['error'])[:20]
    return matches


async def reference_scope(page):
    editor,scope=await composer(page)
    if editor is None or scope is None:return editor,scope
    best=scope
    # Flow can place attachment chips above the inner prompt/button row.
    # Expand only within a small composer card, never into the library grid.
    for depth in range(1,5):
        candidate=scope.locator('xpath=ancestor::*['+str(depth)+']')
        if not await candidate.count():break
        acceptable=await candidate.evaluate('''e=>{
            const r=e.getBoundingClientRect();
            if(['BODY','HTML'].includes(e.tagName)||r.height>400||r.width>1200)return false;
            const editors=[...e.querySelectorAll('textarea,[contenteditable="true"],[role="textbox"]')].filter(x=>x.getClientRects().length);
            if(editors.length!==1||e.querySelector('article,video'))return false;
            if([...e.querySelectorAll('button')].some(x=>/^(Favorite|More options|Add media menu)$/i.test(x.getAttribute('aria-label')||'')))return false;
            return [...e.querySelectorAll('img')].every(x=>{const b=x.getBoundingClientRect();return !b.width||(b.width<=128&&b.height<=128)});
        }''')
        if not acceptable:break
        best=candidate
        if await candidate.evaluate("e=>e.tagName==='FORM'"):break
    return editor,best


async def attached_reference(page, expected, expected_media_id=None, report=None):
    editor,scope=await reference_scope(page)
    if editor is None or scope is None:return False
    await scope.evaluate("e=>e.setAttribute('data-sf-flow-composer','true')")
    probe={'expected_media_id':expected_media_id}
    if report is not None:report['attachment_probe']=probe
    probe['scope']=await scope.evaluate("e=>({tag:e.tagName,width:Math.round(e.getBoundingClientRect().width),height:Math.round(e.getBoundingClientRect().height)})")
    probe['editor_contains_media']=bool(await editor.locator('img,[data-media-id],[data-asset-id]').count())
    if await scope.locator('[role=progressbar],[aria-busy=true],[role=alert]').filter(visible=True).count():
        probe['busy_or_error']=True;return False
    probe['images']=await scope.locator('img').evaluate_all('''xs=>xs.filter(e=>e.getClientRects().length).map(e=>({
        natural_width:e.naturalWidth,natural_height:e.naturalHeight,width:Math.round(e.getBoundingClientRect().width),height:Math.round(e.getBoundingClientRect().height),loaded:e.complete
    }))''')
    usable=[x for x in probe['images'] if x['loaded'] and x['natural_width']>=8 and x['natural_height']>=8 and x['width']>=20 and x['height']>=20]
    chips=await scope.locator('[data-media-id],[data-asset-id]').evaluate_all('''xs=>xs.filter(e=>{
        const r=e.getBoundingClientRect();if(r.width<12||r.height<12||r.width>160||r.height>160)return false;
        return e.matches('img,canvas')||!!e.querySelector('img,canvas')||[e,...e.querySelectorAll('*')].slice(0,12).some(x=>getComputedStyle(x).backgroundImage!=='none');
    }).map(e=>e.getAttribute('data-media-id')||e.getAttribute('data-asset-id')).filter(Boolean)''')
    probe['media_ids']=sorted(set(chips))
    if expected_media_id and probe['media_ids']==[expected_media_id] and len(usable)<=1:
        probe['verified_by']='media_id';return True
    if len(usable)==1:
        image_report={};matches=await reference_images(scope,expected,image_report,small=True)
        probe['image_candidates']=image_report.get('image_candidates',[])
        if len(matches)==1:
            probe['verified_by']='small_thumbnail_pixels';return True
    if expected_media_id is None and len(probe['media_ids'])==1 and len(usable)<=1:
        # A persisted CSS chip can survive app restart without a remembered
        # binding. Its ID must occur on a library thumbnail matching the source.
        library=await reference_images(page,expected)
        ids={m['media_id'] for m in library if not m['composer'] and m['media_id']}
        if probe['media_ids'][0] in ids:
            probe['verified_by']='media_id_from_matched_library';return True
    return False


async def prepare_composer(page, reference, prompt, settings, check, report, selected_reference=None):
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
    editor,scope=await reference_scope(page)
    if editor is None or scope is None:raise PrepareStopped('Chưa nhận diện duy nhất ô tạo Flow.')
    await scope.evaluate("e=>e.setAttribute('data-sf-flow-composer','true')")
    current=prompt_text(await editor_text(editor))
    if current and current!=prompt_text(prompt):
        raise PrepareStopped('Ô Flow đang có prompt khác. Kiểm tra và dọn ô tạo trước; chưa ghi đè.')
    if not await attached_reference(page,expected,(selected_reference or {}).get('media_id'),report):
        if report.get('attachment_probe',{}).get('media_ids'):
            raise PrepareStopped('Ô tạo đang gắn media chưa khớp ảnh nguồn. Kiểm tra và dọn ảnh đó trước; chưa thêm ảnh khác.')
        existing=scope.locator('img').filter(visible=True)
        for item in await existing.all():
            if await item.evaluate('e=>e.complete&&e.naturalWidth>=8&&e.naturalHeight>=8&&e.getBoundingClientRect().width>=20&&e.getBoundingClientRect().height>=20'):
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
        if selected_reference:
            chosen=[m for m in matches if (m['media_id']==selected_reference['media_id'] if selected_reference.get('media_id') else m['source_hash']==selected_reference.get('source_hash'))]
            if len(chosen)==1:
                matches=chosen
                report['reference_selection']='explicit_or_remembered_choice'
            elif matches:
                raise ReferenceChoiceNeeded(matches)
        if len(matches)>1:
            raise ReferenceChoiceNeeded(matches)
        if len(matches)!=1:
            raise PrepareStopped('Chưa xác định duy nhất đúng ảnh đã upload trong thư viện (khớp '+str(len(matches))+'). Không chọn ảnh gần giống hoặc ảnh đầu danh sách.')
        match=matches[0];report['matched_reference']={k:v for k,v in match.items() if k not in ('item','composer')}
        current_source=await match['item'].evaluate('e=>e.currentSrc||e.src')
        if hashlib.sha256(current_source.encode()).hexdigest()!=match['source_hash']:
            raise PrepareStopped('Thumbnail đã đổi trong lúc đối chiếu. Chuẩn bị lại; chưa mở menu ảnh.')
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
            if await attached_reference(page,expected,match['media_id'],report):break
            option=page.get_by_role('menuitem',name=re.compile(r'^(Image|Hình ảnh)$',re.I)).or_(page.get_by_role('option',name=re.compile(r'^(Image|Hình ảnh)$',re.I))).filter(visible=True)
            if await option.count()==1:await option.click(timeout=5000)
            await asyncio.sleep(.15)
        else:raise PrepareStopped('Đã bấm Add to prompt nhưng chưa đối chiếu được đúng ảnh trong ô tạo.')
    phase('fill_scene_prompt')
    await check()
    editor,scope=await reference_scope(page)
    if prompt_text(await editor_text(editor))!=prompt_text(prompt):
        if await editor.locator('img,[data-media-id],[data-asset-id]').count():
            # An inline reference must survive text insertion. No Select All,
            # Enter key or submit shortcut is used here.
            await editor.focus();await editor.press('Control+End')
            await page.keyboard.insert_text(prompt)
        else:
            await editor.fill(prompt,timeout=5000)
    if prompt_text(await editor_text(editor))!=prompt_text(prompt):raise PrepareStopped('Prompt đọc lại không khớp nguyên nội dung của cảnh.')
    if not await attached_reference(page,expected,report.get('matched_reference',{}).get('media_id') or (selected_reference or {}).get('media_id'),report):raise PrepareStopped('Ảnh trong ô tạo đã đổi trước khi xác nhận prompt.')
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
    if editor is None or prompt_text(await editor_text(editor))!=prompt_text(payload['prompt']) or not await attached_reference(service.page,expected,(report.get('matched_reference') or report.get('selected_reference') or {}).get('media_id')):
        raise PrepareStopped('Ảnh hoặc prompt thực tế trong Flow không còn khớp. Chưa gửi tạo.')


def register_prepare_routes(app, service):
    service.prepare_report=None;service.prepared_page=None;service.prepared_reference=None
    service.reference_choices={}
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
            await prepare_composer(service.page,reference,report.pop('_prompt'),report['settings'],check,report,report.get('selected_reference'))
            service.prepared_page=service.page;service.prepared_reference=reference
            matched=report.get('matched_reference')
            if matched:
                service.reference_choices[(report['account_id'],report['room_id'],report['reference_sha256'])]={k:matched[k] for k in ('media_id','source_hash')}
            report.update(state='ready',message='Đã đối chiếu đúng ảnh và prompt trong ô tạo. Xem ảnh kiểm tra trước khi tạo một lần.')
        except ReferenceChoiceNeeded as error:
            choices=[]
            for index,match in enumerate(error.matches[:8]):
                candidate_id=secrets.token_hex(8)
                candidate={'id':candidate_id,'media_id':match['media_id'],'source_hash':match['source_hash'],'error':match['error'],'has_preview':False}
                try:
                    await match['item'].screenshot(path=str(service.root/(report['request_id']+'.candidate-'+candidate_id+'.png')),timeout=3000)
                    candidate['has_preview']=True
                except Exception:pass
                choices.append(candidate)
            report.update(state='awaiting_selection',message='Có '+str(len(error.matches))+' ảnh khớp trong thư viện. Chọn thumbnail bên dưới để gắn đúng ảnh và tiếp tục điền prompt; chưa gửi tạo.',candidates=choices)
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
            selected=service.reference_choices.get((selection['account_id'],body['room_id'],body['reference_sha256']))
            choice=body.get('candidate_choice')
            if choice is not None:
                previous=service.prepare_report
                if (not isinstance(choice,dict) or not previous or previous['state']!='awaiting_selection'
                    or choice.get('request_id')!=previous['request_id']
                    or any(previous.get(k)!=body[k] for k in ('room_id','scene_id','part','reference_sha256'))
                    or previous['account_id']!=selection['account_id'] or previous['settings']!=settings
                    or previous['prompt_sha256']!=hashlib.sha256(prompt.encode()).hexdigest()):
                    raise HTTPException(409,'Ảnh, prompt, cảnh hoặc tài khoản đã đổi. Bấm Gắn ảnh + điền prompt lại trước khi chọn.')
                candidates=[c for c in previous['candidates'] if c['id']==choice.get('candidate_id')]
                if len(candidates)!=1:raise HTTPException(409,'Lựa chọn thumbnail không thuộc lượt chuẩn bị này.')
                selected={k:candidates[0][k] for k in ('media_id','source_hash')}
            rid='flow-prepare-'+secrets.token_hex(12)
            report={'request_id':rid,'state':'running','message':'Đang đối chiếu ảnh, gắn vào ô tạo và điền prompt; chưa gửi tạo.', 'settings':settings,'account_id':selection['account_id'],'room_id':body['room_id'],'scene_id':body['scene_id'],'part':body['part'],'has_preview':False,'_prompt':prompt,'reference_sha256':body['reference_sha256'],'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'selected_reference':selected}
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
    @app.get('/local-api/flow/simple/prepare/{rid}/candidates/{candidate_id}')
    async def candidate_preview(rid:str,candidate_id:str):
        report=status(rid)
        candidates=[c for c in report.get('candidates',[]) if c['id']==candidate_id and c['has_preview']]
        if len(candidates)!=1:raise HTTPException(404,'Không có thumbnail của lựa chọn này.')
        return FileResponse(service.root/(rid+'.candidate-'+candidates[0]['id']+'.png'),media_type='image/png',headers={'Cache-Control':'no-store'})
