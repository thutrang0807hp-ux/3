"""One automatic image+prompt trial. This path never clicks Generate."""
import asyncio,base64,copy,hashlib,io,json,secrets,re,shutil,tempfile
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse
from PIL import Image
from .simple_flow_upload import upload_to_project
from .flow_settings import DEFAULTS,apply_settings,validate_settings,control,exact
from .flow_prepare import reference_scope,editor_text,prompt_text,current_attachment,remove_approved_attachment,original_reference_pixels

class PairStopped(RuntimeError):pass

async def library_snapshot(page,stem):
    _,scope=await reference_scope(page)
    if scope is None:raise PairStopped('Chưa xác định được vùng ô tạo để tách khỏi thư viện.')
    await page.locator('[data-sf-flow-composer]').evaluate_all('xs=>xs.forEach(e=>e.removeAttribute("data-sf-flow-composer"))')
    await scope.evaluate("e=>e.setAttribute('data-sf-flow-composer','true')")
    data=await page.locator('[data-media-id],[data-asset-id]').evaluate_all('''(xs,stem)=>{
      const roots=xs.filter(e=>!e.closest('[data-sf-flow-composer]'));
      if(roots.length>2000)return {truncated:true,records:[]};
      return {truncated:false,records:roots.map(e=>{
        const id=e.getAttribute('data-media-id')||e.getAttribute('data-asset-id');
        const images=(e.matches('img')?[e]:[...e.querySelectorAll('img')]).filter(i=>i.closest('[data-media-id],[data-asset-id]')===e);
        const clone=e.cloneNode(true);clone.querySelectorAll('[data-media-id],[data-asset-id]').forEach(c=>c.remove());
        const labels=[e.getAttribute('data-filename'),e.getAttribute('data-name'),e.getAttribute('aria-label'),e.getAttribute('title'),clone.textContent,...images.flatMap(i=>[i.alt,i.title])].filter(Boolean).join(' ');
        const busy=[...e.querySelectorAll('[role=progressbar],[aria-busy=true]')].some(x=>x.getClientRects().length);
        const ready=!busy; // Metadata/action readiness, never decoded preview pixels.
        return {id,ready,filename_match:labels.includes(stem),sources:images.map(i=>i.currentSrc||i.src).filter(Boolean)};
      }).filter(x=>x.id)};
    }''',stem)
    if data['truncated']:raise PairStopped('Thư viện có quá nhiều phần tử để theo dấu lượt upload đầy đủ.')
    records={}
    for item in data['records']:
        previous=records.setdefault(item['id'],{'ready':False,'filename_match':False,'sources':[]})
        previous['ready']|=item['ready'];previous['filename_match']|=item['filename_match']
        previous['sources']=sorted(set(previous['sources']+item.get('sources',[])))
    return records

def comparable_prompt(value):
    # Rich-text editors may render paragraph breaks and NBSP differently.
    # Only whitespace is normalized; no words, punctuation or case are discarded.
    return re.sub(r'\s+', ' ', prompt_text(value)).strip()

async def write_prompt(page,prompt,replace=False,probe=None,report=None):
    editor,_=await reference_scope(page)
    if editor is None:raise PairStopped('Chưa tìm được duy nhất ô prompt trên Flow.')
    if report is not None:report['prompt_expected']=prompt
    expected=comparable_prompt(prompt)
    current=comparable_prompt(await editor_text(editor))
    if current!=expected:
        inline=await editor.locator('img,[data-media-id],[data-asset-id]').count()
        if inline and not replace:
            if current:raise PairStopped('Prompt đổi sau khi gắn ảnh; chưa sửa nội dung inline làm mất ảnh.')
            await editor.focus();await editor.press('Control+End');await page.keyboard.insert_text(prompt)
        else:
            await editor.fill(prompt,timeout=10000)
    if report is not None:report['prompt_filled']=True
    for attempt in range(8):
        try:readback=prompt_text(await editor_text(editor))
        except Exception as exc:
            if probe is not None:probe.update(verified=False,readback_error=type(exc).__name__)
            return None
        if report is not None:report['prompt_actual']=readback
        observed=comparable_prompt(readback)
        if probe is not None:
            probe.update(expected_length=len(prompt),observed_length=len(readback),
                         observed_sha256=hashlib.sha256(readback.encode()).hexdigest(),
                         comparison='whitespace_normalized',attempts=attempt+1,verified=observed==expected)
        if observed==expected:
            return hashlib.sha256(readback.encode()).hexdigest()
        await asyncio.sleep(.15)
    return hashlib.sha256(readback.encode()).hexdigest()

async def trace_uploaded_media(page,before,stem,check,report,timeout=30):
    deadline=asyncio.get_running_loop().time()+timeout
    inspected={}
    provenance=report['upload_provenance']
    while asyncio.get_running_loop().time()<deadline:
        await check();after=await library_snapshot(page,stem)
        named=[key for key,value in after.items()if key not in before and value['ready']and value['filename_match']]
        new=[key for key,value in after.items()if key not in before and value['ready']]
        provenance.update(new_ids=new,filename_match_ids=named,stage='identify_uploaded_asset')
        if len(named)==1:
            provenance['method']='unique_upload_filename';return named[0]
        # Some Flow cards never expose the filename. Inspect only NEW assets;
        # match downloaded original bytes to the source SHA, never thumbnail pixels.
        exact_ids=[]
        for media_id in new[:8]:
            for url in after[media_id].get('sources',[])[:2]:
                await check()
                key=(media_id,hashlib.sha256(url.encode()).hexdigest())
                if key not in inspected:
                    remaining=deadline-asyncio.get_running_loop().time()
                    if remaining<=0:break
                    probe={}
                    try:
                        raw=await asyncio.wait_for(original_reference_pixels(page,url,probe), min(2,remaining))
                        inspected[key]=bool(raw and hashlib.sha256(raw).hexdigest()==report.get('reference_sha256'))
                    except asyncio.TimeoutError:
                        probe['original_read']='timeout'
                    provenance.setdefault('original_byte_checks',[]).append({'media_id':media_id,**probe})
                if inspected.get(key):exact_ids.append(media_id);break
        exact_ids=sorted(set(exact_ids))
        provenance['exact_original_ids']=exact_ids
        if len(exact_ids)==1:
            provenance['method']='source_sha256_of_new_asset';return exact_ids[0]
        await asyncio.sleep(.25)
    raise PairStopped('Không xác định được duy nhất ảnh mới bằng tên tệp hoặc SHA-256 ảnh gốc. Không đoán ảnh từ thứ tự hay thumbnail.')

async def media_image(page,media_id):
    marker='data-sf-pair-'+secrets.token_hex(8)
    await page.locator('[data-media-id],[data-asset-id]').evaluate_all('''(xs,{id,marker})=>{for(const e of xs){if((e.getAttribute('data-media-id')||e.getAttribute('data-asset-id'))===id&&!e.closest('[data-sf-flow-composer]'))e.setAttribute(marker,'')}}''',{'id':media_id,'marker':marker})
    images=page.locator('['+marker+']')
    if not await images.count():raise PairStopped('Không còn phần tử của media ID vừa upload.')
    # Multiple renderings of one asset share the same ID; any eligible card is that asset.
    for image in await images.all():
        for depth in range(0,9):
            card=image if depth==0 else image.locator('xpath=ancestor::*['+str(depth)+']')
            if not await card.count()or await card.evaluate("e=>['BODY','HTML'].includes(e.tagName)"):break
            ids=await card.locator('[data-media-id],[data-asset-id]').evaluate_all("xs=>xs.map(e=>e.getAttribute('data-media-id')||e.getAttribute('data-asset-id'))")
            if any(value!=media_id for value in ids):break
            if not await card.is_visible():continue
            await card.hover()
            more=await control(card,exact(r'More options|More|Tùy chọn khác|Tuỳ chọn khác'))
            if await more.count()==1 and await more.is_enabled():return image,more
    raise PairStopped('Chưa tìm được menu của chính media ID vừa tải; không mở menu ảnh khác.')

async def composer_state(page):
    _,scope=await reference_scope(page)
    if scope is None:return {'count':0,'ids':[]}
    photos=await scope.locator('img').evaluate_all('''xs=>xs.filter(e=>{const r=e.getBoundingClientRect();return r.width>=20&&r.height>=20}).map(e=>{const p=e.closest('[data-media-id],[data-asset-id]');return p&&(p.getAttribute('data-media-id')||p.getAttribute('data-asset-id'))})''')
    return {'count':len(photos),'ids':sorted({x for x in photos if x})}

async def attach_traced_media(page,media_id,check,report):
    report['attachment_stage']='locate_media_menu'
    await page.keyboard.press('Escape')
    image,more=await media_image(page,media_id)
    existing=await composer_state(page)
    if existing['count']:
        if existing['count']==1 and existing['ids']==[media_id]:return existing
        current=await current_attachment(page)
        if current is None:raise PairStopped('Ô tạo có nhiều ảnh hoặc cấu trúc chưa hỗ trợ thay tự động. Prompt vẫn đã được điền.')
        await remove_approved_attachment(page,current['fingerprint'],check,report)
    # Removing an old chip can rerender controls. Reacquire the same asset ID.
    image,more=await media_image(page,media_id);await check();await more.click(timeout=5000)
    report['attachment_stage']='find_add_to_prompt'
    action=None
    for _ in range(30):
        action=await control(page,exact(r'Add to prompt|Thêm vào câu lệnh|Thêm vào lời nhắc|Thêm vào prompt'))
        if await action.count()==1:break
        await asyncio.sleep(.1)
    if action is None or await action.count()!=1:raise PairStopped('Menu ảnh vừa upload chưa có duy nhất Add to prompt.')
    await check();report['attachment_stage']='click_add_to_prompt';await action.click(timeout=5000)
    report['attachment_stage']='observe_composer_attachment'
    for _ in range(40):
        await check();state=await composer_state(page)
        if state['count']==1:
            if state['ids']and state['ids']!=[media_id]:raise PairStopped('ID ảnh trong ô tạo khác media ID vừa upload.')
            report['attachment_evidence']='composer_media_id'if state['ids']else'tracked_upload_and_single_chip_transition'
            return state
        option=page.get_by_role('menuitem',name=exact(r'Image|Hình ảnh')).or_(page.get_by_role('option',name=exact(r'Image|Hình ảnh'))).filter(visible=True)
        if await option.count()==1:await option.click(timeout=5000)
        await asyncio.sleep(.15)
    raise PairStopped('Đã gọi Add to prompt của ảnh vừa tải nhưng chưa thấy đúng một ảnh trong ô tạo.')

async def upload_and_fill_prompt(
    page, image_path, prompt, settings=None, check=None, report=None,
    *, upload_timeout=20, settings_timeout=15, prompt_timeout=12,
    attachment_timeout=10, attempt_attachment=True,
):
    """Send image and text independently of previews. Never click Generate."""
    reference = Path(image_path)
    if not reference.is_file() or not 0 < reference.stat().st_size <= 6*1024**2:
        raise PairStopped('Ảnh không tồn tại hoặc vượt 6 MB.')
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 20000:
        raise PairStopped('Prompt trống hoặc quá dài.')
    if any(t <= 0 for t in (upload_timeout, settings_timeout, prompt_timeout, attachment_timeout)):
        raise ValueError('Timeout phải lớn hơn 0.')
    if check is None:
        async def check(): pass
    report = {} if report is None else report
    report.update(state='running', delivered=False, upload_uncertain=False,
                  prompt_filled=False, prompt_verified=False, image_attached=False, settings_verified=False,
                  generation_submitted=False, logs=[], errors={}, upload_report={},
                  settings_report={}, upload_provenance={})
    for key in ('uploaded_media_id', 'attachment_evidence', 'composer_state', 'prompt_readback_sha256', 'prompt_probe', 'prompt_actual', 'prompt_expected'):
        report.pop(key, None)
    def log(message): report['logs'].append(message)
    def phase(name, message):
        report.update(phase=name, message=message)
        log(message)
    def error(step, exc):
        detail = str(exc).strip() or type(exc).__name__
        report['errors'][step] = {'type': type(exc).__name__, 'message': detail}
        log(step + ': ' + detail)
    async def fill(replace):
        report['prompt_verified'] = False
        digest = await asyncio.wait_for(write_prompt(page, prompt, replace=replace, probe=report.setdefault('prompt_probe',{}), report=report), prompt_timeout)
        report.update(prompt_verified=bool(report.get('prompt_probe',{}).get('verified')), prompt_readback_sha256=digest)
        report['errors'].pop('prompt', None)
        log('Đã điền prompt; đọc lại khớp.' if report['prompt_verified'] else 'Đã điền prompt; chưa xác nhận đọc lại khớp. Xem prompt_expected và prompt_actual trong báo cáo.')
    if not re.fullmatch(r'flow-pair-[a-f0-9]{24}', reference.stem):
        destination = Path(tempfile.mkdtemp(prefix='sceneforge-pair-')) / ('flow-pair-'+secrets.token_hex(12)+reference.suffix)
        shutil.copyfile(reference, destination)
        reference = destination
    report.update(reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                  prompt_sha256=hashlib.sha256(prompt_text(prompt).encode()).hexdigest())
    try:
        await check()
        phase('settings', 'Đang thử áp dụng cấu hình Flow.')
        try:
            chosen = validate_settings(dict(DEFAULTS) if settings is None else settings)
            report['settings_verified'] = bool(await asyncio.wait_for(
                apply_settings(page, chosen, check, report['settings_report']), settings_timeout))
            if not report['settings_verified']: log('Chưa xác nhận cấu hình; vẫn tiếp tục ảnh và prompt.')
        except Exception as exc:
            error('settings', exc)
            log('Cấu hình chưa hoàn tất; vẫn tiếp tục ảnh và prompt.')
        await check()
        try: await asyncio.wait_for(page.keyboard.press('Escape'), 2)
        except Exception as exc: error('close_menu', exc)
        before = None
        if attempt_attachment:
            try: before = await asyncio.wait_for(library_snapshot(page, reference.stem), 3)
            except Exception as exc: error('snapshot', exc)
        report['upload_provenance'] = {'before_count': len(before) if before is not None else None,
                                       'source_filename': reference.name}
        phase('uploading', 'Đang giao tệp ảnh cho Flow bằng đường upload .19.')
        await check()
        try:
            report['delivered'] = bool(await asyncio.wait_for(
                upload_to_project(page, reference, log, report['upload_report']), upload_timeout))
            report['upload_uncertain'] = not report['delivered']
            log('Đã giao tệp ảnh.' if report['delivered'] else 'Chưa xác nhận giao tệp; không tự gửi lại.')
        except Exception as exc:
            report['upload_uncertain'] = True
            error('upload', exc)
            log('Chưa xác nhận giao tệp; Flow có thể vẫn đang nhận ảnh. Không tự gửi lại.')
        phase('fill_prompt', 'Đang điền prompt ngay, không chờ preview.')
        await check()
        try: await fill(True)
        except Exception as exc: error('prompt', exc)
        attempted = False
        if attempt_attachment and report['delivered'] and before is not None:
            attempted = True
            phase('attach_image', 'Đang thử gắn đúng ảnh vừa tải; prompt được xử lý riêng.')
            report['attachment_stage']='identify_uploaded_asset'
            async def attach():
                await check()
                media_id = await trace_uploaded_media(page, before, reference.stem, check, report, timeout=attachment_timeout)
                report['uploaded_media_id'] = media_id
                await check()
                report['composer_state'] = await attach_traced_media(page, media_id, check, report)
                report['image_attached'] = True
            await check()
            try: await asyncio.wait_for(attach(), attachment_timeout)
            except Exception as exc: error('attachment', exc)
        log('Đã gắn ảnh vào prompt.' if report['image_attached'] else 'Chưa xác nhận gắn ảnh; không chặn việc điền prompt.')
        if attempted or not report['prompt_verified']:
            phase('verify_prompt', 'Đang kiểm tra lại prompt sau bước gắn ảnh.')
            await check()
            try: await fill(False)
            except Exception as exc: error('prompt', exc)
        await check()
        complete = report['delivered'] and report.get('prompt_filled', False)
        report.update(state='inputs_sent' if complete else 'partial', phase='complete',
                      message=('Đã giao tệp và điền prompt; '+('đã ghi nhận gắn ảnh.' if report['image_attached'] else 'chưa xác nhận gắn ảnh.')+' Đọc lại prompt được báo riêng; chưa tạo video.') if complete else 'Chưa xác nhận đủ ảnh và prompt. Xem báo cáo; chưa tạo video.')
    except asyncio.CancelledError:
        report.update(state='cancelled', phase='stopped', message='Đã dừng lượt thử; chưa tạo video.')
        raise
    except Exception as exc:
        error('workflow', exc)
        report.update(state='failed', phase='stopped', message='Đã dừng lượt thử: '+str(exc))
    finally:
        report['generation_submitted'] = False
        if report['upload_uncertain'] and report['prompt_filled']:
            log('Prompt đã điền dù upload chưa xác nhận.')
        log(f"Kết quả: delivered={report['delivered']}, prompt_filled={report['prompt_filled']}, prompt_verified={report['prompt_verified']}, attached={report['image_attached']}")
    return report


async def run_pair(service,report,raw,mime,prompt,settings,token):
    reference=service.root/(report['request_id']+{'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[mime])
    async def check():
        selection=service.account_bridge.selection()
        if not selection['available']or selection['account_id']!=report['account_id']or selection['token']!=token:raise PairStopped('Tài khoản đã đổi; đã dừng thao tác.')
        await service.assert_ready()
    try:
        reference.write_bytes(raw);report.update(phase='opening',message='Đang mở dự án Flow của phòng hiện tại.')
        await service.disconnect_browser();await service.restore();await check()
        service.pair_page=service.page
        deadline=asyncio.get_running_loop().time()+90
        while asyncio.get_running_loop().time()<deadline:
            await check();editor,_=await reference_scope(service.page)
            if editor is not None:break
            await asyncio.sleep(.25)
        else:raise PairStopped('Flow chưa tải xong ô nhập sau 90 giây.')
        # Direct composer trial; the library uploader remains unchanged for diagnostics.
        report.update(logs=[],errors={},settings_verified=False)
        try:
            report['settings_verified']=bool(await asyncio.wait_for(apply_settings(service.page,settings,check,report.setdefault('settings_report',{})),15))
        except Exception as exc:
            report['errors']['settings']={'type':type(exc).__name__,'message':str(exc)}
            report['logs'].append('Cấu hình chưa hoàn tất; vẫn tiếp tục ảnh và prompt.')
        await check()
        await asyncio.wait_for(service.page.keyboard.press('Escape'),timeout=2)
        from .flow_composer_upload import upload_into_composer_and_fill
        await upload_into_composer_and_fill(service.page,reference,prompt,check,report=report)
    except asyncio.CancelledError:
        report.update(state='failed',message='Đã dừng lượt thử; chưa gửi tạo video.');raise
    except Exception as error:
        report.update(state='failed',message=str(error)if isinstance(error,PairStopped)else'Lượt thử dừng: '+type(error).__name__)
    finally:
        report['generation_submitted']=False
        (service.root/(report['request_id']+'.pair.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        service.active=None

def register_pair_routes(app,service):
    service.pair_report=None;service.pair_trial_only=True;service.pair_page=None
    def status(rid):
        report=service.pair_report
        if not report or report['request_id']!=rid:raise HTTPException(404,'Không có lượt thử ảnh/prompt này trong phiên hiện tại.')
        return copy.deepcopy(report)
    @app.post('/local-api/flow/simple/pair-trial')
    async def start(body:dict):
        if body.get('trial_only')is not True or body.get('replace_composer')is not True:raise HTTPException(400,'Cần xác định lượt thử thay ảnh/prompt trong ô tạo, chưa gửi tạo video.')
        settings=validate_settings(body.get('settings'))
        if settings['mode']!='ingredients':raise HTTPException(400,'Lượt thử dùng Thành phần (Ingredients).')
        prompt=body.get('prompt')
        if not isinstance(prompt,str)or not prompt.strip()or len(prompt)>20000:raise HTTPException(400,'Prompt trống hoặc quá dài.')
        for key in ('room_id','scene_id','part'):
            if not isinstance(body.get(key),str)or not body[key]or len(body[key])>100:raise HTTPException(400,'Thiếu định danh cảnh: '+key)
        ref=body.get('reference')or{}
        try:
            raw=base64.b64decode(ref.get('data',''),validate=True)
            if not 0<len(raw)<=6*1024**2:raise ValueError()
            with Image.open(io.BytesIO(raw))as image:
                if image.width*image.height>40_000_000:raise ValueError()
                image.verify();mime=Image.MIME.get(image.format)
            if mime not in ('image/png','image/jpeg','image/webp')or mime!=ref.get('mime_type'):raise ValueError()
        except Exception:raise HTTPException(400,'Ảnh không hợp lệ hoặc vượt 6 MB.')from None
        async with service.gate:
            if service.busy()or service.unresolved():raise HTTPException(409,'Flow còn tác vụ hoặc lượt chưa rõ kết quả.')
            if not service.account_bridge:raise HTTPException(409,'Chọn tài khoản Flow tại tab Tài khoản.')
            selection=service.account_bridge.selection()
            if not selection['available']or body.get('selection_token')!=selection['token']:raise HTTPException(409,'Tài khoản đã đổi hoặc chưa sẵn sàng.')
            rid='flow-pair-'+secrets.token_hex(12)
            report={'request_id':rid,'state':'running','message':'Đang tự đưa ảnh và prompt của cảnh sang Flow; chưa tạo video.','room_id':body['room_id'],'scene_id':body['scene_id'],'part':body['part'],'account_id':selection['account_id'],'reference_sha256':hashlib.sha256(raw).hexdigest(),'prompt_sha256':hashlib.sha256(prompt_text(prompt).encode()).hexdigest(),'delivered':False,'image_attached':False,'prompt_filled':False,'prompt_verified':False,'settings_verified':False,'has_preview':False,'generation_submitted':False,'logs':[],'errors':{}}
            service.prepare_report=None;service.prepared_page=None;service.prepared_reference=None
            service.pair_page=None
            service.pair_report=report;service.upload_report=report;service.active=rid;service.sent=False
            service.pinned_account=selection['account_id'];service.pinned_room=body['room_id']
            service.task=asyncio.create_task(run_pair(service,report,raw,mime,prompt,settings,selection['token']))
            return status(rid)
    @app.get('/local-api/flow/simple/pair-trial/{rid}')
    async def get_status(rid:str):return status(rid)
    @app.get('/local-api/flow/simple/pair-trial/{rid}/preview')
    async def preview(rid:str):
        report=status(rid)
        if not report['has_preview']:
            async with service.gate:
                report=status(rid)
                if service.busy():raise HTTPException(409,'Lượt thử đang chạy. Việc xem ảnh là tùy chọn, không chặn gửi ảnh/prompt.')
                if not service.page or service.page is not service.pair_page or service.page.is_closed():raise HTTPException(404,'Phiên Flow đã đổi; không còn ảnh hiện tại của lượt thử.')
                await service.assert_ready()
                try:await service.page.screenshot(path=str(service.root/(rid+'.pair.png')),timeout=3000)
                except Exception:raise HTTPException(503,'Chưa chụp được Flow. Kết quả gửi ảnh/prompt không thay đổi.')from None
                service.pair_report['has_preview']=True
        return FileResponse(service.root/(rid+'.pair.png'),media_type='image/png',headers={'Cache-Control':'no-store'})
