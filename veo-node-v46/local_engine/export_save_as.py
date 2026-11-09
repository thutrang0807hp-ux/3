"""User-selected Windows Save As for completed local timeline exports."""
import asyncio,json,os,re,shutil,tempfile
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import HTTPException,Request

DIALOG_SCRIPT=r'''
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
$data = [Console]::In.ReadToEnd() | ConvertFrom-Json
$owner = New-Object System.Windows.Forms.Form
$owner.TopMost = $true
$owner.ShowInTaskbar = $false
$owner.StartPosition = 'CenterScreen'
$dialog = New-Object System.Windows.Forms.SaveFileDialog
$dialog.Title = 'Lưu video thành phẩm'
$dialog.Filter = 'Video MP4 (*.mp4)|*.mp4'
$dialog.DefaultExt = 'mp4'
$dialog.AddExtension = $true
$dialog.OverwritePrompt = $true
$dialog.CheckPathExists = $true
$dialog.RestoreDirectory = $true
$dialog.FileName = [string]$data.suggested_name
try {
 while ($true) {
  if ($dialog.ShowDialog($owner) -ne [System.Windows.Forms.DialogResult]::OK) {
   [Console]::WriteLine((@{cancelled=$true} | ConvertTo-Json -Compress))
   break
  }
  if ([IO.Path]::GetExtension($dialog.FileName).ToLowerInvariant() -ne '.mp4') {
   [void][System.Windows.Forms.MessageBox]::Show($owner,'Chọn tên tệp kết thúc bằng .mp4.','Lưu video')
   continue
  }
  [Console]::WriteLine((@{cancelled=$false;path=$dialog.FileName} | ConvertTo-Json -Compress))
  break
 }
} finally { $dialog.Dispose(); $owner.Dispose() }
'''

def suggested_name(value):
 text=re.sub(r'[\\/:*?"<>|\x00-\x1f]','-',str(value or 'SceneForge-thanh-pham.mp4'))[:170].strip(' .')
 if not text:text='SceneForge-thanh-pham.mp4'
 if not text.lower().endswith('.mp4'):text+='.mp4'
 return text

def powershell_path():
 if os.name!='nt':return None
 path=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
 return str(path)if path.is_file()else shutil.which('powershell.exe')

async def choose_windows_file(name):
 binary=powershell_path()
 if not binary:raise HTTPException(501,'Hộp thoại lưu Windows chưa khả dụng. Dùng chọn nơi lưu bằng trình duyệt.')
 import base64
 script=base64.b64encode(DIALOG_SCRIPT.encode('utf-16le')).decode('ascii')
 process=await asyncio.create_subprocess_exec(binary,'-NoProfile','-STA','-WindowStyle','Hidden','-EncodedCommand',script,stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,creationflags=getattr(__import__('subprocess'),'CREATE_NO_WINDOW',0))
 try:
  out,err=await asyncio.wait_for(process.communicate(json.dumps({'suggested_name':name},ensure_ascii=False).encode('utf-8')),900)
  if process.returncode:raise HTTPException(500,'Chưa mở được hộp thoại lưu Windows. Có thể chọn nơi lưu bằng trình duyệt.')
  if len(out)>32768:raise HTTPException(500,'Kết quả chọn nơi lưu không hợp lệ.')
  try:result=json.loads(out.decode('utf-8-sig').strip())
  except(ValueError,UnicodeError):raise HTTPException(500,'Chưa đọc được nơi lưu đã chọn.')
  if result.get('cancelled'):return None
  target=result.get('path')
  if not isinstance(target,str)or not target or len(target)>32700:raise HTTPException(500,'Nơi lưu đã chọn không hợp lệ.')
  return Path(target)
 except asyncio.TimeoutError:raise HTTPException(408,'Đã hết thời gian chọn nơi lưu. Video vẫn được giữ để lưu lại.')
 finally:
  if process.returncode is None:process.kill();await process.wait()

def signature(path):
 try:
  stat=path.stat();return(stat.st_ino,stat.st_size,stat.st_mtime_ns)
 except FileNotFoundError:return None

def atomic_save(source,target):
 """Never truncate a previous destination while copying or on a failed write."""
 source=Path(source);target=Path(target)
 if not target.is_absolute()or target.suffix.lower()!='.mp4':raise ValueError('Chọn đường dẫn tuyệt đối tới tệp MP4.')
 if not target.parent.is_dir()or target.is_symlink():raise ValueError('Thư mục lưu không tồn tại hoặc tệp đích là liên kết.')
 if not source.is_file():raise ValueError('Tệp xuất tạm không còn. Bản đã tải trong khung xem vẫn có thể lưu bằng trình duyệt.')
 if target.exists()and os.path.samefile(source,target):return source.stat().st_size
 before=signature(target);temporary=None
 try:
  with source.open('rb')as reader,tempfile.NamedTemporaryFile(prefix='.SceneForge-',suffix='.tmp',dir=target.parent,delete=False)as writer:
   temporary=Path(writer.name);expected=os.fstat(reader.fileno()).st_size
   shutil.copyfileobj(reader,writer,1024*1024);writer.flush();os.fsync(writer.fileno())
   if writer.tell()!=expected:raise OSError('Tệp video chưa được sao chép đủ.')
  if signature(target)!=before:raise OSError('Tệp đích đã đổi trong lúc lưu. Chọn lại nơi lưu để tránh ghi đè nhầm.')
  os.replace(temporary,target);temporary=None
  return expected
 finally:
  if temporary is not None:temporary.unlink(missing_ok=True)

def install_export_save_as(app,resolve_file):
 lock=asyncio.Lock()
 @app.get('/local-api/export/save-capabilities')
 async def capabilities():return{'native_save_as':bool(powershell_path())}
 @app.post('/local-api/export/timeline/{id}/save-as')
 async def save_as(id:str,request:Request):
  if request.headers.get('X-SceneForge-Local')!='1':raise HTTPException(403,'Yêu cầu lưu phải đến từ ứng dụng trên máy.')
  origin=request.headers.get('Origin')
  if origin:
   parsed=urlsplit(origin)
   if parsed.scheme not in('http','https')or parsed.netloc!=request.url.netloc:raise HTTPException(403,'Nguồn yêu cầu lưu không hợp lệ.')
  raw=bytearray()
  async for chunk in request.stream():
   raw.extend(chunk)
   if len(raw)>4096:raise HTTPException(413,'Tên tệp quá dài.')
  try:body=json.loads(raw or b'{}')
  except ValueError:raise HTTPException(400,'Thông tin lưu không hợp lệ.')
  if not isinstance(body,dict)or set(body)-{'suggested_name'}:raise HTTPException(400,'Chỉ nhận tên gợi ý; thư mục phải được chọn trong hộp thoại.')
  if lock.locked():raise HTTPException(409,'Hộp thoại lưu đang mở. Hoàn tất hoặc hủy cửa sổ đó trước.')
  source=resolve_file(id)
  async with lock:
   target=await choose_windows_file(suggested_name(body.get('suggested_name')))
   if target is None:return{'state':'cancelled'}
   try:count=await asyncio.to_thread(atomic_save,source,target)
   except(OSError,ValueError)as error:raise HTTPException(400,'Chưa lưu được video: '+str(error))
   return{'state':'saved','path':str(target),'bytes':count,'name':target.name}
