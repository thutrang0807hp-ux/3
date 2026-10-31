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
    def __init__(self, profile, process):
        self.profile, self.process = profile, process
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
        if self.closed:
            return
        self.closed = True
        try:
            if self.connection:
                await self.connection.close()
        finally:
            if self.pw:
                await self.pw.stop()
            if self.process.poll() is None:
                if os.name == 'nt':
                    await asyncio.to_thread(subprocess.run, ['taskkill', '/PID', str(self.process.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
                else:
                    self.process.terminate()
                try:
                    await asyncio.to_thread(self.process.wait, timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            await asyncio.to_thread(shutil.rmtree, self.profile, True)

    async def stop(self):
        await self.close()


async def open_google_login(url, data):
    if url not in ('https://gemini.google.com/', 'https://labs.google/fx/tools/flow'):
        raise ValueError('Unsupported Google login destination')
    executable = installed_browser()
    root = Path(data)/'login-sessions'
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    profile = Path(tempfile.mkdtemp(prefix='google-', dir=root))
    # Dedicated writable profile is required by Chrome 136+ for local CDP.
    args = [executable, '--user-data-dir='+str(profile),
            '--no-first-run', '--no-default-browser-check',
            '--disable-session-crashed-bubble', '--disable-sync',
            '--new-window', url]
    try:
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   **({'creationflags':0x08000000} if os.name == 'nt' else {}))
    except OSError:
        shutil.rmtree(profile, ignore_errors=True)
        raise HTTPException(503, 'Chưa mở được Chrome/Edge. Kiểm tra trình duyệt đã cài trên máy.') from None
    login = InteractiveLogin(profile, process)
    deadline = time.monotonic()+25
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        if (profile/'DevToolsActivePort').is_file():
            return login
        await asyncio.sleep(.2)
    await login.close()
    raise HTTPException(503, 'Chrome/Edge chưa sẵn sàng nhận phiên. Có thể trình duyệt bị chính sách máy chặn kết nối cục bộ; chưa lưu tài khoản.')


_FLOW_WEB_PROCESSES=[]

def flow_profile_path(data,profile_key=None):
    if profile_key is None:return Path(data)/'browser-profiles'/'flow-web'
    import re
    if not isinstance(profile_key,str)or not re.fullmatch(r'[a-f0-9]{24}',profile_key):
        raise HTTPException(400,'Profile Flow không hợp lệ.')
    return Path(data)/'browser-profiles'/'flow-accounts'/profile_key


def _kill_profile_chrome(profile):
    """Best-effort: close Chrome/Edge that may be locking this profile (Windows)."""
    if os.name != 'nt':
        return
    try:
        import subprocess as sp
        marker = str(profile.resolve()).lower().replace('\\','\\')
        for exe in ('chrome.exe', 'msedge.exe'):
            try:
                out = sp.check_output(['wmic', 'process', 'where', f"name='{exe}'", 'get', 'ProcessId,CommandLine', '/format:list'],
                                      stderr=sp.DEVNULL, text=True, timeout=8, creationflags=0x08000000)
            except Exception:
                continue
            pid = None
            for line in out.splitlines():
                line=line.strip()
                if line.lower().startswith('commandline=') and marker in line.lower():
                    # next ProcessId line or previous
                    pass
                if line.lower().startswith('processid='):
                    pid = line.split('=',1)[-1].strip()
                if pid and marker in out.lower():
                    sp.run(['taskkill', '/F', '/PID', pid], stdout=sp.DEVNULL, stderr=sp.DEVNULL, creationflags=0x08000000)
                    pid = None
        # Do NOT kill all Chrome/Edge. Only processes that match this profile (handled above).
    except Exception:
        pass

async def open_flow_web_login(data,auto_connect=False,profile_key=None,start_url=None):
    """Installed browser with an app-owned profile; optional standard loopback CDP. No generation."""
    executable=installed_browser()
    profile=flow_profile_path(data,profile_key)
    profile.mkdir(parents=True,exist_ok=True,mode=0o700)
    url = start_url or 'https://flow.google.com/'
    try:
        (Path(data)/'browser-profiles'/'LAST-OPEN-ATTEMPT.txt').write_text('fixedport-9333', encoding='utf-8')
    except Exception:
        pass
    # Always enable debugging when auto_connect or when opening a specific project.
    # First-time clean login (no auto_connect, no start_url) stays without debug.
    args=[executable,'--user-data-dir='+str(profile.resolve()),
          '--no-first-run','--no-default-browser-check',
          '--disable-session-crashed-bubble','--disable-sync',
          '--new-window', url]
    if auto_connect or start_url:
        # Clean stale port file and use a fixed port so we know where to connect
        portfile = profile / 'DevToolsActivePort'
        try:
            portfile.unlink(missing_ok=True)
        except Exception:
            pass
        args[1:1]=['--remote-debugging-address=127.0.0.1','--remote-debugging-port=9333','--remote-allow-origins=*','--disable-background-networking','--disable-sync','--disable-features=Translate,OptimizationHints']
    if auto_connect or start_url:
        _kill_profile_chrome(profile)
        import time; time.sleep(0.8)
    try:
        process=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                 **({'creationflags':0x08000000}if os.name=='nt'else{}))
    except OSError:
        raise HTTPException(503,'Chưa mở được Chrome/Edge. Kiểm tra trình duyệt đã cài trên máy.')from None
    _FLOW_WEB_PROCESSES[:]=[p for p in _FLOW_WEB_PROCESSES if p.poll()is None]
    _FLOW_WEB_PROCESSES.append(process)
    # Wait for debug port if we requested it
    launched_ok = False
    exit_code = None
    if auto_connect or start_url:
        import time
        deadline = time.monotonic() + 25
        portfile = profile / 'DevToolsActivePort'
        while time.monotonic() < deadline:
            if portfile.is_file():
                launched_ok = True
                break
            exit_code = process.poll()
            if exit_code is not None:
                break
            time.sleep(0.4)
        # Write diagnostic
        try:
            diag = f'portfile={portfile.is_file()} exit={exit_code} pid={process.pid}'
            (Path(data)/'browser-profiles'/'LAUNCH-DIAG.txt').write_text(diag, encoding='utf-8')
        except Exception:
            pass
    return {'opened':True,'debug_ready':launched_ok,'message':'Đã gửi lệnh mở Flow.'}
