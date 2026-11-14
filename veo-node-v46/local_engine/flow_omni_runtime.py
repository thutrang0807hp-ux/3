"""Upgrade only the private CLI package; preserve browsers, dependencies and profiles."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import threading
import zipfile

WHEEL_SHA256='f35eedf1e167e5cf5e2837ad2a7d3455f1bc1c205b22ea98a350f3dbaebb77d3'
VERSION='0.98.0'
_LOCK=threading.Lock()


def ensure_sdk(runtime, wheel):
    runtime=Path(runtime)
    wheel=Path(wheel)
    site=runtime/'Lib/site-packages'
    stamp=runtime/'sceneforge-omni-sdk.json'
    expected={'version':VERSION,'wheel_sha256':WHEEL_SHA256}
    with _LOCK:
        try:
            if json.loads(stamp.read_text())==expected and (site/'gflow_cli/cli_video.py').is_file():
                return runtime
        except (OSError,ValueError):pass
        if not (site/'dotenv/__init__.py').is_file():
            raise RuntimeError('Runtime Flow thiếu phụ thuộc dotenv; cần cài lại runtime đầy đủ. Chưa gửi tạo video.')
        if not wheel.is_file() or hashlib.sha256(wheel.read_bytes()).hexdigest()!=WHEEL_SHA256:
            raise RuntimeError('Gói Omni CLI bị thiếu hoặc sai checksum. Chưa gửi tạo video.')
        # Another app process must not mutate this same private runtime concurrently.
        lock=runtime/'.sceneforge-omni-install.lock'
        try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        except FileExistsError:
            raise RuntimeError('Runtime Flow đang được cập nhật hoặc còn khóa từ lượt lỗi; chưa gửi tạo video.') from None
        os.close(fd)
        try:
            with tempfile.TemporaryDirectory(prefix='.sf-omni-',dir=site) as folder:
                stage=Path(folder);incoming=stage/'incoming';incoming.mkdir()
                with zipfile.ZipFile(wheel) as bundle:
                    entries=bundle.infolist()
                    if sum(e.file_size for e in entries)>30*1024**2:raise RuntimeError('Gói Omni vượt giới hạn.')
                    for entry in entries:
                        name=PurePosixPath(entry.filename)
                        if (name.is_absolute() or '..' in name.parts or '\\' in entry.filename
                                or ':' in entry.filename or not name.parts
                                or name.parts[0] not in ('gflow_cli','gflow_cli-0.98.0.dist-info')
                                or entry.external_attr>>16 & 0o170000 == 0o120000):
                            raise RuntimeError('Đường dẫn gói Omni không hợp lệ.')
                        target=incoming.joinpath(*name.parts)
                        if entry.is_dir():target.mkdir(parents=True,exist_ok=True)
                        else:
                            target.parent.mkdir(parents=True,exist_ok=True)
                            with bundle.open(entry) as source,target.open('wb') as output:shutil.copyfileobj(source,output)
                if not (incoming/'gflow_cli/cli_video.py').is_file():raise RuntimeError('Thiếu CLI Omni.')
                previous=stage/'previous';previous.mkdir();moved=[];installed=[]
                try:
                    for old in [site/'gflow_cli',*site.glob('gflow_cli-*.dist-info')]:
                        if old.exists():old.rename(previous/old.name);moved.append(old.name)
                    for item in incoming.iterdir():item.rename(site/item.name);installed.append(item.name)
                    pending=stage/'stamp.json';pending.write_text(json.dumps(expected),encoding='utf-8');os.replace(pending,stamp)
                except BaseException:
                    for name in installed:
                        path=site/name
                        if path.is_dir():shutil.rmtree(path)
                    for name in moved:(previous/name).rename(site/name)
                    raise
            return runtime
        finally:lock.unlink(missing_ok=True)
