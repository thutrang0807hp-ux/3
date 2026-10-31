"""Automatic import from the app-owned persistent login window; no generation."""
import asyncio,json,time
from pathlib import Path
from fastapi import HTTPException
from .google_login import open_flow_web_login,flow_profile_path
from .flow_connection import public_error

def google_signin_rejected(url):
    """Recognize Google's rejection route without reading/exporting query data."""
    from urllib.parse import urlsplit
    import re
    try:
        parsed=urlsplit(url)
        return parsed.scheme=='https'and parsed.hostname=='accounts.google.com'and not parsed.username and not parsed.password and bool(re.match(r'^/(?:v[0-9]+/)?signin/rejected(?:/|$)',parsed.path))
    except (ValueError,TypeError):return False

async def login_attempt_pages(browser,target=None):
    """Follow one selected tab and its auth popup, never unrelated old failures."""
    from urllib.parse import urlsplit
    pages=[(context,page) for context in browser.contexts for page in context.pages]
    def host(page):
        try:
            value=urlsplit(page.url)
            return value.hostname if value.scheme=='https' and not value.username and not value.password else None
        except ValueError:return None
    if target is None:
        candidates=[item for item in pages if host(item[1])=='flow.google.com']
        if not candidates:candidates=[item for item in pages if host(item[1])=='accounts.google.com']
        if len(candidates)>1:
            raise HTTPException(409,'Giữ một tab Flow hoặc một tab đăng nhập trong cửa sổ riêng để chọn đúng lượt đăng nhập.')
        if not candidates:return None,[]
        target=candidates[0][1]
    selected=[item for item in pages if item[1] is target]
    if not selected:raise HTTPException(409,'Tab đăng nhập của lượt này đã đóng. Chưa nhận tài khoản.')
    for context,page in pages:
        if page is target or host(page)!='accounts.google.com':continue
        opener=getattr(page,'opener',None)
        if opener:
            try:
                if await opener() is target:selected.append((context,page))
            except Exception:pass
    return target,selected

class FlowWebLogin:
    startup_timeout=30
    def __init__(self,data,accounts):
        self.data=Path(data);self.accounts=accounts;self.task=None;self.profile_key=None;self.start_lock=asyncio.Lock()
        self.state={'state':'idle','message':'Chưa mở đăng nhập web.'}
    def status(self):return dict(self.state)
    def managed_driver(self):
        ui=getattr(self.accounts,'web_ui',None)
        if getattr(ui,'managed_browser',False):return ui
        legacy=getattr(ui,'legacy',None)
        return legacy if getattr(legacy,'managed_browser',False)else None
    async def start(self,new_profile=False):
        # Serialize startup across the readiness probe and browser launch.
        async with self.start_lock:
            return await self._start(new_profile)
    async def _start(self,new_profile=False):
        if self.task and not self.task.done():
            if new_profile:raise HTTPException(409,'Đang chờ đăng nhập ở cửa sổ hiện tại. Hoàn tất trước khi thêm profile khác.')
            return {'opened':True,**self.status()}
        if self.managed_driver():
            import secrets
            vault=self.accounts.vault;aid=self.accounts.pool.status().get('account_id')
            saved=(vault.secret('flow-managed-profiles')or{}).get(aid)
            last=vault.secret('flow-web-last-profile')or{}
            if new_profile:self.profile_key=secrets.token_hex(12)
            elif saved:self.profile_key=saved.get('profile_key')
            elif last:self.profile_key=last.get('profile_key')
            elif flow_profile_path(self.data).exists():self.profile_key=None
            else:self.profile_key=secrets.token_hex(12)
            vault.set_secret('flow-web-last-profile',{'profile_key':self.profile_key})
        from .flow_browser_probe import probe_flow_browser
        probe=await probe_flow_browser(self.data,self.profile_key)
        reuse=probe['ready']
        if not reuse:
            if self.profile_key is None:await open_flow_web_login(self.data,auto_connect=True)
            else:await open_flow_web_login(self.data,auto_connect=True,profile_key=self.profile_key)
        self.state={'state':'waiting','message':'Đăng nhập Flow trong cửa sổ vừa mở. App sẽ tự kiểm tra và nhận tài khoản; giữ cửa sổ mở.'}
        self.task=asyncio.create_task(self.watch())
        return {'opened':True,**self.status()}
    async def close(self):
        if self.task and not self.task.done():
            self.task.cancel()
            try:await self.task
            except asyncio.CancelledError:pass
    async def import_account(self,cookies,context,email=''):
        self.state={'state':'checking','message':'Đã thấy phiên Flow. Đang kiểm tra kết nối tài khoản; chưa tạo video.'}
        managed=self.managed_driver()
        if email and managed:
            import hashlib
            vault=self.accounts.vault;email=email.strip().casefold();digest=hashlib.sha256(email.encode()).hexdigest();aid='flow-web-'+digest[:24]
            previous=vault.secret('flow-managed-profiles')or{};profiles={**previous}
            profiles[aid]={'account_id':aid,'email':email,'account_hash':digest,'profile_key':self.profile_key,'transport':'managed_browser'}
            vault.set_secret('flow-managed-profiles',profiles)
            try:await managed.verify(aid)
            except BaseException:
                vault.set_secret('flow-managed-profiles',previous);raise
            # Explicit web login switches this identity to the managed browser,
            # after verification, without retaining a conflicting extension route.
            extension=vault.secret('flow-extension-ui')or{}
            if extension.get('account_id')==aid:
                if getattr(self.accounts,'native_relay',None):self.accounts.native_relay.revoke(extension['route_id'])
                vault.delete_secret('flow-extension-ui')
            old=next((a for a in self.accounts.pool.rows()if a['id']==aid),{})
            old={k:v for k,v in old.items()if k not in {'engine_id','native_route_id'}}
            vault.put('accounts',{**old,'id':aid,'service':'flow','name':email+' · trình duyệt riêng','login_transport':'web_ui','enabled':True,'session_verified':True,'state':'ready','active':False,'priority':old.get('priority',len(self.accounts.pool.rows())),'credit':None})
            self.accounts.pool.select({'mode':'selected','account_id':aid})
            self.state={'state':'done','account_id':aid,'message':'Đã nhận tài khoản trong Chrome/Edge riêng, không cần tiện ích hoặc mã. Mở đúng dự án Flow trong cửa sổ này và giữ mở khi tạo video. Chưa gửi tạo nội dung.'}
            return
        if email and getattr(self.accounts,'web_ui',None)and hasattr(self.accounts,'vault'):
            import hashlib
            aid='flow-web-'+hashlib.sha256(email.strip().casefold().encode()).hexdigest()[:24]
            self.accounts.vault.set_secret('flow-ui-profile',{'account_id':aid,'email':email.strip().casefold()})
            await self.accounts.web_ui.verify(aid)
            old=next((a for a in self.accounts.pool.rows()if a['id']==aid),{})
            self.accounts.vault.put('accounts',{**old,'id':aid,'service':'flow','name':email+' · web UI','login_transport':'web_ui','enabled':True,'session_verified':True,'state':'ready','active':False,'priority':old.get('priority',len(self.accounts.pool.rows())),'credit':None})
            self.accounts.pool.select({'mode':'selected','account_id':aid})
            self.state={'state':'done','account_id':aid,'message':'Đã nối tài khoản với cửa sổ Flow riêng. Bản thử sẽ thao tác trực tiếp trên giao diện web khi bạn tạo clip. Trên web chọn Lite 8 giây và Frames to Video; giữ cửa sổ mở.'}
            return
        # Preserve a previously paired native route for this same verified identity.
        existing=next((a for a in self.accounts.pool.rows() if email and str(a.get('name','')).casefold()==email.casefold() and a.get('native_route_id')),None)
        if existing:
            checked=await self.accounts.check(existing['id'])
            if not checked.get('ok'):raise HTTPException(409,'Tài khoản đã nối bằng mã chưa xác minh được; giữ kết nối cũ, không thay phiên đang dùng.')
            self.state={'state':'done','account_id':existing['id'],'message':'Đã nhận tài khoản Flow đã kết nối trong app; giữ nguyên kết nối bằng mã hiện có.'}
            return
        result=await self.accounts.import_session(cookies,browser_context=context)
        aid=result.get('imported_account_id')
        if not aid:raise HTTPException(502,'Engine chưa trả mã tài khoản.')
        checked=await self.accounts.check(aid)
        if not checked.get('ok'):raise HTTPException(409,'Engine chưa xác minh được phiên Flow.')
        if email and hasattr(self.accounts,'vault'):
            self.accounts.vault.set_secret('flow-ui-profile',{'account_id':aid,'email':email.strip().casefold()})
        self.state={'state':'done','account_id':aid,'message':'Đã nhận tài khoản Flow. Bản thử sẽ thao tác trực tiếp trên cửa sổ web này khi bạn bấm tạo clip. Giữ cửa sổ mở, chọn Lite 8 giây và Frames to Video trên web. Chưa gửi tạo video.'}
    async def watch(self):
        pw=None
        try:
            from playwright.async_api import async_playwright
            pw=await async_playwright().start();browser=None;login_page=None;started=time.monotonic();deadline=started+300
            while time.monotonic()<deadline:
                if browser is None:
                    try:
                        from .flow_browser_probe import probe_flow_browser
                        probe=await probe_flow_browser(self.data,self.profile_key)
                        if probe['ready']:browser=await pw.chromium.connect_over_cdp(probe['endpoint'],timeout=2000)
                        elif time.monotonic()-started>=self.startup_timeout:
                            self.state={'state':'failed','code':probe['code'],'message':'Chưa nối được đúng cửa sổ Flow của app ('+probe['code']+'). Chưa xác minh đăng nhập và chưa gửi tạo video.'};return
                    except Exception:
                        if time.monotonic()-started>=self.startup_timeout:
                            self.state={'state':'failed','code':'FLOW_BROWSER_CDP_CONNECT_FAILED','message':'Chrome đã mở nhưng app chưa kết nối được với trình duyệt qua Playwright. Chưa xác minh đăng nhập; chưa gửi tạo video.'};return
                if browser and not getattr(browser,'is_connected',lambda:True)():
                    self.state={'state':'failed','code':'FLOW_BROWSER_DISCONNECTED','message':'Kết nối tới cửa sổ Flow đã ngắt. App đã dừng kiểm tra, không tự đăng nhập lại.'};return
                if browser:
                    try:login_page,pages=await login_attempt_pages(browser,login_page)
                    except HTTPException as exc:
                        self.state={'state':'failed','code':'FLOW_WEB_LOGIN_TAB_SELECTION','message':str(exc.detail)};return
                    for context,page in pages:
                        from urllib.parse import urlsplit,parse_qs
                        u=urlsplit(page.url)
                        if google_signin_rejected(page.url):
                            self.state={'state':'failed','code':'GOOGLE_BROWSER_SIGNIN_REJECTED','message':'Google đã từ chối đăng nhập trong cửa sổ này. Chưa nhận tài khoản; app đã dừng, không tự thử lại. Đây không phải đăng nhập thành công.'};return
                        if u.hostname=='accounts.google.com':
                            try:
                                if await page.get_by_text('This browser or app may not be secure.',exact=True).is_visible():
                                    self.state={'state':'failed','code':'GOOGLE_BROWSER_SIGNIN_REJECTED','message':'Google không chấp nhận cửa sổ đăng nhập này. App đã dừng; không tự đổi nhận diện trình duyệt hoặc thử lại.'};return
                            except Exception:pass
                        if u.scheme!='https' or u.hostname!='flow.google.com':continue
                        try:
                            email=await page.evaluate(r"""() => {
                                const value=window.WIZ_global_data?.oPEP7c;
                                if(typeof value==='string')return value;
                                const match=document.documentElement.innerHTML.match(/"oPEP7c"\s*:\s*("(?:[^"\\]|\\.)*")/);
                                try{return match?JSON.parse(match[1]):'';}catch{return '';}
                            }""")
                            if '@'not in email:continue
                            cookies=[]if getattr(self.accounts,'web_ui',None)else await context.cookies(['https://flow.google.com/','https://accounts.google.com/','https://labs.google/'])
                            cookies=[c for c in cookies if c.get('domain','').lstrip('.')in {'google.com','flow.google.com','labs.google'}]
                            ua=await page.evaluate('() => navigator.userAgent')
                            value={'user_agent':ua};index=parse_qs(u.query).get('authuser',[''])[0]
                            if index.isdigit()and len(index)<=3:value['authuser']=index
                        except Exception:continue
                        await self.import_account(cookies,value,email)
                        return
                await asyncio.sleep(2)
            self.state={'state':'failed','code':'FLOW_WEB_LOGIN_TIMEOUT','message':'Chưa nhận được phiên sau 5 phút. Kiểm tra đăng nhập/xác minh trong cửa sổ Flow riêng. App không tự đăng nhập hoặc thử lại.'}
        except asyncio.CancelledError:raise
        except Exception as exc:
            from .flow_ui_driver import UiFlowFailure
            from .flow_ui_session import SessionUnavailable
            safe={'code':'FLOW_WEB_UI_NOT_READY','message':str(exc)}if isinstance(exc,(UiFlowFailure,SessionUnavailable))else public_error(exc)
            self.state={'state':'failed','code':safe.get('code','FLOW_WEB_LOGIN_FAILED'),'message':'Chưa xác minh được tài khoản từ cửa sổ web. '+safe.get('message','Kiểm tra engine Flow rồi mở lại đăng nhập web.')}
        finally:
            # Disconnect Playwright, keep the user's window/profile intact.
            if pw:await pw.stop()
