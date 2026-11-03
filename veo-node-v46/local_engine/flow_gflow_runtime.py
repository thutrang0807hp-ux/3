"""Private pinned Windows runtime; no pip, shell commands or extra application."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import urllib.request
import zipfile

REVISION = '09ab05b190ddad0b3bbed80439ecbc6739d5abce'
ARCHIVE_SHA256 = '03ae9541fefa55e4f917f87db794cd2b26f61d5d215a754b333b5dfc3d686292'
ARCHIVE_URL = ('https://raw.githubusercontent.com/thutrang0807hp-ux/5gdfgfd/'
               + REVISION + '/GFlow-Studio-Portable-Windows.zip')
PREFIX = 'GFlow-Studio-Portable/runtime/'


def ensure_runtime(data, archive=None):
    """Run off the event loop. Verify whole archive before extracting runtime only."""
    root = Path(data) / 'flow-engine' / ARCHIVE_SHA256[:16]
    python = root / 'python.exe'
    stamp = root / 'sceneforge-runtime.json'
    if python.is_file() and stamp.is_file():
        if json.loads(stamp.read_text()) == {'archive_sha256': ARCHIVE_SHA256}:
            return python
    root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='flow-engine-', dir=root.parent) as folder:
        stage = Path(folder)
        source = Path(archive) if archive else stage / 'engine.zip'
        if archive is None:
            with urllib.request.urlopen(ARCHIVE_URL, timeout=120) as response, source.open('wb') as target:
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > 100 * 1024**2:
                        raise ValueError('engine_archive_size')
                    target.write(chunk)
        with source.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != ARCHIVE_SHA256:
            raise ValueError('engine_archive_checksum')
        runtime = stage / 'runtime'
        runtime.mkdir()
        with zipfile.ZipFile(source) as bundle:
            entries = [entry for entry in bundle.infolist() if entry.filename.startswith(PREFIX)]
            if sum(entry.file_size for entry in entries) > 600 * 1024**2:
                raise ValueError('engine_runtime_size')
            for entry in entries:
                name = PurePosixPath(entry.filename[len(PREFIX):])
                if not name.parts:
                    continue
                if name.is_absolute() or '..' in name.parts or '\\' in str(name) or ':' in str(name):
                    raise ValueError('engine_archive_path')
                target = runtime.joinpath(*name.parts)
                if entry.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with bundle.open(entry) as source_file, target.open('wb') as output:
                        shutil.copyfileobj(source_file, output)
        if not (runtime / 'python.exe').is_file() or not (runtime / 'Lib/site-packages/gflow_cli/__init__.py').is_file():
            raise ValueError('engine_runtime_incomplete')
        (runtime / stamp.name).write_text(json.dumps({'archive_sha256': ARCHIVE_SHA256}))
        if root.exists():
            raise ValueError('engine_existing_runtime_incomplete')
        runtime.replace(root)
    return python
