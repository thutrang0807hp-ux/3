"""Experimental app-owned browser session for normal Flow UI operations.

No private RPCs, CAPTCHA tokens, fingerprint changes or credential export.
"""
from pathlib import Path
from urllib.parse import urlsplit
import asyncio

IDENTITY_SCRIPT="() => String(window.WIZ_global_data?.oPEP7c || '')"

class SessionUnavailable(RuntimeError):pass
class VerificationRequired(SessionUnavailable):pass

class FlowUiSession:
    def __init__(self,data,profile_key=None):
        from .google_login import flow_profile_path
        self.data=Path(data);self.profile_key=profile_key
        self.profile=flow_profile_path(data,profile_key)
        self.playwright=None;self.browser=None;self.page=None;self.email=None
        self.lock=asyncio.Lock()
    async def attach(self,playwright_factory):
        """Attach only to the persistent profile SceneForge opened explicitly."""
        from .flow_browser_probe import probe_flow_browser
        # The stored instance identifier must match the actual local browser.
        probe=await probe_flow_browser(self.data,self.profile_key)
        if not probe['ready']:
            # Force relaunch with fixed debug port, then probe again
            try:
                from .google_login import open_flow_web_login
                await open_flow_web_login(self.data, auto_connect=True, start_url='https://flow.google.com/')
                import asyncio
                await asyncio.sleep(2)
                probe=await probe_flow_browser(self.data,self.profile_key)
            except Exception as e:
                probe={'ready':False,'code':'FLOW_BROWSER_ENDPOINT_UNAVAILABLE','detail':'relaunch:'+type(e).__name__}
        if not probe['ready']:
            from .google_login import flow_profile_path
            prof = flow_profile_path(self.data, self.profile_key)
            portfile = prof / 'DevToolsActivePort'
            exists = portfile.is_file()
            extra = 'portfile=' + ('YES' if exists else 'NO') + ' path=' + str(prof)
            diag=''
            try:
                diag=' | '+(Path(self.data)/'browser-profiles'/'LAUNCH-DIAG.txt').read_text(encoding='utf-8')
            except Exception:
                pass
            raise SessionUnavailable('[V4-DIAG] Chưa nối được đúng cửa sổ Flow của app. '+probe['code']+'. '+extra+' '+probe.get('detail','')+diag)
        self.playwright=await playwright_factory().start()
        try:
            self.browser=await self.playwright.chromium.connect_over_cdp(probe['endpoint'],timeout=10000)
            pages=[p for c in self.browser.contexts for p in c.pages if self.is_flow(p.url)]
            if len(pages)!=1:raise SessionUnavailable('Giữ một tab Flow trong cửa sổ riêng để chọn đúng project.')
            self.page=pages[0]
            identity=await self.page.evaluate(IDENTITY_SCRIPT)
            if not isinstance(identity,str)or '@'not in identity:raise SessionUnavailable('Đăng nhập trong tab Flow trước.')
            self.email=identity.strip().casefold()
            await self.assert_ready()
        except BaseException:
            await self.disconnect();raise
    @staticmethod
    def is_flow(url):
        try:
            p=urlsplit(url)
            return p.scheme=='https'and p.hostname=='flow.google.com'and not p.username and not p.password
        except ValueError:return False

    async def goto_project(self, project_id):
        """Navigate the attached Flow tab to the bound project."""
        if not project_id or not isinstance(project_id, str):
            return
        target = 'https://flow.google.com/project/' + project_id + '?pli=1'
        if not self.page or self.page.is_closed():
            raise SessionUnavailable('Cửa sổ Flow đã đóng.')
        current = self.page.url or ''
        if '/project/' + project_id in current:
            return
        await self.page.goto(target, wait_until='domcontentloaded', timeout=30000)
        await self.page.wait_for_timeout(1500)
        if '/project/' + project_id not in (self.page.url or ''):
            raise SessionUnavailable('Chưa vào được đúng dự án Flow. Kiểm tra cửa sổ.')

    async def assert_ready(self):
        if not self.browser or not self.browser.is_connected()or not self.page or self.page.is_closed():
            raise SessionUnavailable('Cửa sổ Flow đã đóng. Chưa gửi tác vụ mới.')
        if not self.is_flow(self.page.url):raise SessionUnavailable('Tab Flow đã chuyển trang. Chưa gửi tác vụ mới.')
        identity=await self.page.evaluate(IDENTITY_SCRIPT)
        if not isinstance(identity,str)or identity.strip().casefold()!=self.email:
            raise SessionUnavailable('Tài khoản trong tab đã đổi. Chưa gửi tác vụ mới.')
        # Pause for visible challenges. Never interact with or extract CAPTCHA data.
        for frame in self.page.frames:
            if 'google.com/recaptcha/'in frame.url and '/bframe'in frame.url:
                element=await frame.frame_element()
                if await element.is_visible():raise VerificationRequired('Hoàn tất xác minh trên web trước. App không tự vượt xác minh.')
        alerts=self.page.get_by_role('alert')
        for alert in await alerts.all():
            if not await alert.is_visible():continue
            text=(await alert.inner_text()).casefold()
            if any(word in text for word in ('unusual activity','hoạt động bất thường','public_error_unusual_activity')):
                raise VerificationRequired('Google từ chối hoạt động bất thường. Đã dừng, không thử lại.')
        return True
    async def disconnect(self):
        # Disconnect the automation client, never close/delete the user's profile.
        pw=self.playwright
        self.playwright=self.browser=self.page=None;self.email=None
        if pw:await pw.stop()
