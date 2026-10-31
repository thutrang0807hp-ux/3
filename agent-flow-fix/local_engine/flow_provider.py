from .admission import guarded_submission
from contextlib import nullcontext
"""Flow2API loopback bridge. Explicit submissions, bounded concurrency, no retries.

This speaks the inspected upstream OpenAI-compatible protocol. Real provider
generation must still be verified with a user's locally configured Flow engine.
"""
import asyncio, base64, hashlib, io, json, os, re, time, uuid
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from .account_pool import AccountPool
from fastapi import HTTPException
from fastapi.responses import FileResponse
from PIL import Image
from .batch_images import BatchImages
from .image_transport import prepare_images
from .request_ledger import NO_RESULT, RequestConflict


def local_url(value):
    try:
        p = urlsplit(value)
        if p.scheme != 'http' or p.hostname != '127.0.0.1' or not p.port or p.username or p.password or p.path not in ('', '/') or p.query or p.fragment:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(400, 'Địa chỉ engine phải là http://127.0.0.1:PORT, không có đường dẫn.')
    return value.rstrip('/')


class FlowProvider:
    def __init__(self, vault, root, ledger, client_factory=None):
        self.vault, self.ledger = vault, ledger
        self.root = Path(root) / 'flow-results'
        self.root.mkdir(exist_ok=True, mode=0o700)
        self.client_factory = client_factory or (lambda: httpx.AsyncClient(timeout=1800, follow_redirects=False, trust_env=False))
        self.tasks = {}
        self.assignments = {}
        self.reconcile_locks = {}
        self.model_discovery_lock=asyncio.Lock()
        self.model_discovery_attempt=-1e9
        self.model_discovery_error=None
        self.lane = asyncio.Semaphore(3)
        from .video_slots import VideoSlots
        self.video_slots = VideoSlots(vault, 'flow')
        from .image_slots import ImageSlots
        self.image_slots = ImageSlots(vault, 'flow')

    def config(self):
        return self.vault.secret('flow-engine') or {}

    def status(self):
        c = self.config()
        selection=AccountPool(self.vault,'flow').status()
        if getattr(self,'web_ui',None)and self.web_ui.binding(selection.get('account_id')):
            return {'configured':True,'url':'browser-ui','account_binding':True,'task_journal':True,'selection':selection,**self.video_slots.status(),**self.image_slots.status(),'models':['veo-3.1-lite-i2v-8s-portrait'],'model_details':[{'id':'veo-3.1-lite-i2v-8s-portrait','description':'Veo 3.1 Lite · 8s · I2V · web UI (thử nghiệm)','accepts_images':True,'video_type':'i2v','max_images':1}],'generation_verified':bool(self.vault.secret('flow-ui-generation-verified')),'automatic_retry':False,'muse_available':False,'transport':'web_ui','connection_method':'managed_browser'}

        return {'configured': bool(c.get('url') and c.get('key')), 'url': c.get('url', 'http://127.0.0.1:8766'),
                **self.video_slots.status(), **self.image_slots.status(), 'account_binding': bool(c.get('account_binding')), 'task_journal':bool(c.get('task_journal')), 'selection': AccountPool(self.vault, 'flow').status(),
                'models': c.get('models', []), 'model_details': c.get('model_details', []), 'checked_at': c.get('checked_at'),
                'generation_verified': bool(c.get('generation_verified')),
                'automatic_retry': False, 'muse_available': False}

    async def ready_status(self):
        if self.status().get('transport')=='web_ui':return self.status()
        # Local catalog reads are free; never require a separate settings action.
        if self.config().get('key') and (not self.config().get('models') or self.model_discovery_attempt<0):
            async with self.model_discovery_lock:
                if (not self.config().get('models') or self.model_discovery_attempt<0) and time.monotonic()-self.model_discovery_attempt>=15:
                    self.model_discovery_attempt=time.monotonic()
                    try:
                        await self.discover()
                        self.model_discovery_error=None
                    except HTTPException as exc:
                        self.model_discovery_error=str(exc.detail)
        result=self.status()
        if not result['models'] and self.model_discovery_error:result['models_error']=self.model_discovery_error
        return result

    def configure(self, body):
        if self.tasks:
            raise HTTPException(409, 'Đợi các tác vụ Flow hiện tại hoàn tất trước khi đổi engine.')
        url = local_url(body.get('url'))
        key = body.get('key')
        if not isinstance(key, str) or not 12 <= len(key) <= 512 or any(ch in key for ch in '\r\n'):
            raise HTTPException(400, 'Nhập API key riêng của engine Flow, tối thiểu 12 ký tự; không nhập cookie Google.')
        self.model_discovery_attempt=-1e9;self.model_discovery_error=None
        self.vault.set_secret('flow-engine', {'url': url, 'key': key, 'models': [], 'generation_verified': False})
        return self.status()

    async def discover(self):
        if self.status().get('transport')=='web_ui':return self.status()
        c = self.config()
        if not c.get('key'):
            raise HTTPException(409, 'Chưa cấu hình engine Flow cục bộ.')
        try:
            async with self.client_factory() as client:
                r = await client.get(c['url'] + '/v1/models', headers={'Authorization': 'Bearer ' + c['key']}, timeout=15)
                if r.status_code != 200:
                    raise ValueError()
                if len(r.content) > 1024 * 1024:
                    raise ValueError()
                rows = r.json()['data']
                if not isinstance(rows,list) or not rows or len(rows)>2000:raise ValueError()
                models = [m['id'] for m in rows if isinstance(m, dict) and isinstance(m.get('id'), str)
                          and re.fullmatch(r'[A-Za-z0-9._:-]{1,160}', m['id'])]
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise HTTPException(502, 'Chưa đọc được model từ engine Flow. Không gửi yêu cầu tạo nào.')
        details = []
        for m in rows:
            if not isinstance(m, dict) or m.get('id') not in models:
                continue
            item = {'id': m['id'], 'description': str(m.get('description', ''))[:300]}
            contract = m.get('sceneforge_inputs')
            # Only an explicit model-level transport contract enables first/last frames.
            # A model name, prose description or number of accepted references is insufficient.
            if isinstance(contract, dict) and contract.get('transport') == 'ordered_images' and contract.get('first_image') == 'start':
                item['sceneforge_inputs'] = {'transport': 'ordered_images', 'first_image': 'start',
                    'second_image': 'end' if contract.get('second_image') == 'end' else None,
                    'text_to_video': contract.get('text_to_video') is True}
            if isinstance(m.get('sceneforge_accepts_images'),bool):item['accepts_images']=m['sceneforge_accepts_images']
            if m.get('sceneforge_video_type') in ('t2v','i2v','r2v','omni'):item['video_type']=m['sceneforge_video_type']
            if type(m.get('sceneforge_max_images')) is int and 0<=m['sceneforge_max_images']<=8:item['max_images']=m['sceneforge_max_images']
            details.append(item)
        self.model_discovery_error=None
        latest=self.config()
        if any(latest.get(k)!=c.get(k)for k in ('url','key')):raise HTTPException(409,'Engine Flow đã đổi trong lúc đọc model; mở lại node để đọc nguồn mới.')
        latest.update(models=sorted(set(models)), model_details=details, checked_at=time.time())
        self.vault.set_secret('flow-engine', latest)
        return self.status()

    @staticmethod
    def valid_id(value):
        if not isinstance(value, str) or not re.fullmatch(r'flow-[a-f0-9-]{36}', value):
            raise HTTPException(400, 'Mã tác vụ Flow không hợp lệ.')
        try:
            uuid.UUID(value[5:])
        except ValueError:
            raise HTTPException(400, 'Mã tác vụ Flow không hợp lệ.')

    def lookup(self, request_id):
        self.valid_id(request_id)
        with self.ledger.connect() as db:
            row = db.execute('SELECT state,result,updated FROM request WHERE id=?', (request_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'Không có tác vụ Flow này.')
        failure=self.ledger.metadata(request_id).get('flow_error',{})
        return {**self.ledger.receipt(request_id), 'request_id': request_id, 'state': row[0], 'result': json.loads(row[1]) if row[0] == 'done' else None,
                'updated': row[2], 'automatic_retry': False,**({k:failure[k]for k in ('code','message','http_status')if k in failure}if isinstance(failure,dict)else {})}

    @guarded_submission
    async def submit(self, body):
        # A web cookie import is not a live browser binding. Fail before any
        # engine preflight can open its own guest/verification browser.
        service=getattr(self,'account_service',None)
        if service is not None:
            selected=service.pool.status().get('account_id')
            account=next((a for a in service.pool.rows()if a['id']==selected),None)
            if account and not account.get('native_route_id') and not (getattr(self,'web_ui',None)and self.web_ui.binding(account['id'])):
                raise HTTPException(409,'Đã nhận đăng nhập web nhưng chưa nối đường tạo video với tab Flow. Chưa gửi tạo và không mở cửa sổ đăng nhập khác. Hiện cần nối tab bằng tiện ích/mã; tự nối từ đăng nhập web chưa hoàn chỉnh.')
        if service is not None and account and account.get('login_transport')=='web_ui'and service.pool.status().get('mode')!='selected':raise HTTPException(409,'Bản thử web cần chế độ Dùng riêng tài khoản đã chọn; chưa gửi.')
        if body.get('confirm_send') is not True:
            raise HTTPException(409, 'Xác nhận gửi tới Flow; tạo video/ảnh có thể tốn credit.')
        c = self.config()
        if self.status().get('transport')=='web_ui':c={**c,'url':'browser-ui','key':'local-web-ui-no-api','account_binding':True,'models':self.status()['models'],'model_details':self.status()['model_details']}
        if not c.get('key') or body.get('model') not in c.get('models', []):
            raise HTTPException(409, 'Kết nối engine, đọc model và chọn model Flow trước.')
        rid = body.get('request_id')
        self.valid_id(rid)
        prompt, refs, kind = body.get('prompt'), body.get('references', []), body.get('kind')
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 20000 or kind not in ('image', 'video'):
            raise HTTPException(400, 'Prompt tối đa 20.000 ký tự; đầu ra ảnh hoặc video.')
        model = body['model'].lower()
        if kind == 'video' and 'image' in model or kind == 'image' and model.startswith(('veo-', 'omni-')):
            raise HTTPException(400, 'Model đã chọn không khớp loại đầu ra. Chưa gửi yêu cầu.')
        if isinstance(refs,list)and len(refs)<=8:refs=prepare_images(refs)
        if not isinstance(refs, list) or len(refs) > 8 or sum(BatchImages.decode_image(r) for r in refs) > 24 * 1024**2:
            raise HTTPException(400, 'Tối đa 8 ảnh tham chiếu, tổng 24 MB.')
        selected=next((m for m in c.get('model_details',[])if m.get('id')==body['model']),{})
        if kind=='video'and refs and selected.get('accepts_images')is False:
            raise HTTPException(409,'Model này chỉ tạo video từ chữ và sẽ bỏ ảnh khung. Chọn model nhận ảnh (I2V) trên node; chưa gửi tạo video.')
        frame_inputs = body.get('frame_inputs')
        if frame_inputs is not None:
            if kind != 'video' or not isinstance(frame_inputs, dict) or frame_inputs.get('mode') not in ('start', 'pair'):
                raise HTTPException(400, 'Liên kết ảnh đầu/cuối không hợp lệ.')
            pair = frame_inputs['mode'] == 'pair'
            if len(refs) < (2 if pair else 1):
                raise HTTPException(400, 'Thiếu byte ảnh đầu/cuối; chưa gửi yêu cầu.')
            for field in ('start_id', 'slot') + (('end_id',) if pair else ()):
                if not isinstance(frame_inputs.get(field), str) or not re.fullmatch(r'[A-Za-z0-9_:-]{1,180}', frame_inputs[field]):
                    raise HTTPException(400, 'Mã ảnh/cảnh không hợp lệ.')
            if body.get('scene_id') and body.get('part') and frame_inputs['slot'] != str(body['scene_id']) + ':' + str(body['part']):
                raise HTTPException(400, 'Ảnh đầu/cuối thuộc mã cảnh/phần khác; chưa gửi.')
            contract = next((m.get('sceneforge_inputs', {}) for m in c.get('model_details', []) if m.get('id') == body['model']), {})
            if pair and not (contract.get('transport') == 'ordered_images' and contract.get('first_image') == 'start' and contract.get('second_image') == 'end'):
                raise HTTPException(409, 'Model/adapter chưa xác nhận ảnh đầu + cuối; không gửi và không bỏ ảnh cuối.')
            frame_inputs = {k: frame_inputs.get(k) for k in ('mode', 'start_id', 'end_id', 'slot')}
        if len(self.tasks) >= 30:
            raise HTTPException(429, 'Hàng chờ Flow đầy; chưa gửi tác vụ mới.')
        payload = {'kind': kind, 'model': body['model'], 'prompt': prompt, 'references': refs, 'engine': c['url'],'room_id':str(body.get('room_id',''))[:100],'scene_id':str(body.get('scene_id',''))[:100]}
        if frame_inputs is not None:
            payload['frame_inputs'] = frame_inputs
            payload['part'] = str(body.get('part', ''))[:40]
        if hasattr(self, 'account_service'):
            selection = self.account_service.pool.status()
            if not c.get('account_binding') or not selection['available'] or body.get('selection_token') != selection['token']:
                raise HTTPException(409, 'Đồng bộ và chọn tài khoản Flow; rà lại lựa chọn trước khi gửi.')
            payload.update(mode=selection['mode'], plan=selection['permitted'], selection_token=selection['token'])
            if getattr(self,'web_ui',None)and self.web_ui.binding(selection.get('account_id')) and selection['mode']=='selected'and account:payload['web_ui_account']=selection['account_id']
        try:
            _, cached = self.ledger.claim(rid, payload)
        except (ValueError, RequestConflict) as e:
            raise HTTPException(409, str(e))
        if cached is not NO_RESULT:
            return self.lookup(rid)
        if 'plan' in payload:
            self.assignments[rid] = min(payload['plan'], key=lambda a: list(self.assignments.values()).count(a)) if payload['mode'] == 'balanced' else payload['plan'][0]
        self.tasks[rid] = asyncio.create_task(self.run(rid, payload, c))
        def finished(task):
            self.tasks.pop(rid, None)
            self.assignments.pop(rid, None)
        self.tasks[rid].add_done_callback(finished)
        return self.lookup(rid)

    @staticmethod
    def output_url(data):
        if isinstance(data.get('url'), str):
            return data['url']
        try:
            text = data['choices'][0]['message']['content']
            if not isinstance(text, str):
                return None
            match = re.search(r'!\[[^\]]*\]\(([^\s)]+)\)|<video[^>]*\bsrc=[\"\x27]([^\"\x27]+)', text)
            return next((v for v in match.groups() if v), None) if match else None
        except (KeyError, IndexError, TypeError):
            return None

    async def run(self, rid, payload, config):
        if payload.get('web_ui_account'):return await self._run_web_ui(rid,payload)
        if not hasattr(self, 'account_service'):
            return await self._run_one(rid, payload, config)
        import contextlib
        service = self.account_service
        sent = False
        plan = payload['plan'] if payload['mode'] == 'failover' else payload['plan'][:1]
        if payload['mode'] == 'balanced':
            plan = [self.assignments[rid]]
        try:
            for aid in plan:
                async with (self.image_slots.slot(aid) if payload['kind']=='image' else self.video_slots.slot(aid)):
                    self.assignments[rid] = aid
                    row = next((a for a in service.pool.rows() if a['id'] == aid), None)
                    if not row or not service.pool.eligible(row):
                        continue
                    checked = await service.check(aid)
                    reason = 'auth' if checked.get('accepted') is False and checked.get('reason') == 'auth' else (
                        'quota' if checked.get('ok') and checked.get('credit') == 0 and payload['kind'] == 'video' else None)
                    if reason:
                        service.pool.limit(aid, reason)
                        if payload['mode'] == 'failover':
                            continue
                        break
                    if not checked.get('ok'):
                        break
                    await service.prepare_concurrency(aid, payload['kind'])
                    sent = True
                    return await self._run_one(rid, {**payload, 'account_id': aid, 'engine_id': row['engine_id']}, config)
            self.ledger.finish(rid, 'unknown' if sent else 'failed')
        except asyncio.CancelledError:
            self.ledger.finish(rid, 'unknown')
            raise
        except Exception:
            self.ledger.finish(rid, 'unknown' if sent else 'failed')

    async def _run_web_ui(self,rid,payload):
        from .flow_ui_driver import UiFlowFailure
        target=self.root/(rid+'.partial');sent=False
        def dispatched():
            nonlocal sent
            sent=True;self.ledger.set_metadata(rid,{'web_ui_sent':True,'transport':'web_ui','account_id':payload['web_ui_account'],'room_id':payload.get('room_id'),'scene_id':payload.get('scene_id')})
        self.ledger.set_metadata(rid,{'transport':'web_ui','account_id':payload['web_ui_account']})
        try:
            if payload['kind']!='video':raise UiFlowFailure('Bản thử web chỉ hỗ trợ video từ một ảnh.')
            if self.ledger.storage:self.ledger.storage.reserve_download(rid,8*1024**2)
            await self.web_ui.generate(payload['web_ui_account'],payload['model'],payload['prompt'],payload['references'],target,dispatched)
            size=target.stat().st_size
            if not 0<size<=500*1024**2:raise UiFlowFailure('Kết quả tải xuống vượt giới hạn hoặc rỗng.',True)
            from .machine_checks import run_command
            rc,output,_=await run_command('ffprobe','-v','error','-protocol_whitelist','file,pipe','-show_streams','-of','json',str(target),timeout=30)
            streams=json.loads(output).get('streams',[])if not rc else []
            if not any(x.get('codec_type')=='video'for x in streams):raise UiFlowFailure('Tệp tải chưa được xác nhận là video.',True)
            with target.open('rb')as stream:header=stream.read(4)
            fmt='video/webm'if header==b'\x1aE\xdf\xa3'else'video/mp4'
            name=rid+('.webm'if fmt=='video/webm'else'.mp4');digest=hashlib.sha256()
            with target.open('rb')as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
            digest=digest.hexdigest();os.replace(target,self.root/name)
            result={'file':name,'mime_type':fmt,'sha256':digest,'bytes':size,'account_id':payload['web_ui_account'],'room_id':payload.get('room_id'),'scene_id':payload.get('scene_id'),'model':payload['model'],'kind':'video','origin':'flow','cost':None}
            self.ledger.finish(rid,'done',result)
            self.vault.set_secret('flow-ui-generation-verified',True)
        except asyncio.CancelledError:
            self.ledger.finish(rid,'unknown'if sent else'failed');raise
        except Exception as exc:
            uncertain=sent or bool(getattr(exc,'sent',False))
            message=str(exc)if isinstance(exc,UiFlowFailure)else'Không hoàn tất được luồng web. Đã dừng; không tự gửi lại.'
            self.ledger.set_metadata(rid,{'flow_error':{'code':'FLOW_UI_OUTCOME_UNKNOWN'if uncertain else'FLOW_UI_NOT_SUBMITTED','message':message}})
            self.ledger.finish(rid,'unknown'if uncertain else'failed')
        finally:
            target.unlink(missing_ok=True)
            try:
                entry=self.lookup(rid)
                self.vault.put('logs',{'id':rid,'request_id':rid,'service':'flow','kind':'Flow','state':entry['state'],'transport':'web_ui','account_id':payload['web_ui_account'],'code':entry.get('code'),'message':entry.get('message'),'at':time.time(),'cost':None})
            except Exception:pass

    async def _run_one(self, rid, payload, config, recovered_response=None):
        state, result, code = 'unknown', None, 'UNKNOWN'
        tmp = self.root / (rid + '.partial')
        try:
            async with self.lane if not hasattr(self, 'account_service') else nullcontext():
                parts = [{'type': 'text', 'text': payload.get('prompt','')}] + [
                    {'type': 'image_url', 'image_url': {'url': 'data:' + r['mime_type'] + ';base64,' + r['data']}}
                    for r in payload.get('references',[])]
                async with self.client_factory() as client:
                    self.ledger.set_metadata(rid,{'provider':'flow','account_id':payload.get('account_id'),'engine_id':payload.get('engine_id'),'model':payload['model'],'kind':payload['kind'],'frame_inputs':payload.get('frame_inputs'),'room_id':payload.get('room_id'),'scene_id':payload.get('scene_id'),'engine_instance':hashlib.sha256((config['url']+config['key']).encode()).hexdigest()})
                    if recovered_response is None:
                        async with client.stream('POST', config['url'] + '/v1/chat/completions',
                                                 headers={'Authorization': 'Bearer ' + config['key'], 'X-SceneForge-Request':rid, **({'X-SceneForge-Room':hashlib.sha256(payload['room_id'].encode()).hexdigest()} if payload.get('room_id') else {}), **({'X-SceneForge-Account': str(payload['engine_id'])} if 'engine_id' in payload else {})},
                                                 json={'model': payload['model'], 'messages': [{'role': 'user', 'content': parts}], 'stream': False}) as r:
                            if r.status_code != 200:
                                state = 'failed' if r.status_code in (400, 401, 403, 404, 422, 429) else 'unknown'
                                code = 'HTTP_' + str(r.status_code)
                                return
                            if 'engine_id' in payload and r.headers.get('x-sceneforge-account') != str(payload['engine_id']):
                                code = 'ACCOUNT_BINDING_UNCONFIRMED'
                                return
                            chunks, total = [], 0
                            async for chunk in r.aiter_bytes():
                                total += len(chunk)
                                if total > 2 * 1024**2:
                                    raise ValueError('oversized response')
                                chunks.append(chunk)
                        response_data=json.loads(b''.join(chunks))
                    else:response_data=recovered_response
                    url = self.output_url(response_data)
                    p, origin = urlsplit(url or ''), urlsplit(config['url'])
                    # Never fetch arbitrary model-supplied URLs or send engine keys to a CDN.
                    if not url or p.username or p.password or p.fragment or not (
                        (p.scheme, p.hostname, p.port) == (origin.scheme, origin.hostname, origin.port)
                        or p.scheme == 'https' and p.hostname in ('storage.googleapis.com', 'lh3.googleusercontent.com') and p.port in (None, 443)):
                        code = 'UNSUPPORTED_RESULT_URL'
                        return
                    size = 0
                    async with client.stream('GET', url, headers={}) as media:
                        if media.status_code != 200:
                            code = 'RESULT_DOWNLOAD_FAILED'
                            return
                        mime = media.headers.get('content-type', '').split(';')[0]
                        allowed = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp'} if payload['kind'] == 'image' else {'video/mp4': '.mp4', 'video/webm': '.webm'}
                        if mime not in allowed:
                            code = 'RESULT_TYPE_MISMATCH'
                            return
                        if self.ledger.storage:
                            try:expected=int(media.headers.get('content-length','0'))
                            except ValueError:expected=0
                            self.ledger.storage.reserve_download(rid,expected or 8*1024**2)
                        digest = hashlib.sha256()
                        with tmp.open('xb') as out:
                            async for chunk in media.aiter_bytes():
                                size += len(chunk)
                                if size > (24 if payload['kind'] == 'image' else 500) * 1024**2:
                                    raise ValueError('oversized media')
                                if self.ledger.storage and(size==len(chunk)or size//(8*1024**2)!=(size-len(chunk))//(8*1024**2)):self.ledger.storage.reserve_download(rid,8*1024**2)
                                digest.update(chunk)
                                out.write(chunk)
                            out.flush()
                            os.fsync(out.fileno())
                    if not size:
                        raise ValueError('empty media')
                    if payload['kind'] == 'image':
                        with Image.open(tmp) as image:
                            if image.width * image.height > 40_000_000:
                                raise ValueError('oversized image')
                            image.verify()
                    else:
                        # Check actual decode before accepting a file as a completed video.
                        from .machine_checks import run_command
                        rc, output, _ = await run_command('ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-show_streams', '-of', 'json', str(tmp), timeout=30)
                        if rc or not any(s.get('codec_type') == 'video' for s in json.loads(output).get('streams', [])):
                            raise ValueError('invalid video')
                    name = rid + allowed[mime]
                    os.replace(tmp, self.root / name)
                    result = {'file': name, 'mime_type': mime, 'sha256': digest.hexdigest(), 'bytes': size,
                              'account_id': payload.get('account_id'),'room_id':payload.get('room_id'),'scene_id':payload.get('scene_id'),
                              'model': payload['model'], 'kind': payload['kind'], 'origin': 'flow', 'cost': None}
                    state, code = 'done', 'DONE'
                    current = self.config()
                    if current.get('url') == config['url'] and current.get('key') == config['key']:
                        current['generation_verified'] = True
                        self.vault.set_secret('flow-engine', current)
        except asyncio.CancelledError:
            code = 'INTERRUPTED'
            raise
        except Exception:
            code = 'NETWORK_OR_RESULT_UNKNOWN'
        finally:
            tmp.unlink(missing_ok=True)
            self.ledger.finish(rid, state, result)
            self.vault.put('logs', {'id': rid,'request_id':rid,'service':'flow','account_id':payload.get('account_id'), 'kind': 'Flow', 'state': state, 'code': code, 'at': time.time(), 'cost': None})

    async def reconcile(self,rid):
        async with self.reconcile_locks.setdefault(rid,asyncio.Lock()):
            return await self._reconcile(rid)

    async def _reconcile(self,rid):
        record=self.lookup(rid)
        if self.ledger.metadata(rid).get('transport')=='web_ui':return {**record,'reconciliation':record['state']}
        if record['state']=='done':return record
        if rid in self.tasks:raise HTTPException(409,'Lượt vẫn đang chạy trong app; chờ kết quả.')
        meta=self.ledger.metadata(rid);config=self.config()
        if not meta.get('engine_id')or meta.get('engine_instance')!=hashlib.sha256((config.get('url','')+config.get('key','')).encode()).hexdigest():raise HTTPException(409,'Không có định danh engine/tài khoản gốc để đối soát. Không tạo lại.')
        async with self.client_factory()as client:
            response=await client.get(config['url']+'/sceneforge/tasks/'+rid+'?refresh_media=true',headers={'Authorization':'Bearer '+config['key']},timeout=120)
            if response.status_code!=200 or len(response.content)>2*1024**2:raise HTTPException(409,'Engine chưa tìm được kết quả; kiểm tra lịch sử. Không gửi tạo mới.')
            remote=response.json()
        if remote.get('account_id')!=meta['engine_id']:raise HTTPException(409,'Tài khoản engine không khớp lượt gốc; chưa nhận kết quả.')
        if remote.get('state')!='done':
            # Only return safe known engine diagnostics; no raw upstream response.
            allowed={'PUBLIC_ERROR_UNUSUAL_ACTIVITY','CAPTCHA_REQUIRED','AUTH_OR_ACCESS_DENIED','QUOTA_OR_RATE_LIMIT','CONTENT_REJECTED','MODEL_UNAVAILABLE','IMAGE_INPUT_REJECTED','ENGINE_ERROR_DETAILS_NOT_SAVED','UPSTREAM_LOOKUP_UNAVAILABLE'}
            code=remote.get('code');failure={}
            if code in allowed or isinstance(code,str)and re.fullmatch(r'ENGINE_HTTP_[1-5][0-9]{2}',code):
                from .flow_task_journal import safe_failure
                if code=='ENGINE_ERROR_DETAILS_NOT_SAVED':failure={'code':code,'message':'Engine xác nhận lượt thất bại nhưng bản cũ chưa lưu lý do; không thể khôi phục nguyên nhân từ lượt này.'}
                elif code=='UPSTREAM_LOOKUP_UNAVAILABLE':failure={'code':code,'message':'Engine chưa đọc được trạng thái upstream. Giữ lượt cũ; chưa gửi lại.'}
                else:
                    status=remote.get('http_status',400)
                    if type(status)is not int or not 100<=status<=599:status=400
                    hints={'PUBLIC_ERROR_UNUSUAL_ACTIVITY':'PUBLIC_ERROR_UNUSUAL_ACTIVITY','CAPTCHA_REQUIRED':'captcha','AUTH_OR_ACCESS_DENIED':'unauthorized','QUOTA_OR_RATE_LIMIT':'quota','CONTENT_REJECTED':'policy','MODEL_UNAVAILABLE':'invalid model','IMAGE_INPUT_REJECTED':'invalid image'}
                    failure=safe_failure(status,hints.get(code,''))
                self.ledger.set_metadata(rid,{'flow_error':failure})
                self.vault.put('logs',{'id':rid,'request_id':rid,'service':'flow','kind':'Flow','account_id':meta.get('account_id'),'state':record['state'],'code':failure['code'],'message':failure['message'],'at':time.time(),'cost':None})
            if remote.get('state')=='failed':
                self.ledger.finish(rid,'failed')
                record=self.lookup(rid)
                self.vault.put('logs',{'id':rid,'request_id':rid,'service':'flow','kind':'Flow','account_id':meta.get('account_id'),'state':'failed','code':failure.get('code'),'message':failure.get('message'),'at':time.time(),'cost':None})
            return {**record,'reconciliation':remote.get('state','unknown'),**failure}

        (self.root/(rid+'.partial')).unlink(missing_ok=True)
        await self._run_one(rid,meta,config,recovered_response=remote['response'])
        return self.lookup(rid)

    def file(self, rid):
        if self.ledger.storage:
            stored=self.ledger.storage.file(rid)
            if stored is not None:
                record=self.lookup(rid)
                if record['state']=='done':return FileResponse(stored,media_type=record['result'].get('mime_type','application/octet-stream'),filename=record['result'].get('file',rid))
        record = self.lookup(rid)
        if record['state'] != 'done':
            raise HTTPException(409, 'Chưa có kết quả Flow được lưu. Không tự gửi lại.')
        result = record['result']
        name = result.get('file', '')
        if name not in {rid + ext for ext in ('.png', '.jpg', '.webp', '.mp4', '.webm')} or not (self.root / name).is_file():
            raise HTTPException(404, 'Thiếu tệp kết quả Flow.')
        return FileResponse(self.root / name, media_type=result['mime_type'], filename=name)

    async def close(self):
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        close=getattr(getattr(self,'web_ui',None),'close',None)
        if close:await close()


def install_flow_provider(app, vault, root, ledger):
    service = FlowProvider(vault, root, ledger)
    app.get('/local-api/flow/status')(service.ready_status)
    @app.post('/local-api/flow/configure')
    async def configure(body: dict):
        return service.configure(body)
    app.post('/local-api/flow/models')(service.discover)
    @app.post('/local-api/flow/jobs')
    async def submit(body: dict):
        return await service.submit(body)
    app.get('/local-api/flow/jobs/{request_id}')(service.lookup)
    app.get('/local-api/flow/jobs/{rid}/reconcile')(service.reconcile)
    app.get('/local-api/flow/files/{rid}')(service.file)
    return service
