"""Interactive Google login in an installed browser, isolated from personal profiles.

Start Chrome/Edge normally; do not attach automation until the user saves the
session. This fixes our Playwright-created login window, not Google's policies.
"""
import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from fastapi import HTTPException


def installed_browser():
    override = os.environ.get('SCENEFORGE_BROWSER')
    if override and Path(override).is_file():
        return override
    if os.name == 'nt':
        import winreg
        for name in ('chrome.exe', 'msedge.exe'):
            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                try:
                    with winreg.OpenKey(hive, 'Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\'+name) as key:
                        value = winreg.QueryValue(key, None)
                        if Path(value).is_file():
                            return value
                except OSError:
                    pass
        for folder in ('LOCALAPPDATA', 'PROGRAMFILES', 'PROGRAMFILES(X86)'):
            for suffix in ('Google/Chrome/Application/chrome.exe', 'Microsoft/Edge/Application/msedge.exe'):
                value = Path(os.environ.get(folder, '')) / suffix
                if value.is_file():
                    return str(value)
    for name in ('google-chrome', 'microsoft-edge', 'chromium', 'chromium-browser'):
        if shutil.which(name):
            return shutil.which(name)
    raise HTTPException(503, 'Cần Chrome hoặc Microsoft Edge cài trên máy để đăng nhập Google. Không dùng cửa sổ nhúng hoặc Chromium tự động để thay thế.')


class InteractiveLogin:
    def __init__(self, profile, process, keep_profile=False):
        self.profile, self.process = profile, process
        self.keep_profile=keep_profile;self.profile_release=None
        self.browser = self.context = self  # Compatible with existing login lifecycle.
        self.pw = None
        self.connection = None
        self.closed = False

    async def cookies(self):
        if self.closed or self.process.poll() is not None:
            raise HTTPException(409, 'Cửa sổ đăng nhập đã đóng. Kết nối lại và giữ cửa sổ mở đến khi Lưu phiên.')
        if self.connection is None:
            try:
                from playwright.async_api import async_playwright
                self.pw = await async_playwright().start()
                port = int((self.profile/'DevToolsActivePort').read_text().splitlines()[0])
                self.connection = await self.pw.chromium.connect_over_cdp('http://127.0.0.1:'+str(port), timeout=15000)
            except Exception:
                if self.pw:
                    await self.pw.stop()
                    self.pw = None
                raise HTTPException(503, 'Chưa đọc được phiên từ cửa sổ đăng nhập. Giữ cửa sổ mở rồi bấm Lưu phiên lại.') from None
        return await self.connection.contexts[0].cookies()

    async def close(self):
        if self.closed:return
        # Persistent Chromium profiles need a graceful browser shutdown to flush
        # their cookie database. Disconnecting CDP then killing the process loses
        # recently changed cookies even though the directory itself survives.
        if self.keep_profile and self.connection is None and self.process.poll() is None:
            try:await self.cookies()
            except Exception:pass
        self.closed=True
        try:
            if self.connection:
                if self.keep_profile:
                    try:
                        session=await self.connection.new_browser_cdp_session()
                        await session.send('Browser.close')
                    except Exception:pass  # Browser closing can end the CDP reply.
                await self.connection.close()
        finally:
            try:
                if self.keep_profile and self.process.poll() is None:
                    try:await asyncio.to_thread(self.process.wait,timeout=5)
                    except subprocess.TimeoutExpired:pass
                if self.process.poll() is None:
                    if os.name=='nt':
                        await asyncio.to_thread(subprocess.run,['taskkill','/PID',str(self.process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=0x08000000)
                    else:self.process.terminate()
                    try:await asyncio.to_thread(self.process.wait,timeout=10)
                    except subprocess.TimeoutExpired:self.process.kill()
            finally:
                try:
                    if self.pw:await self.pw.stop()
                    if not self.keep_profile:await asyncio.to_thread(shutil.rmtree,self.profile,True)
                finally:
                    if self.profile_release:self.profile_release();self.profile_release=None

    async def stop(self):
        await self.close()


async def open_google_login(url, data, *, profile=None, keep_profile=False, executable=None, device_profile=None):
    if url not in ('https://gemini.google.com/', 'https://labs.google/fx/tools/flow','https://muse.ai/','https://flow.google.com/'):
        raise ValueError('Unsupported Google login destination')
    executable = executable or installed_browser()
    root = Path(data)/'login-sessions'
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    profile = Path(profile)if profile is not None else Path(tempfile.mkdtemp(prefix='google-', dir=root))
    profile.mkdir(parents=True,exist_ok=True,mode=0o700)
    (profile/'DevToolsActivePort').unlink(missing_ok=True)
    # Dedicated writable profile is required by Chrome 136+ for local CDP.
    args = [executable, '--user-data-dir='+str(profile), '--remote-debugging-address=127.0.0.1',
            '--remote-debugging-port=0', '--window-size=1280,800', '--disk-cache-size=67108864', '--media-cache-size=33554432', '--no-first-run', '--no-default-browser-check', '--new-window', 'about:blank'if device_profile else url]
    try:
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   **({'creationflags':0x08000000} if os.name == 'nt' else {}))
    except OSError:
        if not keep_profile:shutil.rmtree(profile, ignore_errors=True)
        raise HTTPException(503, 'Chưa mở được Chrome/Edge. Kiểm tra trình duyệt đã cài trên máy.') from None
    login = InteractiveLogin(profile, process, keep_profile)
    deadline = time.monotonic()+25
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        if (profile/'DevToolsActivePort').is_file():
            if device_profile:
                try:
                    await login.cookies()
                    from .fingerprints import apply
                    context=login.connection.contexts[0];await apply(context,device_profile)
                    page=context.pages[0]if context.pages else await context.new_page();await page.goto(url,wait_until='domcontentloaded',timeout=45000)
                except BaseException:
                    await login.close();raise
            return login
        await asyncio.sleep(.2)
    await login.close()
    raise HTTPException(503, 'Chrome/Edge chưa sẵn sàng nhận phiên. Có thể trình duyệt bị chính sách máy chặn kết nối cục bộ; chưa lưu tài khoản.')


_FLOW_WEB_PROCESSES=[]
_FLOW_DEVICE_LOGINS=[]

def flow_profile_path(data,profile_key=None):
    if profile_key is None:return Path(data)/'browser-profiles'/'flow-web'
    import re
    if not isinstance(profile_key,str)or not re.fullmatch(r'[a-f0-9]{24}',profile_key):
        raise HTTPException(400,'Profile Flow không hợp lệ.')
    return Path(data)/'browser-profiles'/'flow-accounts'/profile_key

async def open_flow_web_login(data,auto_connect=False,profile_key=None):
    """Installed browser with an app-owned profile; optional standard loopback CDP. No generation."""
    executable=installed_browser()
    profile=flow_profile_path(data,profile_key)
    profile.mkdir(parents=True,exist_ok=True,mode=0o700)
    identity=profile/'sceneforge-browser.json'
    if identity.exists():
        saved=json.loads(identity.read_text());executable=saved['executable']
        if not Path(executable).is_file():raise HTTPException(409,'Cài lại trình duyệt đã dùng cho profile Flow trước khi mở lại.')
    else:
        temp=identity.with_suffix('.tmp');temp.write_text(json.dumps({'executable':executable,'window':[1280,800]}));os.replace(temp,identity)
    from .fingerprints import read_config
    fp=read_config(profile)
    if fp['enabled']:
        for old in list(_FLOW_DEVICE_LOGINS):
            if old.process.poll()is not None:await old.close();_FLOW_DEVICE_LOGINS.remove(old)
        login=await open_google_login('https://flow.google.com/',data,profile=profile,keep_profile=True,executable=executable,device_profile=fp)
        _FLOW_DEVICE_LOGINS.append(login);_FLOW_WEB_PROCESSES.append(login.process)
        return {'opened':True,'message':'Đã mở Flow với fingerprint tùy chỉnh của profile. Không bảo đảm phiên còn hiệu lực; chưa tạo video.'}
    args=[executable,'--user-data-dir='+str(profile.resolve()),'--window-size=1280,800','--disk-cache-size=67108864','--media-cache-size=33554432','--no-first-run',
          '--no-default-browser-check','--new-window','https://flow.google.com/']
    if auto_connect:args[1:1]=['--remote-debugging-address=127.0.0.1','--remote-debugging-port=0']
    try:
        process=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                 **({'creationflags':0x08000000}if os.name=='nt'else{}))
    except OSError:
        raise HTTPException(503,'Chưa mở được Chrome/Edge. Kiểm tra trình duyệt đã cài trên máy.')from None
    _FLOW_WEB_PROCESSES[:]=[p for p in _FLOW_WEB_PROCESSES if p.poll()is None]
    _FLOW_WEB_PROCESSES.append(process)
    return {'opened':True,'message':'Đã gửi lệnh mở Flow trên Chrome/Edge với profile riêng được lưu lại. Tự đăng nhập trên web. SceneForge sẽ kiểm tra phiên trong cửa sổ này; không cần cài tiện ích. Chưa đổi tài khoản đang chọn và chưa tạo video.'}
