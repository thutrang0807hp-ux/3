"""Compatibility entry point: the Python port has been replaced with original Node/CDP."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('check_gemini_node_cdp_e2e.py')),run_name='__main__')
