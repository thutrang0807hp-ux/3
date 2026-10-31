"""Bundled-Python entry; no core pip installation/download during ordinary startup."""
import os,sys,subprocess
from pathlib import Path

def browser():
    if os.environ.get('SCENEFORGE_BROWSER'):return
    for root in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'):
        base=os.environ.get(root)
        if not base:continue
        for relative in ('Google/Chrome/Application/chrome.exe','Microsoft/Edge/Application/msedge.exe'):
            candidate=Path(base)/relative
            if candidate.is_file():
                os.environ['SCENEFORGE_BROWSER']=str(candidate);return

def main():
    app=Path(__file__).resolve().parent
    os.chdir(app)
    if str(app)not in sys.path:sys.path.insert(0,str(app))
    from paths import configure
    cfg=configure(app)
    browser()
    os.environ['SCENEFORGE_OPEN_BROWSER']='0'if os.environ.get('SCENEFORGE_NO_BROWSER')=='1'else'1'
    # Engine source/configuration is prepared offline by setup; only start the owned loopback service.
    flow=None
    if cfg and os.environ.get('SCENEFORGE_LEGACY_FLOW_ENGINE')=='1':
        engine=Path(cfg['data_directory'])/'engines/flow2api';python=engine/'venv/Scripts/python.exe'
        if python.is_file()and(engine/'installation.json').is_file():
            import socket,atexit
            with socket.socket()as probe:occupied=probe.connect_ex(('127.0.0.1',8766))==0
            if not occupied:
                log=(Path(cfg['data_directory'])/'flow-startup.log').open('ab')
                flowenv={**os.environ}
                if os.environ.get('SCENEFORGE_DESKTOP')=='1':flowenv['SCENEFORGE_FLOW_QUIET_START']='1'
                if os.environ.get('SCENEFORGE_BROWSER'):flowenv.setdefault('BROWSER_EXECUTABLE_PATH',os.environ['SCENEFORGE_BROWSER'])
                flow=subprocess.Popen([str(python),str(app/'local_engine/flow_account_engine.py'),'--source',str(engine/'source')],cwd=engine/'source',stdout=log,stderr=log,env=flowenv,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                atexit.register(lambda:flow.terminate()if flow.poll()is None else None)
    from local_engine.__main__ import main as run
    run()

if __name__=='__main__':main()
