"""Offline original CLI runtime and filesystem alias to SceneForge's selected profile."""
import ctypes
import hashlib
import os
from pathlib import Path
import struct


def bundled_runtime(data):
    from .flow_gflow_runtime import ensure_runtime
    archive=Path(__file__).resolve().parents[1]/'vendor/gflow-original.zip'
    if not archive.is_file():
        raise RuntimeError('Bản cập nhật thiếu runtime CLI đi kèm. Cài lại gói cập nhật đầy đủ; không cần GFlow trong Downloads.')
    return ensure_runtime(data,archive=archive).parent


def profile_identity(data,account,binding):
    from .google_login import flow_profile_path
    target=flow_profile_path(data,binding.get('profile_key')).resolve()
    if not target.is_dir():raise RuntimeError('Không có profile Flow đã chọn trong dữ liệu SceneForge; kiểm tra tab Tài khoản.')
    home=Path(data)/'flow-cli';name='sf_'+hashlib.sha256(account.encode()).hexdigest()[:20]
    return home,name,target


def directory_alias(alias,target):
    if alias.exists() or alias.is_symlink():
        if alias.resolve()!=target:raise RuntimeError('Profile CLI trỏ sang tài khoản khác; chưa gọi CLI.')
        return
    if os.name!='nt':alias.symlink_to(target,target_is_directory=True);return
    # NTFS junction; no administrator privileges or cmd/shell required.
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    create=kernel.CreateFileW;create.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p];create.restype=wintypes.HANDLE
    control=kernel.DeviceIoControl;control.argtypes=[wintypes.HANDLE,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),ctypes.c_void_p];control.restype=wintypes.BOOL
    close=kernel.CloseHandle;close.argtypes=[wintypes.HANDLE];close.restype=wintypes.BOOL
    text=str(target)
    substitute=('\\??\\UNC\\'+text[2:] if text.startswith('\\\\') else '\\??\\'+text).encode('utf-16-le');printed=text.encode('utf-16-le')
    paths=substitute+b'\0\0'+printed+b'\0\0'
    data=struct.pack('<IHHHHHH',0xA0000003,8+len(paths),0,0,len(substitute),len(substitute)+2,len(printed))+paths
    alias.mkdir();handle=create(str(alias),0x40000000,0,None,3,0x02200000,None)
    if handle==ctypes.c_void_p(-1).value:
        alias.rmdir();raise ctypes.WinError(ctypes.get_last_error())
    try:
        returned=wintypes.DWORD();buffer=ctypes.create_string_buffer(data)
        if not control(handle,0x900A4,buffer,len(data),None,0,ctypes.byref(returned),None):raise ctypes.WinError(ctypes.get_last_error())
    except BaseException:
        close(handle);alias.rmdir();raise
    else:close(handle)


def prepare_profile(data,account,binding):
    """Call only after the managed browser is disconnected. No cookie copies."""
    from .google_login import installed_browser
    home,name,target=profile_identity(data,account,binding)
    email=binding['email'].strip().casefold();marker=target/'.gflow_account'
    if marker.exists() and marker.read_text(encoding='utf-8').strip().casefold()!=email:
        raise RuntimeError('Email trong profile CLI không khớp tài khoản SceneForge; chưa gửi tạo.')
    strategy=target/'.gflow_browser_strategy'
    if not strategy.exists():
        browser=Path(installed_browser()).name.lower()
        if browser not in ('chrome.exe','google-chrome','google-chrome-stable'):
            raise RuntimeError('CLI gốc cần Google Chrome cho profile này. Phiên đăng nhập được giữ; chưa gửi tạo.')
        strategy.write_text('chrome',encoding='utf-8')
    if not marker.exists():marker.write_text(email,encoding='utf-8')
    home.mkdir(parents=True,exist_ok=True);directory_alias(home/('profile_'+name),target)
    return home,name


def existing_profile(data,account,binding,meta):
    home,name,target=profile_identity(data,account,binding)
    alias=home/('profile_'+name)
    if meta.get('home')!=str(home) or meta.get('profile')!=name or not alias.is_dir() or alias.resolve()!=target:return None
    try:
        if (alias/'.gflow_account').read_text(encoding='utf-8').strip().casefold()!=binding['email'].casefold():return None
    except OSError:return None
    return home,name
