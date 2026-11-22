"""User-issued, expiring pairing between the app and its installed extension.

Only the extension's two exchange paths bypass the normal app-cookie boundary.
Each exchange still needs a loopback host, exact extension Origin, protocol
header and a one-use code issued through an authenticated app action.
"""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import time

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from .flow_connection import error as flow_error, public_error as flow_public_error, diagnostics as flow_diagnostics

from .flow_browser_relay import BrowserRelay, PATHS as NATIVE_PATHS
EXCHANGE = {'/local-api/browser-bridge/claim', '/local-api/browser-bridge/complete'} | NATIVE_PATHS


class BrowserBridge:
    def __init__(self, app, gemini, flow):
        self.gemini, self.flow = gemini, flow
        self.root = Path(__file__).resolve().parents[1]/'scripts/browser-extension'
        manifest = json.loads((self.root/'manifest.json').read_text())
        digest = hashlib.sha256(base64.b64decode(manifest['key'])).hexdigest()[:32]
        self.extension_id = ''.join(chr(ord('a')+int(c,16)) for c in digest)
        self.origin = 'chrome-extension://'+self.extension_id
        self.relay=BrowserRelay(app,gemini.vault)
        flow.native_relay=self.relay
        self.pairs = {}
        self.tasks = set()
        self.bad_attempts = []
        self.install(app)

    async def extension_request(self, request, call_next):
        from urllib.parse import urlsplit
        try:
            authority = urlsplit('//'+request.headers.get('host',''));host = authority.hostname
            if authority.username or authority.password:host=None
        except ValueError:
            host = None
        origin = request.headers.get('origin')
        if host not in {'127.0.0.1','localhost','testserver'} or origin != self.origin:
            return JSONResponse({'detail':'Nguồn tiện ích không được phép.'},403)
        headers = {'Access-Control-Allow-Origin':self.origin, 'Vary':'Origin',
                   'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff'}
        if request.method == 'OPTIONS':
            requested = {h.strip().lower() for h in request.headers.get('access-control-request-headers','').split(',') if h.strip()}
            if request.headers.get('access-control-request-method') != 'POST' or not requested <= {'content-type','x-sceneforge-bridge'}:
                return JSONResponse({'detail':'Preflight không hợp lệ.'},403,headers=headers)
            headers.update({'Access-Control-Allow-Methods':'POST','Access-Control-Allow-Headers':'Content-Type, X-SceneForge-Bridge','Access-Control-Allow-Private-Network':'true'})
            return JSONResponse({'ok':True},headers=headers)
        if request.method != 'POST' or request.headers.get('x-sceneforge-bridge') != '1':
            return JSONResponse({'detail':'Yêu cầu tiện ích không hợp lệ.'},403,headers=headers)
        # Bound even a chunked request; never trust Content-Length alone.
        body = bytearray()
        async for part in request.stream():
            body.extend(part)
            if len(body)>(21*1024**2 if request.url.path in NATIVE_PATHS else 128*1024):
                return JSONResponse({'detail':'Phiên quá lớn; chưa nhận.'},413,headers=headers)
        request._body = bytes(body)
        # BaseHTTPMiddleware forwards the cached body via Request.wrapped_receive.
        response = await call_next(request)
        for k,v in headers.items():response.headers[k]=v
        return response

    def prune(self):
        now=time.time()
        self.pairs={k:p for k,p in self.pairs.items() if p['state']=='checking' or p['expires_at']+600>now}

    def find_code(self, value):
        now=time.time()
        self.bad_attempts=[t for t in self.bad_attempts if now-t<60]
        if len(self.bad_attempts)>=20:raise HTTPException(429,'Nhập sai nhiều lần; chờ một phút rồi thử lại.')
        if not isinstance(value,str) or not re.fullmatch(r'\d{8}',value):
            self.bad_attempts.append(now);raise HTTPException(400,'Mã gồm 8 chữ số trong SceneForge.')
        for p in self.pairs.values():
            if secrets.compare_digest(p['code'],value):
                if p['expires_at']<now:raise HTTPException(410,'Mã đã hết hạn. Tạo mã mới trong SceneForge.')
                return p
        self.bad_attempts.append(now)
        raise HTTPException(404,'Mã không đúng hoặc app đã khởi động lại. Tạo mã mới trong SceneForge.')

    def public(self,p):
        return {k:p.get(k) for k in ('id','service','name','state','expires_at','message','account_id','services','results')}

    def google_status(self):
        services = {}
        for key, pool in [('gemini_chat', self.gemini.pool), ('flow', self.flow.pool)]:
            selection = pool.status()
            services[key] = {'id': selection['account_id'], 'name': selection['account_name'],
                             'ready': selection['available'], 'mode': selection['mode']}
        links = self.gemini.vault.secret('google-service-links') or []
        flow_row = next((r for r in self.flow.pool.rows() if r['id'] == services['flow']['id']), {})
        config=self.flow.flow.config()
        engine_identity=hashlib.sha256((config.get('url','')+config.get('key','')).encode()).hexdigest()
        ui=getattr(self.flow,'web_ui',None)
        if ui and ui.binding(services['flow']['id']):
            services['flow']['transport']='web_ui'
        elif not config.get('key') or flow_row.get('engine_instance')!=engine_identity:services['flow']['ready']=False
        shared = any(link.get('gemini_chat') == services['gemini_chat']['id']
                     and link.get('flow') == services['flow']['id']
                     and link.get('engine_instance') == flow_row.get('engine_instance')
                     for link in links)
        return {'services': services, 'shared': bool(shared and all(s['ready'] and s['mode'] == 'selected' for s in services.values())),
                'identity_note': 'Cùng lượt kết nối không xác minh hai trang đang mở cùng email Google.'}

    async def finish(self,p,cookies,browser_context=None):
        services = p.get('services') or [p['service']]
        joint = len(services) == 2
        results = {}
        p['results'] = results
        try:
            for service in services:
                allowed = {'google.com','gemini.google.com'} if service == 'gemini_chat' else {'google.com','labs.google','flow.google.com'}
                scoped = [c for c in cookies if c['domain'].lstrip('.') in allowed and (service!='gemini_chat' or c.get('path','/')=='/')]
                try:
                    if service == 'gemini_chat':
                        result = await self.gemini.import_session(p['name'], scoped)
                        aid = result['id']
                        self.gemini.pool.select({'mode':'selected','account_id':aid})
                    else:
                        options={}
                        if browser_context:options['browser_context']=browser_context
                        if p.get('native_route'):options['browser_route']=p['native_route']
                        result = await self.flow.import_session(scoped,**options)
                        aid = result.get('imported_account_id')
                        if joint or aid:
                            if not aid:raise flow_error('FLOW_ACCOUNT_ID_MISSING','import')
                            check = await self.flow.check(aid)
                            if not check.get('ok'):raise flow_error('FLOW_AUTH_EXPIRED' if check.get('reason')=='auth' else 'FLOW_SESSION_CHECK_FAILED','check')
                            self.flow.pool.select({'mode':'selected','account_id':aid})
                    results[service] = {'state':'done','account_id':aid,'message':'Đã kiểm tra và chọn tài khoản.' if joint else 'Đã nhận phiên; xem trạng thái dịch vụ.'}
                    if service == p['service']:p['account_id'] = aid
                except asyncio.CancelledError:raise
                except Exception as exc:
                    # Only locally allow-listed error codes/messages may cross the boundary.
                    results[service] = {'state':'failed',**(flow_public_error(exc) if service=='flow' else {'code':'GEMINI_SESSION_CHECK_FAILED','message':'Chưa kiểm tra/kết nối được Gemini. Kiểm tra đăng nhập trong trình duyệt rồi kết nối lại.'})}
                    if service=='gemini_chat' and isinstance(exc,HTTPException):
                        detail=exc.detail
                        allowed={'GEMINI_SESSION_COOKIE_MISSING','GEMINI_SESSION_GUEST','GEMINI_SESSION_TOKEN_MISSING','GEMINI_ACCOUNT_UNAVAILABLE','GEMINI_SESSION_INIT_FAILED','GEMINI_SESSION_AUTH_ERROR','GEMINI_SESSION_CHECK_TIMEOUT','GEMINI_SDK_UNAVAILABLE','GEMINI_SESSION_AUTH_REJECTED','GEMINI_SDK_INCOMPATIBLE','GEMINI_SESSION_CHECK_FAILED'}
                        if isinstance(detail,dict) and detail.get('code') in allowed:
                            results[service].update(code=detail['code'],message=detail['message'])
                        elif detail=='Chạy local_engine/install-gemini-web.bat trước khi dùng Gemini Chat.':
                            results[service].update(code='GEMINI_SDK_MISSING',message=detail)
                    if service=='flow' and p.get('native_route'):self.relay.revoke(p['native_route']['id'])
                    if service=='flow':results[service]['diagnostics']={**flow_diagnostics(scoped),**{k:v for k,v in results[service].items()if k in {'stage','provider_http_status','provider_error_kind','completed_steps'}}}
            done = sum(r['state'] == 'done' for r in results.values())
            if joint and done == 2:
                row = next((r for r in self.flow.pool.rows() if r['id'] == results['flow']['account_id']), {})
                link = {'gemini_chat':results['gemini_chat']['account_id'], 'flow':results['flow']['account_id'],
                        'engine_instance':row.get('engine_instance'), 'name':p['name'], 'at':time.time()}
                links = self.gemini.vault.secret('google-service-links') or []
                links = [r for r in links if (r.get('gemini_chat'),r.get('flow')) != (link['gemini_chat'],link['flow'])]
                self.gemini.vault.set_secret('google-service-links', (links + [link])[-50:])
            state = 'done' if done == len(services) else 'partial' if done else 'failed'
            message = ('Gemini Chat và Flow đã kết nối, kiểm tra riêng từng dịch vụ. Chưa thử tạo nội dung.' if joint and done == 2
                       else 'Chỉ kết nối được một dịch vụ; bên còn lại cần kiểm tra. Không tự tạo nội dung.' if state == 'partial'
                       else 'Đã nhận phiên vào app. Xem trạng thái trong Tài khoản; chưa chứng nhận tạo nội dung hoặc hạn mức.' if done
                       else 'Chưa xác minh được phiên. Kiểm tra đăng nhập trong trình duyệt rồi kết nối lại.')
            if joint:
                message='; '.join(('Gemini Chat' if k=='gemini_chat' else 'Flow')+(': đã kiểm tra và chọn' if results[k]['state']=='done' else ': '+results[k]['message']) for k in services)+'. Chưa thử tạo nội dung.'
            elif not done:message=results[services[0]]['message']
            if p.get('native_route') and results.get('flow',{}).get('state')=='done':message+=' Flow chạy qua tab đã nối; giữ Chrome/Edge và tab Flow mở.'
            p.update(state=state,message=message)
        except asyncio.CancelledError:
            p.update(state='failed',message='App đã dừng lúc kiểm tra phiên. Mở lại mục Tài khoản để kiểm tra kết quả.')
            raise
        except Exception:
            p.update(state='partial' if any(r.get('state')=='done' for r in results.values()) else 'failed',message='Đã xử lý phiên nhưng chưa lưu đủ liên kết. Xem từng dịch vụ trong Tài khoản; không tự gửi lại.')

    async def close(self):
        await self.relay.close()
        for task in list(self.tasks):task.cancel()
        if self.tasks:await asyncio.gather(*self.tasks,return_exceptions=True)
        self.pairs.clear()

    def install(self,app):
        @app.get('/local-api/browser-bridge/setup')
        async def setup():
            return {'extension_id':self.extension_id,'folder':str(self.root), 'download':'/local-api/browser-bridge/extension.zip','protocol':2}

        @app.get('/local-api/browser-bridge/google-status')
        async def google_status():
            return self.google_status()

        @app.get('/local-api/browser-bridge/extension.zip')
        async def extension_zip():
            return FileResponse(self.root.parent/'browser-extension-package.zip',filename='SceneForge-Browser-Connect.zip',media_type='application/zip')

        @app.post('/local-api/browser-bridge/open-folder')
        async def folder():
            if os.name!='nt':raise HTTPException(409,'Sao chép đường dẫn tiện ích vào hộp chọn thư mục của trình duyệt.')
            os.startfile(self.root)
            return {'opened':True}

        @app.post('/local-api/browser-bridge/pairs')
        async def issue(body:dict):
            service=body.get('service');name=body.get('name','').strip() if isinstance(body.get('name'),str) else ''
            if not isinstance(service,str) or service not in {'gemini_chat','flow'} or not 1<=len(name)<=80:raise HTTPException(400,'Chọn nguồn và nhập tên tài khoản 1–80 ký tự.')
            services = body.get('services', [service])
            if not isinstance(services,list) or not services or len(services)>2 or len(set(str(v) for v in services))!=len(services) or any(v not in ('gemini_chat','flow') for v in services) or service not in services:
                raise HTTPException(400,'Chọn Gemini Chat, Flow hoặc cả hai dịch vụ.')
            if 'gemini_chat' in services:self.gemini.require_sdk()
            self.prune()
            if sum(p['state'] in {'issued','claimed','checking'} and p['expires_at']>time.time() for p in self.pairs.values())>=8:
                raise HTTPException(409,'Có nhiều mã đang chờ. Đóng các kết nối cũ hoặc chờ mã hết hạn.')
            code=str(secrets.randbelow(100_000_000)).zfill(8)
            while any(p['code']==code for p in self.pairs.values()):code=str(secrets.randbelow(100_000_000)).zfill(8)
            p={'id':secrets.token_urlsafe(20),'code':code,'service':service,'services':services,'name':name,'state':'issued','expires_at':time.time()+180,'message':'Nhập mã này trong tiện ích SceneForge ở trình duyệt đang đăng nhập.'}
            self.pairs[p['id']]=p
            return {**self.public(p),'code':code}

        @app.get('/local-api/browser-bridge/pairs/{id}')
        async def status(id:str):
            p=self.pairs.get(id)
            if not p:raise HTTPException(404,'Mã không còn; làm mới mục Tài khoản trước khi tạo mã khác.')
            value=self.public(p)
            if p['state'] in {'issued','claimed'} and p['expires_at']<time.time():value.update(state='expired',message='Mã hết hạn. Tạo mã mới.')
            return value

        @app.post('/local-api/browser-bridge/pairs/{id}/cancel')
        async def cancel(id:str):
            p=self.pairs.get(id)
            if p and p['state'] in {'issued','claimed'}:
                p.update(state='cancelled',message='Đã hủy mã.');p['code']=''
                if p.get('native_route'):self.relay.revoke(p['native_route']['id'])
            return {'ok':True}

        @app.post('/local-api/browser-bridge/claim')
        async def claim(body:dict,request:Request):
            p=self.find_code(body.get('code'))
            if p['state']!='issued':raise HTTPException(409,'Mã đã dùng. Kiểm tra trạng thái trong app trước khi tạo mã khác.')
            p.update(state='claimed',submission=secrets.token_urlsafe(32))
            relay=None
            if 'flow' in p['services'] and body.get('protocol') in (3,4):
                port=request.url.port or 8840
                relay,route=self.relay.issue('http://127.0.0.1:'+str(port)+'/local-api/browser-bridge/flow-execute',self.origin)
                p['native_route']=route
                p['ui_protocol']=body.get('protocol')==4 and p['services']==['flow']
            return {'service':p['service'],'services':p['services'],'protocol':4 if p.get('ui_protocol') else 3 if relay else 2,'name':p['name'],'submission':p['submission'],**({'relay':relay}if relay else {})}

        @app.post('/local-api/browser-bridge/complete')
        async def complete(body:dict):
            p=self.find_code(body.get('code'))
            if p['state']!='claimed' or not isinstance(body.get('submission'),str) or not secrets.compare_digest(body['submission'],p['submission']):
                raise HTTPException(409,'Mã không còn quyền nhận phiên. Kiểm tra trạng thái trong app.')
            if p.get('ui_protocol'):
                if body.get('protocol')!=4:raise HTTPException(409,'Cập nhật tiện ích kết nối giao diện Flow.')
                route=p['native_route'];self.relay.activate(route['id'])
                try:
                    result=await self.relay.request(route['id'],{'kind':'ui','action':'identity'},30)
                    driver=getattr(self.flow,'web_ui',None)
                    if not driver or not hasattr(driver,'register_extension'):raise HTTPException(409,'App chưa hỗ trợ cầu nối giao diện.')
                    aid=driver.register_extension(route['id'],result)
                except BaseException:
                    self.relay.revoke(route['id']);p.update(state='failed',message='Chưa nối được tab Flow. Tạo mã mới rồi thử lại.');raise
                p.pop('submission',None);p['code']=''
                p.update(state='done',account_id=aid,message='Đã nối tab Flow qua tiện ích. Tạo video trong SceneForge; giữ tab mở. Chưa tạo nội dung.')
                return {'accepted':True,'state':'done','message':p['message']}
            joint = len(p['services']) == 2
            if joint and body.get('protocol') not in (2,3):
                raise HTTPException(409,'Cập nhật tiện ích: mở chrome://extensions hoặc edge://extensions, bấm tải lại SceneForge rồi tạo mã mới.')
            supplied=body.get('cookies')
            allowed={'google.com','gemini.google.com'} if p['service']=='gemini_chat' else {'google.com','labs.google','flow.google.com'}
            if joint:allowed={'google.com','gemini.google.com','labs.google','flow.google.com'}
            if not isinstance(supplied,list) or not 0<len(supplied)<=200:raise HTTPException(400,'Phiên trình duyệt không hợp lệ.')
            cookies=[]
            for c in supplied:
                if not isinstance(c,dict) or str(c.get('domain','')).lstrip('.') not in allowed:raise HTTPException(400,'Phiên có miền ngoài nguồn đã chọn; chưa nhận.')
                if not isinstance(c.get('name'),str) or not isinstance(c.get('value'),str) or not 1<=len(c['name'])<=200 or len(c['value'])>16000:raise HTTPException(400,'Cookie không hợp lệ.')
                cookies.append({k:v for k,v in c.items() if k in {'name','value','domain','path','secure','httpOnly','expires','hostOnly','sameSite'}})
            if not joint and p['service']=='gemini_chat' and not any(c['name']=='__Secure-1PSID' and c['value'] for c in cookies):raise HTTPException(400,'Chưa có phiên Gemini. Đăng nhập Gemini trong chính trình duyệt chứa tiện ích trước.')
            if p.get('native_route'):self.relay.activate(p['native_route']['id'])
            p.update(state='checking',message='Đã nhận phiên · đang kiểm tra với dịch vụ.')
            p.pop('submission',None)
            from .flow_browser_context import clean_context
            context=clean_context(body.get('browser_context')) if 'flow' in p['services'] else {}
            task=asyncio.create_task(self.finish(p,cookies,context));self.tasks.add(task);task.add_done_callback(self.tasks.discard)
            return {'accepted':True,'state':'checking','message':'Đã chuyển phiên. Quay lại SceneForge để xem kết quả kiểm tra.'}


def install_browser_bridge(app,gemini,flow):return BrowserBridge(app,gemini,flow)
