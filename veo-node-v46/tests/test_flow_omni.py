"""Omni admission and exact CLI routing; no provider calls or credits."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest

ROOT=Path(__file__).parents[1]/'local_engine'
PACKAGE='_omni_test'
package=types.ModuleType(PACKAGE);package.__path__=[str(ROOT)];sys.modules[PACKAGE]=package

def module(name):
    spec=importlib.util.spec_from_file_location(PACKAGE+'.'+name,ROOT/(name+'.py'))
    value=importlib.util.module_from_spec(spec);sys.modules[spec.name]=value;spec.loader.exec_module(value)
    return value

options=module('flow_video_options')
cli=module('flow_gflow_cli')

class OmniTests(unittest.TestCase):
    def test_exact_model_and_fixed_eight_seconds(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);src=root/'src/gflow_cli';src.mkdir(parents=True)
            (src/'cli_video.py').write_text('choices=["omni-1.2-flash"]; duration="--duration"')
            for mode in ('frames','ingredients'):
                for ratio,suffix in [('9:16','portrait'),('16:9','landscape')]:
                    cfg=dict(kind='video',mode=mode,ratio=ratio,model='omni-1.2-flash',outputs=1)
                    self.assertEqual(options.model_id(cfg),'omni-1.2-flash-i2v-8s-'+suffix)
                    args=cli.command(root,'start.png','--prompt text','project','output',settings=cfg)
                    self.assertEqual(args[args.index('--model')+1],'omni-1.2-flash')
                    self.assertEqual(args[args.index('--duration')+1],'8')
                    self.assertLess(args.index('--duration'),args.index('--'))
                    self.assertEqual(args[-1],'--prompt text')
                    self.assertEqual(args[4],'i2v' if mode=='frames' else 'r2v')

    def test_old_engine_and_unknown_models_blocked(self):
        with tempfile.TemporaryDirectory() as root:
            cfg=dict(kind='video',mode='frames',ratio='9:16',model='omni-1.2-flash',outputs=1)
            with self.assertRaisesRegex(ValueError,'chưa gửi'):
                cli.command(root,'start.png','prompt','project','output',settings=cfg)
            cfg['model']='omni'
            with self.assertRaises(ValueError):options.model_id(cfg)

    def test_legacy_settings_keep_identity(self):
        self.assertEqual(options.model_id(None),'veo-3.1-lite-i2v-8s-portrait')

if __name__=='__main__':unittest.main()
