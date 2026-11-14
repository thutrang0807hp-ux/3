"""Pinned source-only SDK update. Never starts a browser or provider request."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('omni_runtime',ROOT/'local_engine/flow_omni_runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
WHEEL=ROOT/'vendor/gflow_cli-0.98.0-py3-none-any.whl'

class RuntimeTests(unittest.TestCase):
    def fixture(self,root):
        site=root/'Lib/site-packages';(site/'gflow_cli').mkdir(parents=True)
        (site/'gflow_cli/cli_video.py').write_text('old cli')
        (site/'gflow_cli-0.92.1.dist-info').mkdir()
        (site/'dotenv').mkdir();(site/'dotenv/__init__.py').write_text('# dependency')
        (root/'profile-cookie-fixture').write_text('keep')
        return site

    def test_install_exact_sdk_without_copying_runtime_or_profiles(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);site=self.fixture(root)
            runtime.ensure_sdk(root,WHEEL)
            self.assertIn('omni-1.2-flash',(site/'gflow_cli/cli_video.py').read_text())
            self.assertFalse((site/'gflow_cli-0.92.1.dist-info').exists())
            self.assertEqual((root/'profile-cookie-fixture').read_text(),'keep')
            self.assertEqual((site/'dotenv/__init__.py').read_text(),'# dependency')
            before=(site/'gflow_cli/cli_video.py').stat().st_mtime_ns
            runtime.ensure_sdk(root,WHEEL)
            self.assertEqual(before,(site/'gflow_cli/cli_video.py').stat().st_mtime_ns)
            self.assertFalse((root/'.sceneforge-omni-install.lock').exists())

    def test_bad_checksum_keeps_old_sdk(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);site=self.fixture(root);bad=root/'bad.whl';bad.write_bytes(b'bad')
            with self.assertRaisesRegex(RuntimeError,'checksum'):runtime.ensure_sdk(root,bad)
            self.assertEqual((site/'gflow_cli/cli_video.py').read_text(),'old cli')

    def test_failed_commit_restores_previous_package_and_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);site=self.fixture(root)
            with patch.object(runtime.os,'replace',side_effect=OSError('fixture write failure')):
                with self.assertRaises(OSError):runtime.ensure_sdk(root,WHEEL)
            self.assertEqual((site/'gflow_cli/cli_video.py').read_text(),'old cli')
            self.assertTrue((site/'gflow_cli-0.92.1.dist-info').is_dir())
            self.assertFalse((site/'gflow_cli-0.98.0.dist-info').exists())

if __name__=='__main__':unittest.main()
