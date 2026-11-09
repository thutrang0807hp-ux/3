"""Apply the installed SceneForge icon to its own desktop window, without replacing the host."""
import json,os,threading
from pathlib import Path

def normalized(path):return os.path.normcase(os.path.realpath(path))

def owned_window(state,expected_exe,api):
 try:
  hwnd=int(state['window']);pid=int(state['pid'])
  if hwnd<=0 or pid<=0 or api.window_pid(hwnd)!=pid:return None
  actual=api.process_path(pid)
  if not actual or normalized(actual)!=normalized(expected_exe):return None
  return hwnd
 except(KeyError,TypeError,ValueError,OSError):return None

class WindowsIcons:
 def __init__(self):
  import ctypes
  from ctypes import wintypes
  self.c=ctypes;self.user=ctypes.WinDLL('user32',use_last_error=True);self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
  self.user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)];self.user.GetWindowThreadProcessId.restype=wintypes.DWORD
  self.kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];self.kernel.OpenProcess.restype=wintypes.HANDLE
  self.kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)];self.kernel.QueryFullProcessImageNameW.restype=wintypes.BOOL
  self.kernel.CloseHandle.argtypes=[wintypes.HANDLE];self.kernel.CloseHandle.restype=wintypes.BOOL
  self.user.LoadImageW.argtypes=[wintypes.HINSTANCE,wintypes.LPCWSTR,wintypes.UINT,ctypes.c_int,ctypes.c_int,wintypes.UINT];self.user.LoadImageW.restype=wintypes.HANDLE
  self.user.SendMessageTimeoutW.argtypes=[wintypes.HWND,wintypes.UINT,ctypes.c_size_t,ctypes.c_ssize_t,wintypes.UINT,wintypes.UINT,ctypes.POINTER(ctypes.c_size_t)];self.user.SendMessageTimeoutW.restype=ctypes.c_ssize_t
  self.user.DestroyIcon.argtypes=[wintypes.HANDLE];self.user.DestroyIcon.restype=wintypes.BOOL
  self.user.GetSystemMetrics.argtypes=[ctypes.c_int];self.user.GetSystemMetrics.restype=ctypes.c_int
  self.icons=None
 def window_pid(self,hwnd):
  from ctypes import wintypes
  pid=wintypes.DWORD()
  if not self.user.GetWindowThreadProcessId(hwnd,self.c.byref(pid)):return 0
  return pid.value
 def process_path(self,pid):
  from ctypes import wintypes
  handle=self.kernel.OpenProcess(0x1000,False,pid)
  if not handle:return None
  try:
   size=wintypes.DWORD(32768);text=self.c.create_unicode_buffer(size.value)
   return text.value if self.kernel.QueryFullProcessImageNameW(handle,0,text,self.c.byref(size)) else None
  finally:self.kernel.CloseHandle(handle)
 def apply(self,hwnd,icon_path):
  if self.icons is None:
   metric=self.user.GetSystemMetrics
   try:
    self.user.GetDpiForWindow.argtypes=[self.c.c_void_p];self.user.GetDpiForWindow.restype=self.c.c_uint
    self.user.GetSystemMetricsForDpi.argtypes=[self.c.c_int,self.c.c_uint];self.user.GetSystemMetricsForDpi.restype=self.c.c_int
    dpi=self.user.GetDpiForWindow(hwnd) or 96;metric=lambda index:self.user.GetSystemMetricsForDpi(index,dpi)
   except AttributeError:pass
   big=self.user.LoadImageW(None,str(icon_path),1,max(32,metric(11)),max(32,metric(12)),0x10)
   small=self.user.LoadImageW(None,str(icon_path),1,max(16,metric(49)),max(16,metric(50)),0x10)
   if not big or not small:
    if big:self.user.DestroyIcon(big)
    if small:self.user.DestroyIcon(small)
    return False
   # Window messages retain the HICON handles for this backend/desktop lifetime.
   self.icons=(big,small)
  result=self.c.c_size_t()
  for kind,icon in [(1,self.icons[0]),(0,self.icons[1])]:
   if not self.user.SendMessageTimeoutW(hwnd,0x80,kind,int(icon),2,1000,self.c.byref(result)):return False
  return True
 def release(self):
  if self.icons:
   for icon in self.icons:self.user.DestroyIcon(icon)
   self.icons=None

def install_desktop_icon(data,app_root,api_factory=WindowsIcons):
 if os.name!='nt' or os.environ.get('SCENEFORGE_DESKTOP')!='1':return None
 data=Path(data);app_root=Path(app_root);icon=app_root/'dist/web-demo/icons/SceneForge.ico';expected=app_root.parent/'SceneForge.exe'
 if not icon.is_file():return None
 def worker():
  api=None
  try:
   api=api_factory();state_file=data/'desktop-state.json';applied=None;attempts=0
   while attempts<120:
    attempts+=1
    try:state=json.loads(state_file.read_text(encoding='utf-8-sig'))
    except(OSError,ValueError):state={}
    hwnd=owned_window(state,expected,api)
    if hwnd and api.apply(hwnd,icon):
     applied=hwnd;break
    threading.Event().wait(.25)
   if applied:
    # Reapply after startup/DPI messages; only the matching installed app can be touched.
    for _ in range(3):
     threading.Event().wait(1)
     try:state=json.loads(state_file.read_text(encoding='utf-8-sig'))
     except(OSError,ValueError):break
     if owned_window(state,expected,api)!=applied:break
     api.apply(applied,icon)
    # Keep handles alive: the window owns references until this process exits.
    return
   if api:api.release()
  except Exception:
   # Branding must never prevent application startup or exports.
   if api:
    try:api.release()
    except Exception:pass
 thread=threading.Thread(target=worker,name='SceneForge-desktop-icon',daemon=True);thread.start();return thread
