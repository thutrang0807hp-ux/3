import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import closing
from http.client import HTTPConnection, HTTPException

from PIL import Image

GEMINI_URL = "https://gemini.google.com/app"


class WorkspaceError(Exception):
    pass


def runtime_directory():
    installed = Path(sys.executable).parent / "runtime"
    return installed if getattr(sys, "frozen", False) else Path(__file__).parent / "runtime"


def discover_chrome():
    locations = ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")
    for location in locations:
        if root := os.getenv(location):
            chrome = Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe"
            if chrome.is_file():
                return chrome
    raise WorkspaceError("Cần cài Chrome trên máy để Studio mở hồ sơ Google riêng.")


def browser_port(metadata):
    try:
        port_text, socket_path, *_ = metadata.read_text().splitlines()
        port = int(port_text)
        if not 1024 <= port <= 65535 or not socket_path.startswith("/devtools/browser/"):
            return None
        with closing(HTTPConnection("127.0.0.1", port, timeout=1)) as connection:
            connection.request("GET", "/json/version")
            response = connection.getresponse()
            if response.status != 200:
                return None
            endpoint = json.loads(response.read(8192))["webSocketDebuggerUrl"]
        if endpoint == f"ws://127.0.0.1:{port}{socket_path}":
            return port
    except (OSError, ValueError, KeyError, HTTPException):
        pass
    return None


class GeminiWorkspace:
    def __init__(self, folder):
        self.folder = folder
        self.profile = folder / "google-signin-profile"
        self.login = None
        self.browser = None
        self.port = None

    def open_login(self):
        if self.login is not None and self.login.poll() is None:
            raise WorkspaceError("Cửa sổ đăng nhập đang mở. Đăng nhập Gemini xong rồi đóng cửa sổ đó.")
        if self.browser is not None and self.browser.poll() is None:
            self.close()
            if self.browser.poll() is None:
                raise WorkspaceError("Cửa sổ Gemini của app vẫn đang mở. Hãy đóng cửa sổ đó rồi thử lại.")
        chrome = discover_chrome()
        self.profile.mkdir(parents=True, exist_ok=True)
        # Credentials are entered in ordinary Chrome, before any automation attaches.
        self.login = subprocess.Popen([
            str(chrome), f"--user-data-dir={self.profile}", "--no-first-run",
            "--no-default-browser-check", "--disable-background-mode", "--new-window", GEMINI_URL,
        ], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.port = None

    def start(self):
        if self.login is not None and self.login.poll() is None:
            raise WorkspaceError("Đăng nhập xong hãy đóng cửa sổ đăng nhập trước, rồi bấm Kiểm tra kết nối.")
        if not self.profile.is_dir():
            raise WorkspaceError("Bấm Đăng nhập Gemini để kết nối tài khoản trước.")
        if self.browser is not None and self.browser.poll() is None:
            if self.port:
                return
            raise WorkspaceError("Hồ sơ Gemini của app chưa sẵn sàng. Hãy đóng cửa sổ đó rồi thử lại.")
        chrome = discover_chrome()
        metadata = self.profile / "DevToolsActivePort"
        if browser_port(metadata):
            raise WorkspaceError("Hồ sơ này còn mở từ bản trước. Hãy thoát app cũ và đóng cửa sổ Chrome riêng của nó.")
        metadata.unlink(missing_ok=True)
        self.browser = subprocess.Popen([
            str(chrome), f"--user-data-dir={self.profile}", "--remote-debugging-address=127.0.0.1",
            "--remote-debugging-port=0", "--headless=new", "--no-first-run", "--no-default-browser-check",
            "--disable-background-mode", "about:blank",
        ], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.port = None
        deadline = time.monotonic() + 18
        while time.monotonic() < deadline:
            port = browser_port(metadata)
            if port and self.browser.poll() is None:
                self.port = port
                return
            if self.browser.poll() is not None:
                break
            time.sleep(0.25)
        raise WorkspaceError("Không khởi chạy được hồ sơ Chrome riêng. Nếu cửa sổ của Gemini Tạo Ảnh đang mở từ lần trước, hãy đóng nó rồi thử lại.")

    def request(self, action, **values):
        runtime = runtime_directory()
        exe = runtime / "node.exe"
        command = str(exe) if exe.is_file() else "node"
        try:
            completed = subprocess.run(
                [command, str(runtime / "gemini.mjs")],
                input=json.dumps({"port": self.port, "request": {"action": action, **values}}),
                encoding="utf-8", capture_output=True, timeout=300,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            response = json.loads(completed.stdout)
        except subprocess.TimeoutExpired as error:
            raise WorkspaceError("Đã hết thời gian chờ Gemini.") from error
        except (OSError, ValueError) as error:
            raise WorkspaceError("Không chạy được bộ kết nối Gemini.") from error
        if response.get("error") or completed.returncode != 0:
            raise WorkspaceError(response.get("error") or "Kết nối Gemini không hoàn tất.")
        return response["result"]

    def close(self):
        if self.browser and self.browser.poll() is None and self.port:
            try:
                self.request("shutdown")
                self.browser.wait(timeout=5)
            except (WorkspaceError, subprocess.TimeoutExpired):
                pass


    def verify(self):
        self.start()
        if not self.request("verify").get("signedIn"):
            raise WorkspaceError("Gemini chưa nhận phiên đã đăng nhập. Hãy bấm Đăng nhập Gemini và kiểm tra lại.")

    def write_prompt(self, prompt):
        self.start()
        text = self.request("prompt", prompt=prompt).get("text", "").strip()
        if not text:
            raise WorkspaceError("Gemini chưa trả prompt.")
        return text

    def create_image(self, prompt):
        self.start()
        with TemporaryDirectory(dir=self.folder, prefix="gemini-image-") as temp:
            output = Path(temp) / "response"
            result = self.request("image", prompt=prompt, output=str(output))
            if not result.get("saved") or not output.is_file():
                raise WorkspaceError("Gemini chưa trả ảnh.")
            with Image.open(output) as image:
                if image.width * image.height > 24_000_000:
                    raise WorkspaceError("Ảnh kết quả quá lớn để mở trong app.")
                buffer = io.BytesIO()
                image.convert("RGBA" if "A" in image.getbands() else "RGB").save(buffer, format="PNG")
                return buffer.getvalue()
