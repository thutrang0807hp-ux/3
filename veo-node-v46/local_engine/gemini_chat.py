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
        self.login_tasks = {}
        self.login_results = {}
        self.login_locks = {}
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
        return {'installed': self.engine().is_file() or any(a.get('transport')=='browser' for a in self.accounts()), 'configured': selection['available'], 'adapter': True,
                'selection': selection, 'accounts': self.accounts(), 'per_account': 1, 'max_concurrency': 3, **self.image_slots.status(),
                'generation_verified': bool(self.vault.secret('gemini-chat-generation')), 'automatic_retry': False,
                'web_login': self.web_login_status(), 'roles': self.vault.secret('gemini-chat-roles') or {}, 'service_url': 'https://gemini.google.com/'}

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
            from .browser_profiles import profiles
            ident=body.get('account_id')
            if ident and (self.lock(ident).locked()or ident in self.phases.values()):raise HTTPException(409,'Đợi tác vụ tài khoản xong trước khi mở lại profile.')
            manager=profiles(self.vault,self.data);entry=manager.reserve('gemini_chat',ident)
            from .browser_profiles import saved_cookies
            prior=self.vault.secret('gemini-chat-session:'+str(body.get('account_id')))or{}
            login = await manager.native(entry,'https://gemini.google.com/',saved_cookies(prior,'gemini_chat'))
            browser = context = pw = login
            aid = 'gchat-account-' + uuid.uuid4().hex
            self.logins[aid] = {'name': name.strip(), 'browser': browser, 'context': context, 'pw': pw,'profile_entry':entry}
            self.login_results[aid]={'id':aid,'state':'waiting','message':'Đăng nhập Gemini rồi đóng cửa sổ đó; app vẫn nhận phiên khi bạn quay lại bảng tài khoản.'}
            self.login_locks[aid]=asyncio.Lock()
            self.login_tasks[aid]=asyncio.create_task(self.watch_login(aid))
            return {'id': aid, 'awaiting_login': True}
        return await self.import_session(name.strip(), supplied)

    def web_login_status(self):
        return list(self.login_results.values())[-5:]

    async def watch_login(self, aid):
        try:
            while aid in self.logins:
                context=self.logins[aid]['context']
                process=getattr(context,'process',None)
                if getattr(context,'deferred_capture',False) and process is not None and process.poll() is not None:
                    await self.confirm({'id':aid})
                    return
                await asyncio.sleep(1)
        except asyncio.CancelledError:raise
        except Exception as exc:
            self.login_results[aid]={'id':aid,'state':'failed','message':str(exc.detail) if isinstance(exc,HTTPException) else 'Chưa kiểm chứng được phiên Gemini; dữ liệu đăng nhập vẫn giữ để thử nhận lại.'}

    async def login_status(self, aid):
        if aid not in self.login_results:
            raise HTTPException(409,'Lượt đăng nhập không còn; mở lại Đăng nhập trên web.')
        return self.login_results[aid]

    async def finish_login(self, body: dict):
        aid=body.get('id');login=self.logins.get(aid)
        if not login:
            result=self.login_results.get(aid,{})
            if result.get('state')=='done':return result['result']
            raise HTTPException(409,'Lượt đăng nhập không còn; mở lại Đăng nhập trên web.')
        try:
            await login['context'].finish_signin()
            return await self.confirm({'id':aid})
        except Exception as exc:
            self.login_results[aid]={'id':aid,'state':'failed','message':str(exc.detail) if isinstance(exc,HTTPException) else 'Không hoàn tất được bước nhận tài khoản Gemini; phiên vẫn được giữ để thử lại.'}
            raise

    async def confirm(self, body: dict):
        aid=body.get('id')
        if aid not in self.login_locks:raise HTTPException(409,'Lượt đăng nhập không còn.')
        async with self.login_locks[aid]:
            previous=self.login_results.get(aid,{})
            if previous.get('state')=='done':return previous['result']
            login=self.logins.get(aid)
            if not login:raise HTTPException(409,'Lượt đăng nhập không còn.')
            self.login_results[aid]={'id':aid,'state':'checking','message':'Đang nhận và kiểm chứng phiên Gemini…'}
            try:
                cookies=await login['context'].cookies()
                result=await self.import_session(login['name'],cookies)
                if login.get('profile_entry'):
                    from .browser_profiles import profiles
                    profiles(self.vault,self.data).bind(login['profile_entry'],result['id'])
                await self.cancel_login(aid,completed=True)
                self.login_results[aid]={'id':aid,'state':'done','message':'Đã kiểm chứng và lưu phiên Gemini.','result':result}
                return result
            except Exception as exc:
                self.login_results[aid]={'id':aid,'state':'failed','message':str(exc.detail) if isinstance(exc,HTTPException) else 'Chưa kiểm chứng được phiên Gemini; có thể thử nhận lại.'}
                raise

    async def cancel_login(self, aid, completed=False):
        task=self.login_tasks.pop(aid,None)
        if task and task is not asyncio.current_task() and not task.done():
            task.cancel()
            try:await task
            except asyncio.CancelledError:pass
        if not completed:self.login_results.pop(aid,None)
        login = self.logins.pop(aid, None)
        if login:
            await login['browser'].close()
            await login['pw'].stop()
            if login.get('profile_entry'):
                from .browser_profiles import profiles
                await profiles(self.vault,self.data).discard(login['profile_entry'])
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
            self.require_sdk()
            try:
                result = await self.runner({'operation': 'check', 'session': {'cookies': clean}})
            except (asyncio.TimeoutError, TimeoutError):
                raise HTTPException(504, {'code':'GEMINI_SESSION_CHECK_TIMEOUT','message':'Đã chuyển phiên nhưng kiểm tra Gemini quá thời gian; tài khoản chưa được lưu.'}) from None
            except (FileNotFoundError, OSError):
                raise HTTPException(503, {'code':'GEMINI_SDK_UNAVAILABLE','message':'Đã chuyển phiên nhưng bộ chạy Gemini trên máy chưa khởi động được.'}) from None
            if not result.get('ok'):
                reason = result.get('reason')
                message = 'Cookie đã chuyển nhưng Gemini không chấp nhận phiên đăng nhập này.' if reason == 'auth' else 'Bộ chạy Gemini không tương thích; chưa thể kiểm tra và lưu tài khoản.' if reason == 'sdk_incompatible' else 'Đã chuyển phiên nhưng bộ chạy chưa xác minh được tài khoản Gemini.'
                code = 'GEMINI_SESSION_AUTH_REJECTED' if reason == 'auth' else 'GEMINI_SDK_INCOMPATIBLE' if reason == 'sdk_incompatible' else 'GEMINI_SESSION_CHECK_FAILED'
                messages = {
                    'GEMINI_SESSION_COOKIE_MISSING':'Tiện ích chưa cung cấp cookie đăng nhập bắt buộc cho bộ chạy Gemini.',
                    'GEMINI_SESSION_GUEST':'SDK khởi tạo thành phiên khách thay vì tài khoản đã đăng nhập; chưa lưu tài khoản.',
                    'GEMINI_SESSION_TOKEN_MISSING':'SDK mở được phiên nhưng chưa đọc được token đăng nhập Gemini; chưa lưu tài khoản.',
                    'GEMINI_ACCOUNT_UNAVAILABLE':'SDK có token đăng nhập nhưng báo tài khoản chưa sẵn sàng; đây không phải kết luận cookie bị từ chối.',
                    'GEMINI_SESSION_INIT_FAILED':'SDK không khởi tạo được phiên từ cookie đã chuyển. Chưa xác định do cookie, SDK hay phản hồi Google.',
                    'GEMINI_SESSION_AUTH_ERROR':'SDK báo lỗi xác thực sau khi khởi tạo phiên; chưa lưu tài khoản.'}
                if result.get('code') in messages:
                    code=result['code'];message=messages[code]
                    status=result.get('account_status')
                    if code=='GEMINI_ACCOUNT_UNAVAILABLE' and isinstance(status,str) and re.fullmatch(r'[A-Z_]{1,60}',status):
                        message+=' Trạng thái SDK: '+status+'.'
                raise HTTPException(409, {'code':code,'message':message})
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
        row = self.account(aid)
        if row.get('transport')=='browser':
            if not self.browser.available(row['browser_route']):raise HTTPException(409,'Tiện ích Gemini chưa online. Mở trình duyệt đã kết nối.')
            return {'account':row}
        self.require_sdk()
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
        selection = self.selection()
        if body.get('image_engine')=='studio-v1' and (not selection.get('permitted')or any(self.account(a).get('transport')!='browser'for a in selection['permitted'])):raise HTTPException(409,'Node ảnh khung mới cần kết nối Gemini qua trình duyệt đang được chọn; đợi tiện ích tự kết nối.')
        if not selection.get('permitted') or any(self.account(a).get('transport')!='browser' for a in selection['permitted']):self.require_sdk()
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
        if size > 24 * 1024**2:
            raise HTTPException(413, 'Tổng tệp tham khảo vượt 24 MB. Chưa gửi yêu cầu tới Gemini; giảm dung lượng trước khi viết lại.')
        if len(self.tasks) >= 30:
            raise HTTPException(409, 'Hàng chờ Gemini đã đủ 30 việc. Chưa gửi yêu cầu này; chờ việc đang chạy hoàn tất.')
        if not selection['available']:
            raise HTTPException(409, 'Chưa có tài khoản Gemini Chat đã kiểm chứng và được chọn để chạy. Chưa gửi yêu cầu viết lại. Vào Cài đặt → Tài khoản → Gemini Chat, nhận/kiểm tra phiên rồi chọn Dùng.')
        role = body.get('role', 'writing')
        if role not in ('writing', 'analysis', 'translation', 'image'):
            raise HTTPException(400, 'Vai trò AI không hợp lệ.')
        model = (self.vault.secret('gemini-chat-roles') or {}).get(role, '')
        payload = {'prompt': prompt, 'references': refs, 'kind': body['kind'], 'role': role, 'model': model,
                   'plan': selection['permitted'], 'mode': selection['mode'], 'selection_token': selection['token'],
                   'room_id': str(body.get('room_id', ''))[:100], 'scene_id': str(body.get('scene_id', ''))[:100]}
        if body.get('image_engine')=='studio-v1' and body['kind']=='image':
            payload['image_engine']='studio-v1'
            ratio=body.get('ratio','9:16')
            if not isinstance(ratio,str) or not re.fullmatch(r'[1-9][0-9]{0,3}:[1-9][0-9]{0,3}',ratio):raise HTTPException(400,'Tỉ lệ ảnh không hợp lệ.')
            payload['ratio']=ratio
        scope = body.get('conversation_scope')
        if scope is not None:
            if body['kind'] != 'image' or not isinstance(scope, str) or not re.fullmatch(r'[a-f0-9-]{36}', scope):
                raise HTTPException(400, 'Phạm vi hội thoại ảnh không hợp lệ.')
            try:
                uuid.UUID(scope)
            except ValueError:
                raise HTTPException(400, 'Phạm vi hội thoại ảnh không hợp lệ.') from None
            payload['conversation_scope'] = scope
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
        self.tasks[rid].add_done_callback(lambda t: self.tasks.pop(rid, None) if self.tasks.get(rid) is t else None)
        return self.lookup(rid)

    def lookup(self, rid):
        record = super().lookup(rid)
        code=self.ledger.metadata(rid).get('last_error_code')
        messages={
            'GEMINI_BROWSER_OFFLINE':'Tiện ích Gemini chưa online; chưa gửi prompt. Mở trình duyệt đã kết nối.',
            'GEMINI_BROWSER_OUTCOME_UNKNOWN':'Đã gửi qua trình duyệt nhưng chưa nhận kết quả; kiểm tra tab Gemini, không tự gửi lại.',
            'GEMINI_BROWSER_TRANSFER_FAILED':'Gemini đã tạo ảnh; cần nhận lại ảnh từ tab cũ, không tạo mới.',
            'GEMINI_BROWSER_ATTACH_FAILED':'Chưa tải đủ ảnh tham khảo vào Gemini; chưa gửi prompt. Kiểm tra tab của lượt này.',
            'GEMINI_BROWSER_SEND_CONTROL_MISSING':'Chưa tìm được nút gửi Gemini khả dụng; chưa gửi prompt.',
            'GEMINI_BROWSER_TEXT_TIMEOUT':'Đã gửi prompt nhưng chưa đọc được văn bản hoàn tất trong tab Gemini; không tự gửi lại.',
            'GEMINI_BROWSER_IMAGE_TIMEOUT':'Đã gửi prompt nhưng chưa đọc được ảnh trong tab Gemini; giữ tab mở và nhận lại kết quả cũ, không tự gửi lại.',
            'GEMINI_BROWSER_FAILED':'Gemini chưa trả kết quả qua trình duyệt. Xem tab Gemini của lượt này.',
            'CHAT_TURN_UNRESOLVED':'Chat ảnh của dự án còn lượt trước chưa rõ kết quả. Kiểm tra lịch sử trước khi gửi thêm.',
            'SDK_CONTRACT_MISMATCH':'SDK Gemini Chat không tương thích với adapter hiện tại. Cần kiểm tra/cập nhật SDK; chưa gửi lại.',
            'auth':'Phiên đăng nhập Gemini không còn hợp lệ. Kiểm tra kết nối tài khoản Gemini Chat trong Cài đặt.',
            'quota':'Gemini báo giới hạn/quota. Kiểm tra tài khoản và chờ trước khi thử lại.',
            'input':'Gemini không chấp nhận dữ liệu đầu vào. Kiểm tra prompt và các ảnh đính kèm.',
            'conversation_metadata':'Gemini đã nhận lượt nhưng thiếu thông tin hội thoại trả về. Kiểm tra lịch sử; không tự gửi lại.',
            'no_generated_image':'Gemini đã nhận lượt nhưng chưa trả ảnh tạo. Kiểm tra hội thoại trước khi gửi thêm.',
            'unknown':'Chưa xác định kết quả phía Gemini. Kiểm tra lịch sử; không tự gửi lại.',
            'UNKNOWN':'Chưa xác định kết quả phía Gemini. Kiểm tra lịch sử; không tự gửi lại.',
            'GEMINI_INIT_ERROR':'Lỗi khởi tạo kết nối/phiên Gemini; chưa tới bước tạo ảnh.',
            'GEMINI_ATTACHMENT_ERROR':'Lỗi chuẩn bị tệp tham khảo trước khi gửi tạo ảnh.',
            'GEMINI_UPLOAD_ERROR':'Lỗi tải ảnh tham khảo hoặc chuẩn bị yêu cầu; chưa bắt đầu tạo ảnh.',
            'GEMINI_GENERATE_ERROR':'Lỗi khi gửi/đọc phản hồi tạo nội dung Gemini; chưa xác định kết quả, không tự gửi lại.',
            'GEMINI_IMAGE_DOWNLOAD_ERROR':'Gemini đã trả ảnh nhưng tải tệp kết quả thất bại; tránh tạo lại vì có thể dùng thêm hạn mức.',
            'GEMINI_RESULT_ERROR':'Đã nhận phản hồi Gemini nhưng xử lý kết quả thất bại.',
            'GEMINI_WORKER_ERROR':'Lỗi ở tiến trình gọi Gemini. Cần xem loại lỗi kỹ thuật bên dưới.',
            'GEMINI_ADAPTER_ERROR':'Lỗi gọi tiến trình Gemini hoặc kiểm tra tệp trả về; chưa đủ bằng chứng xác định kết quả.',
        }
        if code in messages and record.get('state') not in ('done',):
            record.update(code=code,message=messages[code])
            metadata = self.ledger.metadata(rid) if hasattr(self.ledger, 'metadata') else {}
            metadata = metadata or {}
            kind = metadata.get('error_type')
            status = metadata.get('http_status')
            if isinstance(kind, str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}', kind):
                record['message'] += ' Loại lỗi: ' + kind + '.'
            if isinstance(status, int) and not isinstance(status, bool) and 100 <= status <= 599:
                record['message'] += ' HTTP ' + str(status) + '.'
        elif record.get('state')=='failed':
            record.update(code='GEMINI_JOB_FAILED',message='Lượt Gemini thất bại; bản ghi cũ chưa lưu nguyên nhân chi tiết. Kiểm tra lịch sử tài khoản trước khi bỏ lượt hoặc gửi lại.')
        metadata = self.ledger.metadata(rid)
        if metadata.get('browser_request'):
            record['transport']='browser'
        if (metadata.get('browser_request') and record.get('state') in ('unknown','failed')) or metadata.get('last_error_code') == 'GEMINI_IMAGE_DOWNLOAD_ERROR' or metadata.get('image_result_available'):
            record['can_receive_image'] = record.get('state') != 'done'
        if metadata.get('receive_active') and rid in self.tasks and record.get('state') != 'done':
            record.update(state='downloading', phase='receiving_existing_image')
        return record

    @staticmethod
    def conversation_room(payload):
        room, scope = payload.get('room_id', ''), payload.get('conversation_scope')
        if not scope:
            return room
        return 'scoped:' + hashlib.sha256(json.dumps([room, scope]).encode()).hexdigest()

    async def run(self, rid, aid, payload):
        # Serialize turns for this project before choosing its latest saved cursor.
        # Different projects retain their existing account image-slot scheduling.
        if payload['kind'] == 'image' and payload['room_id']:
            lock = self.conversation_locks.setdefault(self.conversation_room(payload), asyncio.Lock())
            async with lock:
                return await self._run(rid, aid, payload)
        return await self._run(rid, aid, payload)

    async def _run(self, rid, aid, payload):
        state, result, dispatched = 'failed', None, False
        output = self.root / (rid + '.partial')
        try:
            plan = payload['plan'] if payload['mode'] == 'failover' else [aid]
            for aid in plan:
                async with (self.image_slots.slot(aid) if payload['kind']=='image' else self.image_slots.exclusive(aid)), (self.lock(aid) if self.account(aid).get('transport')=='browser' or payload['kind']!='image' else nullcontext()), (nullcontext() if payload['kind']=='image' else self.lane):
                    row = next((a for a in self.accounts() if a['id'] == aid), None)
                    if not row or not self.pool.eligible(row):
                        continue
                    chat_key = (conversation_key(self.conversation_room(payload), aid)
                                if payload['kind'] == 'image' and payload['room_id'] and row.get('transport')!='browser' else None)
                    cursor = self.vault.secret(chat_key) or {} if chat_key else {}
                    if cursor.get('state') in ('in_flight', 'unknown'):
                        self.ledger.set_metadata(rid, {'last_error_code': 'CHAT_TURN_UNRESOLVED'})
                        return  # no request was sent, never silently start a new chat
                    if chat_key:
                        self.vault.set_secret(chat_key, {**cursor, 'state': 'in_flight', 'request_id': rid})
                    dispatched = True
                    session = self.vault.secret('gemini-chat-session:' + aid) or {}
                    response = await (self.browser_generate(rid,aid,payload,output) if row.get('transport')=='browser' else self.runner({'operation': 'generate', 'session': session,
                        'prompt': payload['prompt'], 'kind': payload['kind'], 'references': payload['references'],
                        'model': payload['model'], 'output': str(output),
                        **({'conversation': {'metadata': cursor.get('metadata')}} if chat_key else {})}))
                    if chat_key:
                        incoming = (response.get('conversation') or {}).get('metadata')
                        if valid_metadata(incoming):
                            self.vault.set_secret(chat_key, {'metadata': incoming, 'state': 'ready', 'request_id': rid})
                        elif response.get('accepted') is False:
                            self.vault.set_secret(chat_key, {**cursor, 'state': 'ready'})
                        else:
                            self.vault.set_secret(chat_key, {**cursor, 'state': 'unknown', 'request_id': rid})
                    if response.get('image_result'):
                        self.vault.set_secret('gemini-image-result:' + rid, {'request_id':rid,'account_id':aid,'image_result':response['image_result']})
                        self.ledger.set_metadata(rid, {'account_id':aid,'image_result_available':True})
                    if not response.get('ok'):
                        self.ledger.set_metadata(rid,{'last_error_code':response.get('code')or response.get('reason')or'UNKNOWN',**{key:response.get(key) for key in ('phase','error_type','http_status')}})
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
                              'origin': 'gemini-chat', 'kind': payload['kind'], 'cost': None, 'model': 'browser-session' if row.get('transport')=='browser' else payload['model'] or 'account-default'}
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
                        result.update(file=name, mime_type=mime, width=image.width, height=image.height, download_variant=response.get('download_variant','full-size'))
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
        except Exception as error:
            self.ledger.set_metadata(rid, {'last_error_code': 'GEMINI_ADAPTER_ERROR', 'error_type': type(error).__name__[:80]})
            state = 'unknown' if dispatched else 'failed'
        finally:
            output.unlink(missing_ok=True)
            self.phases.pop(rid, None)
            if self.ledger.metadata(rid).get('browser_request'):self.ledger.set_metadata(rid,{'receive_active':False})
            self.ledger.finish(rid, state, result)
            if state=='done' and getattr(self,'browser',None) and self.ledger.metadata(rid).get('browser_request'):
                self.browser.retire(rid)
                receive_id=self.ledger.metadata(rid).get('browser_receive_job')
                if receive_id:self.browser.retire(receive_id)
            self.vault.put('logs', {'id': rid, 'service': 'gemini_chat', 'kind': payload['role'], 'state': state,
                'account_id': aid, 'room_id': payload['room_id'], 'scene_id': payload['scene_id'], 'at': time.time(), 'cost': None})

    async def browser_generate(self,rid,aid,payload,output):
        row=self.account(aid);route=row['browser_route']
        # A durable browser job ID may be received again but can never be re-dispatched.
        safe_payload={k:v for k,v in payload.items()if k not in {'prompt','references','browser_receive'}}
        self.ledger.set_metadata(rid,{'browser_request':True,'account_id':aid,'browser_payload':safe_payload})
        receive_id=None
        try:
            old=self.browser.read(rid)
            if payload.get('browser_receive') and (old is None or not old.get('ok')):
                receive_id='receive-'+uuid.uuid4().hex
                result=await self.browser.request(route,receive_id,{'operation':'receive','target_job':rid,'kind':payload['kind'],**({'engine':'frame-studio'}if payload.get('image_engine')=='studio-v1'else{})},240)
            else:
                result=await self.browser.request(route,rid,{'operation':'generate','prompt':payload.get('prompt',''),'kind':payload['kind'],'references':payload.get('references',[]),**({'ratio':payload['ratio']}if payload.get('image_engine')=='studio-v1' and payload.get('ratio')else{}),**({'engine':'frame-studio'}if payload.get('image_engine')=='studio-v1'else{})},240)
        except HTTPException as exc:
            detail=exc.detail if isinstance(exc.detail,dict)else {}
            if detail.get('sent')is False:self.ledger.set_metadata(rid,{'browser_request':False})
            return {'ok':False,'accepted':None if detail.get('sent',True)else False,'code':detail.get('code','GEMINI_BROWSER_OUTCOME_UNKNOWN')}
        if not result.get('ok'):
            if result.get('accepted')is False:self.ledger.set_metadata(rid,{'browser_request':False})
            code=result.get('code')
            if code not in {'GEMINI_BROWSER_TRANSFER_FAILED','GEMINI_BROWSER_OFFLINE','GEMINI_BROWSER_ATTACH_FAILED','GEMINI_BROWSER_SEND_CONTROL_MISSING','GEMINI_BROWSER_TEXT_TIMEOUT','GEMINI_BROWSER_IMAGE_TIMEOUT'}:code='GEMINI_BROWSER_FAILED'
            return {'ok':False,'accepted':result.get('accepted'),'code':code}
        if payload['kind']=='image':
            try:
                data=base64.b64decode(result.get('image',''),validate=True)
                if not 0<len(data)<=24*1024**2:raise ValueError()
                Path(output).write_bytes(data)
            except Exception:
                return {'ok':False,'accepted':True,'code':'GEMINI_BROWSER_TRANSFER_FAILED'}
            if receive_id:self.ledger.set_metadata(rid,{'browser_receive_job':receive_id})
            return {'ok':True,'download_variant':'browser-authenticated'}
        return {'ok':True,'text':result.get('text','')}

    async def receive_image(self, rid, body=None):
        self.valid_id(rid)
        record = self.lookup(rid)
        if record['state'] == 'done':
            return record
        task = self.tasks.get(rid)
        if task is not None:
            if record['state'] == 'unknown' and self.ledger.metadata(rid).get('image_result_available'):
                await asyncio.shield(task)
            elif not task.done():
                return record
            if self.tasks.get(rid) is task:
                self.tasks.pop(rid, None)
        meta = self.ledger.metadata(rid)
        if meta.get('browser_request'):
            aid=meta['account_id'];payload={**meta['browser_payload'],'browser_receive':True}
            self.ledger.set_metadata(rid,{'receive_active':True});self.phases[rid]=aid
            self.tasks[rid]=asyncio.create_task(self.run(rid,aid,payload))
            self.tasks[rid].add_done_callback(lambda task:self.tasks.pop(rid,None) if self.tasks.get(rid)is task else None)
            return self.lookup(rid)
        pointer = self.vault.secret('gemini-image-result:' + rid)
        # Legacy .151 errors retained a cursor but no per-request descriptor.
        # Accept it only if its exact request_id still matches this receipt.
        if not pointer:
            scope = (body or {}).get('conversation_scope')
            scopes = [None]
            if scope is not None:
                try:
                    if not isinstance(scope, str) or str(uuid.UUID(scope)) != scope:
                        raise ValueError()
                except (ValueError, AttributeError):
                    raise HTTPException(400, 'Phạm vi nhận lại ảnh không hợp lệ.') from None
                scopes.append(scope)
            for account in self.accounts():
                for candidate in scopes:
                    room = self.conversation_room({'room_id':meta.get('room_id',''),'conversation_scope':candidate})
                    cursor = self.vault.secret(conversation_key(room, account['id'])) or {}
                    if cursor.get('request_id') == rid and valid_metadata(cursor.get('metadata')):
                        pointer = {'request_id':rid,'account_id':account['id'],'image_result':{'metadata':cursor['metadata']}}
                        break
                if pointer:
                    break
        if not pointer or pointer.get('request_id') != rid:
            raise HTTPException(409, 'Không còn dấu ảnh chính xác của lượt cũ để nhận lại. Không tạo ảnh mới tự động.')
        self.require_sdk()
        aid = pointer['account_id']
        self.vault.set_secret('gemini-image-result:' + rid, pointer)
        self.ledger.set_metadata(rid, {'receive_active':True,'image_result_available':True,'account_id':aid})
        self.tasks[rid] = asyncio.create_task(self._receive_image(rid, pointer, meta))
        self.tasks[rid].add_done_callback(lambda task: self.tasks.pop(rid, None) if self.tasks.get(rid) is task else None)
        return self.lookup(rid)

    async def _receive_image(self, rid, pointer, meta):
        output = self.root / (rid + '.receive.partial')
        aid = pointer['account_id']
        try:
            async with self.image_slots.slot(aid):
                session = self.vault.secret('gemini-chat-session:' + aid) or {}
                response = await self.runner({'operation':'receive_image','kind':'image','session':session,
                    'image_result':pointer['image_result'],'output':str(output)})
                if response.get('image_result'):
                    pointer = {**pointer,'image_result':response['image_result']}
                    self.vault.set_secret('gemini-image-result:' + rid, pointer)
                if not response.get('ok'):
                    self.ledger.set_metadata(rid, {'last_error_code':response.get('code')or response.get('reason')or'UNKNOWN',
                        **{key:response.get(key) for key in ('phase','error_type','http_status')}})
                    return
                if not output.is_file() or not 0 < output.stat().st_size <= 24 * 1024**2:
                    raise ValueError('invalid recovered image size')
                with Image.open(output) as image:
                    ext,mime = {'PNG':('.png','image/png'),'JPEG':('.jpg','image/jpeg'),'WEBP':('.webp','image/webp')}[image.format]
                    width,height = image.size
                    if width * height > 40_000_000:
                        raise ValueError('oversized recovered image')
                    image.verify()
                name = rid + ext
                os.replace(output, self.root / name)
                self.ledger.finish(rid, 'done', {'file':name,'mime_type':mime,'account_id':aid,
                    'room_id':meta.get('room_id',''),'scene_id':meta.get('scene_id',''),'kind':'image','origin':'gemini-chat',
                    'cost':None,'model':meta.get('model',''),'width':width,'height':height,
                    'download_variant':response.get('download_variant','full-size'),'received_existing_image':True})
                if response.get('session') and self.image_slots.limit()==1 and self.vault.secret('gemini-chat-session:' + aid)==session:
                    self.vault.set_secret('gemini-chat-session:' + aid,response['session'])
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self.ledger.set_metadata(rid, {'last_error_code':'GEMINI_IMAGE_DOWNLOAD_ERROR','phase':'download_image','error_type':type(error).__name__[:80],'http_status':None})
        finally:
            output.unlink(missing_ok=True)
            self.ledger.set_metadata(rid, {'receive_active':False})

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
        row=self.account(aid)
        if row.get('transport')=='browser':self.browser.revoke(row['browser_route'])
        self.vault.delete_secret('gemini-chat-session:' + aid)

    async def close(self):
        await super().close()
        for ident in list(self.logins):
            await self.cancel_login(ident)


def install_gemini_chat(app, vault, data, ledger):
    service = GeminiChat(vault, data, ledger)
    app.get('/local-api/gemini-chat/status')(service.status)
    @app.post('/local-api/gemini-chat/image-concurrency')
    async def image_concurrency(body: dict):
        return service.image_slots.configure(body, bool(service.tasks))
    app.post('/local-api/gemini-chat/login')(service.login)
    app.post('/local-api/gemini-chat/confirm')(service.confirm)
    app.post('/local-api/gemini-chat/finish-login')(service.finish_login)
    app.get('/local-api/gemini-chat/login/{aid}/status')(service.login_status)
    @app.post('/local-api/gemini-chat/login/{aid}/cancel')
    async def cancel_login(aid: str):
        return await service.cancel_login(aid)
    @app.post('/local-api/gemini-chat/selection')
    async def select(body: dict):
        return service.select(body)
    app.post('/local-api/gemini-chat/jobs')(service.submit)
    app.get('/local-api/gemini-chat/jobs/{rid}')(service.lookup)
    @app.post('/local-api/gemini-chat/jobs/{rid}/receive')
    async def receive_image(rid: str, body: dict):
        return await service.receive_image(rid, body)
    app.get('/local-api/gemini-chat/files/{rid}')(service.file)
    @app.post('/local-api/gemini-chat/roles')
    async def roles(body: dict):
        known = {m['id'] for a in service.accounts() for m in a.get('models', [])}
        if set(body) - {'writing', 'analysis', 'translation', 'image'} or any(not isinstance(v, str) or v and v not in known for v in body.values()):
            raise HTTPException(400, 'Chọn model đã đọc từ tài khoản hoặc để mặc định.')
        vault.set_secret('gemini-chat-roles', body)
        return {'roles': body}
    return service
