from .admission import guarded_submission
from .image_slots import ImageSlots
from .gemini_conversations import conversation_key, valid_metadata
from contextlib import nullcontext
"""Gemini Chat account adapter, isolated SDK and durable task queue. No paid fallback."""
import asyncio
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import time
import uuid
from fastapi import HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw, ImageOps
from .muse_provider import MuseProvider
from .account_pool import AccountPool, safe_rejection
from .batch_images import BatchImages
from .request_ledger import NO_RESULT, RequestConflict


def evidence_sheets(images):
    """Label original CPU frames by code; at most eight evidence attachments."""
    if len(images) > 32:
        raise HTTPException(400, 'Tối đa 32 ảnh mỗi lượt; chia phân tích theo nhóm tối đa 8 cảnh.')
    output, counts = [], {}
    for start in range(0, len(images), 4):
        part = images[start:start+4]
        sheet = Image.new('RGB', (1280, ((len(part)+1)//2)*1160), '#171c22')
        draw = ImageDraw.Draw(sheet)
        for index, (code, data, mime) in enumerate(part):
            counts[code] = counts.get(code, 0) + 1
            with Image.open(io.BytesIO(base64.b64decode(data, validate=True))) as image:
                if image.width*image.height > 40_000_000:
                    raise HTTPException(400, 'Khung ảnh quá lớn.')
                image = image.convert('RGB'); image.thumbnail((620, 1100))
                x, y = (index%2)*640, (index//2)*1160
                sheet.paste(image, (x+(640-image.width)//2, y+28))
                draw.text((x+8, y+8), str(code)[:80]+' / '+str(counts[code]), fill='white')
        encoded = io.BytesIO()
        sheet.save(encoded, format='JPEG', quality=88)
        output.append({'mime_type': 'image/jpeg', 'data': base64.b64encode(encoded.getvalue()).decode()})
    return output


class GeminiChat(MuseProvider):
    worker_script = 'gemini_chat_worker.py'

    def __init__(self, vault, data, ledger, runner=None):
        super().__init__(vault, data, ledger, runner)
        self.root = Path(data) / 'gemini-chat-results'
        self.root.mkdir(exist_ok=True, mode=0o700)
        self.pool = AccountPool(vault, 'gemini_chat')
        self.logins = {}
        self.conversation_locks = {}
        self.image_slots = ImageSlots(vault, 'gemini_chat')

    def engine(self):
        root = Path(os.environ.get('SCENEFORGE_GEMINI_WEB_DIRECTORY', str(self.data / 'engines/gemini-web')))
        return root / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

    def accounts(self):
        return self.pool.rows()

    def selection(self):
        choice = self.pool.status()
        roles = self.vault.secret('gemini-chat-roles') or {}
        choice['token'] = hashlib.sha256((choice['token'] + json.dumps(roles, sort_keys=True)).encode()).hexdigest()
        return choice

    def select(self, body: dict):
        result = self.pool.select(body)
        return {**result, 'selection': self.selection()}

    def status(self):
        selection = self.selection()
        return {'installed': self.engine().is_file(), 'configured': selection['available'], 'adapter': True,
                'selection': selection, 'accounts': self.accounts(), 'per_account': 1, 'max_concurrency': 3, **self.image_slots.status(),
                'generation_verified': bool(self.vault.secret('gemini-chat-generation')), 'automatic_retry': False,
                'roles': self.vault.secret('gemini-chat-roles') or {}, 'service_url': 'https://gemini.google.com/'}

    def require_sdk(self):
        if self.runner == self.worker and not self.engine().is_file():
            raise HTTPException(409, 'Chạy local_engine/install-gemini-web.bat trước khi dùng Gemini Chat.')

    async def login(self, body: dict):
        self.require_sdk()
        name = body.get('name', '')
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise HTTPException(400, 'Nhập tên để nhận biết tài khoản Gemini.')
        supplied = body.get('cookies')
        if supplied is None:
            if len(self.logins) >= 5:
                raise HTTPException(409, 'Đóng các cửa sổ đăng nhập chưa lưu trước khi mở thêm.')
            from .google_login import open_google_login
            login = await open_google_login('https://gemini.google.com/', self.data)
            browser = context = pw = login
            aid = 'gchat-account-' + uuid.uuid4().hex
            self.logins[aid] = {'name': name.strip(), 'browser': browser, 'context': context, 'pw': pw}
            return {'id': aid, 'awaiting_login': True}
        return await self.import_session(name.strip(), supplied)

    async def confirm(self, body: dict):
        login = self.logins.get(body.get('id'))
        if not login:
            raise HTTPException(409, 'Cửa sổ đăng nhập không còn mở.')
        cookies = await login['context'].cookies()
        # Keep the interactive window available when sign-in is incomplete or
        # verification fails. Close only after a verified session was committed.
        result = await self.import_session(login['name'], cookies)
        await self.cancel_login(body['id'])
        return result

    async def cancel_login(self, aid):
        login = self.logins.pop(aid, None)
        if login:
            await login['browser'].close()
            await login['pw'].stop()
        return {'ok': True}

    async def import_session(self, name, supplied):
        if isinstance(supplied, str):
            if len(supplied) > 200000:
                raise HTTPException(400, 'Cookie JSON quá lớn.')
            try:
                supplied = json.loads(supplied)
            except ValueError:
                raise HTTPException(400, 'Cookie cần là JSON xuất từ trình duyệt.') from None
        if isinstance(supplied, dict):
            supplied = supplied.get('cookies', [])
        if not isinstance(supplied, list) or len(supplied) > 300:
            raise HTTPException(400, 'Cookie cần là danh sách JSON.')
        clean = {}
        for c in supplied:
            if not isinstance(c, dict):
                continue
            domain = str(c.get('domain', '')).lstrip('.')
            if domain not in ('google.com', 'gemini.google.com'):
                continue
            key, value = c.get('name'), c.get('value')
            if isinstance(key, str) and isinstance(value, str) and len(key) <= 200 and len(value) <= 16000:
                clean[key] = value
        if not clean.get('__Secure-1PSID'):
            raise HTTPException(400, 'Thiếu cookie phiên Google __Secure-1PSID; đăng nhập Gemini trước.')
        # Fingerprint the supplied session, not an unverified account email.
        aid = 'gchat-account-' + hashlib.sha256(clean['__Secure-1PSID'].encode()).hexdigest()[:24]
        async with self.image_slots.exclusive(aid), self.lock(aid):
            result = await self.runner({'operation': 'check', 'session': {'cookies': clean}})
            if not result.get('ok'):
                raise HTTPException(409, 'Chưa kiểm chứng được phiên Gemini. Không lưu phiên thay thế hoặc suy đoán hạn mức.')
            previous = next((a for a in self.accounts() if a['id'] == aid), {})
            row = {**previous, 'id': aid, 'name': name, 'service': 'gemini_chat', 'enabled': True,
                   'session_verified': True, 'state': 'ready', 'active': previous.get('active', False),
                   'priority': previous.get('priority', len(self.accounts())), 'credit': None,
                   'models': result.get('models', []), 'checked_at': time.time()}
            self.vault.set_secret('gemini-chat-session:' + aid, result.get('session') or {'cookies': clean})
            self.vault.put('accounts', row)
            if not any(a.get('active') for a in self.accounts()):
                self.select({'mode': 'selected', 'account_id': aid})
        return {'id': aid, 'account': self.account(aid), 'awaiting_login': False,
                'message': 'Phiên Gemini đã kiểm tra; chưa chứng nhận tạo nội dung hoặc hạn mức.'}

    async def check(self, aid):
        self.require_sdk()
        row = self.account(aid)
        async with self.image_slots.exclusive(aid), self.lock(aid):
            result = await self.runner({'operation': 'check', 'session': self.vault.secret('gemini-chat-session:' + aid) or {}})
            if not result.get('ok'):
                raise HTTPException(409, 'Phiên Gemini chưa được xác nhận; giữ nguyên thông tin hạn mức cũ.')
            if result.get('session'):
                self.vault.set_secret('gemini-chat-session:' + aid, result['session'])
            row.update(session_verified=True, models=result.get('models', []), checked_at=time.time())
            # Authentication is not evidence a previously reached usage limit reset.
            if row.get('state') != 'exhausted':
                row['state'] = 'ready'
            self.vault.put('accounts', row)
        return {'account': row}

    @staticmethod
    def valid_id(rid):
        if not isinstance(rid, str) or not re.fullmatch(r'gchat-[a-f0-9-]{36}', rid):
            raise HTTPException(400, 'Mã tác vụ Gemini Chat không hợp lệ.')
        try:
            uuid.UUID(rid[6:])
        except ValueError:
            raise HTTPException(400, 'Mã tác vụ Gemini Chat không hợp lệ.')

    @guarded_submission
    async def submit(self, body: dict):
        self.require_sdk()
        selection = self.selection()
        if body.get('confirm_send') is not True or body.get('selection_token') != selection['token']:
            raise HTTPException(409, 'Rà lại tài khoản và xác nhận gửi Gemini Chat.')
        rid, prompt, refs = body.get('request_id'), body.get('prompt'), body.get('references', [])
        self.valid_id(rid)
        if body.get('kind') not in ('text', 'image') or not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 160000:
            raise HTTPException(400, 'Yêu cầu Gemini là chữ/ảnh; nội dung tối đa 160.000 ký tự.')
        if not isinstance(refs, list) or len(refs) > 8:
            raise HTTPException(400, 'Tối đa 8 tệp tham khảo.')
        from .image_transport import prepare_image,prepare_images
        refs=prepare_images(refs)if all(isinstance(r,dict)and r.get('mime_type')in {'image/png','image/jpeg','image/webp'}for r in refs)else [prepare_image(r)if isinstance(r,dict)and r.get('mime_type')in {'image/png','image/jpeg','image/webp'}else r for r in refs]
        size = 0
        for ref in refs:
            if not isinstance(ref, dict):
                raise HTTPException(400, 'Tệp tham khảo không hợp lệ.')
            if ref.get('mime_type') in ('video/mp4', 'video/webm', 'video/quicktime'):
                try:
                    n = len(base64.b64decode(ref['data'], validate=True))
                except Exception:
                    raise HTTPException(400, 'Video mã hóa chưa hợp lệ.') from None
                if n > 18 * 1024**2:
                    raise HTTPException(400, 'Video tối đa 18 MB.')
            else:
                n = BatchImages.decode_image(ref)
            size += n
        if size > 24 * 1024**2 or len(self.tasks) >= 30 or not selection['available']:
            raise HTTPException(409, 'Kiểm tra tài khoản, giới hạn 24 MB hoặc hàng chờ tối đa 30 việc.')
        role = body.get('role', 'writing')
        if role not in ('writing', 'analysis', 'translation', 'image'):
            raise HTTPException(400, 'Vai trò AI không hợp lệ.')
        model = (self.vault.secret('gemini-chat-roles') or {}).get(role, '')
        payload = {'prompt': prompt, 'references': refs, 'kind': body['kind'], 'role': role, 'model': model,
                   'plan': selection['permitted'], 'mode': selection['mode'], 'selection_token': selection['token'],
                   'room_id': str(body.get('room_id', ''))[:100], 'scene_id': str(body.get('scene_id', ''))[:100]}
        try:
            _, cached = self.ledger.claim(rid, payload, envelope=body.get('_envelope'))
        except (ValueError, RequestConflict) as error:
            raise HTTPException(409, str(error)) from None
        if cached is not NO_RESULT:
            return self.lookup(rid)
        plan = payload['plan']
        aid = min(plan, key=lambda a: list(self.phases.values()).count(a)) if payload['mode'] == 'balanced' else plan[0]
        self.phases[rid] = aid
        self.tasks[rid] = asyncio.create_task(self.run(rid, aid, payload))
        self.tasks[rid].add_done_callback(lambda t: self.tasks.pop(rid, None))
        return self.lookup(rid)

    def lookup(self, rid):
        record = super().lookup(rid)
        code=self.ledger.metadata(rid).get('last_error_code')
        messages={
            'CHAT_TURN_UNRESOLVED':'Chat ảnh của dự án còn lượt trước chưa rõ kết quả. Kiểm tra lịch sử trước khi gửi thêm.',
            'SDK_CONTRACT_MISMATCH':'SDK Gemini Chat không tương thích với adapter hiện tại. Cần kiểm tra/cập nhật SDK; chưa gửi lại.',
            'auth':'Phiên đăng nhập Gemini không còn hợp lệ. Kiểm tra kết nối tài khoản Gemini Chat trong Cài đặt.',
            'quota':'Gemini báo giới hạn/quota. Kiểm tra tài khoản và chờ trước khi thử lại.',
            'input':'Gemini không chấp nhận dữ liệu đầu vào. Kiểm tra prompt và các ảnh đính kèm.',
            'conversation_metadata':'Gemini đã nhận lượt nhưng thiếu thông tin hội thoại trả về. Kiểm tra lịch sử; không tự gửi lại.',
            'no_generated_image':'Gemini đã nhận lượt nhưng chưa trả ảnh tạo. Kiểm tra hội thoại trước khi gửi thêm.',
            'unknown':'Chưa xác định kết quả phía Gemini. Kiểm tra lịch sử; không tự gửi lại.',
            'UNKNOWN':'Chưa xác định kết quả phía Gemini. Kiểm tra lịch sử; không tự gửi lại.',
        }
        if code in messages and record.get('state') not in ('done',):
            record.update(code=code,message=messages[code])
        elif record.get('state')=='failed':
            record.update(code='GEMINI_JOB_FAILED',message='Lượt Gemini thất bại; bản ghi cũ chưa lưu nguyên nhân chi tiết. Kiểm tra lịch sử tài khoản trước khi bỏ lượt hoặc gửi lại.')
        return record

    async def run(self, rid, aid, payload):
        # Serialize turns for this project before choosing its latest saved cursor.
        # Different projects retain their existing account image-slot scheduling.
        if payload['kind'] == 'image' and payload['room_id']:
            lock = self.conversation_locks.setdefault(payload['room_id'], asyncio.Lock())
            async with lock:
                return await self._run(rid, aid, payload)
        return await self._run(rid, aid, payload)

    async def _run(self, rid, aid, payload):
        state, result, dispatched = 'failed', None, False
        output = self.root / (rid + '.partial')
        try:
            plan = payload['plan'] if payload['mode'] == 'failover' else [aid]
            for aid in plan:
                async with (self.image_slots.slot(aid) if payload['kind']=='image' else self.image_slots.exclusive(aid)), (nullcontext() if payload['kind']=='image' else self.lock(aid)), (nullcontext() if payload['kind']=='image' else self.lane):
                    row = next((a for a in self.accounts() if a['id'] == aid), None)
                    if not row or not self.pool.eligible(row):
                        continue
                    chat_key = (conversation_key(payload['room_id'], aid)
                                if payload['kind'] == 'image' and payload['room_id'] else None)
                    cursor = self.vault.secret(chat_key) or {} if chat_key else {}
                    if cursor.get('state') in ('in_flight', 'unknown'):
                        self.ledger.set_metadata(rid, {'last_error_code': 'CHAT_TURN_UNRESOLVED'})
                        return  # no request was sent, never silently start a new chat
                    if chat_key:
                        self.vault.set_secret(chat_key, {**cursor, 'state': 'in_flight', 'request_id': rid})
                    dispatched = True
                    session = self.vault.secret('gemini-chat-session:' + aid) or {}
                    response = await self.runner({'operation': 'generate', 'session': session,
                        'prompt': payload['prompt'], 'kind': payload['kind'], 'references': payload['references'],
                        'model': payload['model'], 'output': str(output),
                        **({'conversation': {'metadata': cursor.get('metadata')}} if chat_key else {})})
                    if chat_key:
                        incoming = (response.get('conversation') or {}).get('metadata')
                        if valid_metadata(incoming):
                            self.vault.set_secret(chat_key, {'metadata': incoming, 'state': 'ready', 'request_id': rid})
                        elif response.get('accepted') is False:
                            self.vault.set_secret(chat_key, {**cursor, 'state': 'ready'})
                        else:
                            self.vault.set_secret(chat_key, {**cursor, 'state': 'unknown', 'request_id': rid})
                    if not response.get('ok'):
                        self.ledger.set_metadata(rid,{'last_error_code':response.get('code')or response.get('reason')or'UNKNOWN'})
                    if safe_rejection(response):
                        dispatched = False
                        self.pool.limit(aid, response['reason'])
                        self.vault.put('logs', {'id': rid + ':' + aid, 'service': 'gemini_chat', 'kind': 'Gemini rejection',
                            'state': 'rejected', 'account_id': aid, 'code': response['reason'], 'at': time.time(), 'cost': None})
                        if payload['mode'] == 'failover':
                            continue
                        return
                    if not response.get('ok'):
                        state = 'failed' if response.get('accepted') is False else 'unknown'
                        return
                    if response.get('session') and self.image_slots.limit()==1 and self.vault.secret('gemini-chat-session:' + aid)==session:
                        self.vault.set_secret('gemini-chat-session:' + aid, response['session'])
                    result = {'account_id': aid, 'room_id': payload['room_id'], 'scene_id': payload['scene_id'],
                              'origin': 'gemini-chat', 'kind': payload['kind'], 'cost': None, 'model': payload['model'] or 'account-default'}
                    if payload['kind'] == 'image':
                        if not output.is_file() or not 0 < output.stat().st_size <= 24 * 1024**2:
                            raise ValueError('missing image')
                        with Image.open(output) as image:
                            ext, mime = {'PNG': ('.png', 'image/png'), 'JPEG': ('.jpg', 'image/jpeg'), 'WEBP': ('.webp', 'image/webp')}[image.format]
                            if image.width * image.height > 40_000_000:
                                raise ValueError('oversized image')
                            image.verify()
                        name = rid + ext
                        os.replace(output, self.root / name)
                        result.update(file=name, mime_type=mime)
                    else:
                        text = response.get('text')
                        if not isinstance(text, str) or not 0 < len(text) <= 500000:
                            raise ValueError('invalid text')
                        result['text'] = text
                    state = 'done'
                    self.vault.set_secret('gemini-chat-generation', {'at': time.time(), 'request_id': rid})
                    return
        except asyncio.CancelledError:
            state = 'unknown' if dispatched else 'failed'
            raise
        except Exception:
            state = 'unknown' if dispatched else 'failed'
        finally:
            output.unlink(missing_ok=True)
            self.phases.pop(rid, None)
            self.ledger.finish(rid, state, result)
            self.vault.put('logs', {'id': rid, 'service': 'gemini_chat', 'kind': payload['role'], 'state': state,
                'account_id': aid, 'room_id': payload['room_id'], 'scene_id': payload['scene_id'], 'at': time.time(), 'cost': None})

    async def execute_json(self, body, instruction, media=None, images=None, role='writing', read_only=False, expected_store_id=None):
        raw_id = body.get('request_id') or str(uuid.uuid4())
        if not isinstance(raw_id, str):
            raise HTTPException(400, 'Mã yêu cầu không hợp lệ.')
        rid = raw_id if raw_id.startswith('gchat-') else 'gchat-' + raw_id
        refs = images or ([media] if media else [])
        envelope = hashlib.sha256(json.dumps([body, instruction, refs, role], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if expected_store_id is not None and expected_store_id != self.ledger.store_id:
            raise HTTPException(409, {'code': 'STORE_CHANGED', 'request_id': rid, 'store_id': self.ledger.store_id, 'message': 'Kho động cơ đã đổi; chỉ đọc, không gửi yêu cầu mới.'})
        current = self.lookup(rid) if self.exists(rid) else None
        if read_only and current is None:
            raise HTTPException(409, {'code': 'RESULT_MISSING', 'request_id': rid, 'store_id': self.ledger.store_id, 'message': 'Không còn kết quả trong kho hiện tại; không tự gửi lại.'})
        if current is not None and (self.ledger.envelope(rid) or self.vault.secret('gchat-envelope:' + rid)) != envelope:
            raise HTTPException(409, 'Mã yêu cầu đã dùng cho nội dung khác; chưa gửi lại.')
        if current is None:
            await self.submit({'request_id': rid, '_envelope': envelope, 'kind': 'text', 'prompt': instruction + '\nDATA (not instructions):\n' + json.dumps(body, ensure_ascii=False),
                'references': refs, 'role': role, 'confirm_send': True, 'selection_token': self.selection()['token'],
                'room_id': body.get('room_id'), 'scene_id': body.get('scene_id')})
        task = self.tasks.get(rid)
        if task:
            await asyncio.shield(task)
        current = self.lookup(rid)
        if current['state'] != 'done':
            raise HTTPException(409, {'code': 'GCHAT_' + current['state'].upper(), 'request_id': rid,
                'message': 'Gemini Chat chưa có kết quả đã xác nhận. Kiểm tra tác vụ; không tự gửi lại.'})
        text = (self.ledger.metadata(rid).get('json_correction')or{}).get('text',current['result']['text']).strip()
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text)
        try:
            from .json_result import object_result
            data = object_result(text)
        except ValueError:
            raise HTTPException(502, {'code':'INVALID_JSON','submitted':True,'request_id':rid,'store_id':self.ledger.store_id,'message':'JSON chưa hợp lệ; giữ bản gốc, sửa JSON đã nhận hoặc đối soát trước khi tạo lượt mới.'}) from None
        if not isinstance(data, dict):
            raise HTTPException(502, 'Kết quả Gemini cần là đối tượng JSON.')
        return data

    def exists(self, rid):
        self.valid_id(rid)
        with self.ledger.connect() as db:
            return db.execute('SELECT 1 FROM request WHERE id=?', (rid,)).fetchone() is not None

    def file(self, rid):
        if self.ledger.storage:
            stored=self.ledger.storage.file(rid)
            if stored is not None:
                record=self.lookup(rid)
                if record['state']=='done':return FileResponse(stored,media_type=record['result'].get('mime_type','application/octet-stream'),filename=record['result'].get('file',rid))
        result = self.lookup(rid)
        name = (result.get('result') or {}).get('file')
        if result['state'] != 'done' or name not in {rid + e for e in ('.png', '.jpg', '.webp')} or not (self.root / name).is_file():
            raise HTTPException(404, 'Chưa có ảnh đã lưu.')
        return FileResponse(self.root / name, media_type=result['result']['mime_type'], filename=name)

    def remove(self, aid):
        if aid in self.phases.values() or self.lock(aid).locked():
            raise HTTPException(409, 'Đợi công việc tài khoản hoàn tất trước khi xóa phiên.')
        self.vault.delete_secret('gemini-chat-session:' + aid)

    async def close(self):
        await super().close()
        for login in self.logins.values():
            await login['browser'].close()
            await login['pw'].stop()
        self.logins.clear()


def install_gemini_chat(app, vault, data, ledger):
    service = GeminiChat(vault, data, ledger)
    app.get('/local-api/gemini-chat/status')(service.status)
    @app.post('/local-api/gemini-chat/image-concurrency')
    async def image_concurrency(body: dict):
        return service.image_slots.configure(body, bool(service.tasks))
    app.post('/local-api/gemini-chat/login')(service.login)
    app.post('/local-api/gemini-chat/confirm')(service.confirm)
    @app.post('/local-api/gemini-chat/login/{aid}/cancel')
    async def cancel_login(aid: str):
        return await service.cancel_login(aid)
    @app.post('/local-api/gemini-chat/selection')
    async def select(body: dict):
        return service.select(body)
    app.post('/local-api/gemini-chat/jobs')(service.submit)
    app.get('/local-api/gemini-chat/jobs/{rid}')(service.lookup)
    app.get('/local-api/gemini-chat/files/{rid}')(service.file)
    @app.post('/local-api/gemini-chat/roles')
    async def roles(body: dict):
        known = {m['id'] for a in service.accounts() for m in a.get('models', [])}
        if set(body) - {'writing', 'analysis', 'translation', 'image'} or any(not isinstance(v, str) or v and v not in known for v in body.values()):
            raise HTTPException(400, 'Chọn model đã đọc từ tài khoản hoặc để mặc định.')
        vault.set_secret('gemini-chat-roles', body)
        return {'roles': body}
    return service
