"""App startup must not spawn the optional legacy engine by default."""
import importlib.util,os,sys,tempfile,types
from pathlib import Path
from unittest.mock import Mock,patch

def main():
 source=Path(__file__).resolve().parents[1]/'scripts/windows-installer/windows_bootstrap.py'
 spec=importlib.util.spec_from_file_location('bootstrap_under_test',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);engine=root/'engines/flow2api';(engine/'venv/Scripts').mkdir(parents=True);(engine/'venv/Scripts/python.exe').touch();(engine/'installation.json').write_text('{}')
  paths=types.ModuleType('paths');paths.configure=lambda app:{'data_directory':str(root)}
  entry=types.ModuleType('local_engine.__main__');entry.main=Mock()
  before=Path.cwd()
  try:
   with patch.dict(sys.modules,{'paths':paths,'local_engine.__main__':entry}),patch.object(module,'browser'),patch.dict(os.environ,{'SCENEFORGE_LEGACY_FLOW_ENGINE':'0'}),patch('subprocess.Popen')as launch:
    module.main();launch.assert_not_called();entry.main.assert_called_once()
  finally:os.chdir(before)
 print('PASS lightweight startup: legacy engine installation exists but zero subprocesses are launched by default. No browser/engine executed.')
if __name__=='__main__':main()
