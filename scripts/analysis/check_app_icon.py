"""Real ICO assets and ownership boundary for the optional Windows branding worker."""
import importlib.util,json
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[2]
path=root/'veo-node-v46/local_engine/desktop_icon.py'
spec=importlib.util.spec_from_file_location('desktop_icon',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
icon=root/'icons/SceneForge.ico';image=Image.open(icon)
required={16,20,24,32,40,48,64,128,256};assert {w for w,h in image.ico.sizes()if w==h}==required
for size in required:
 frame=image.ico.getimage((size,size)).convert('RGBA');assert frame.getpixel((0,0))[3]<100
 pixels=list(frame.get_flattened_data());assert any(g>150 and r>100 and b<140 and a>200 for r,g,b,a in pixels),(size,'lime mark missing')
class Fake:
 def __init__(self,pid=123,path='/install/SceneForge.exe'):self.pid=pid;self.path=path
 def window_pid(self,hwnd):return self.pid if hwnd==567 else 0
 def process_path(self,pid):return self.path
state={'pid':123,'window':567}
assert module.owned_window(state,'/install/SceneForge.exe',Fake())==567
assert module.owned_window(state,'/install/SceneForge.exe',Fake(pid=124))is None
assert module.owned_window(state,'/install/SceneForge.exe',Fake(path='/other/SceneForge.exe'))is None
assert module.owned_window({'pid':123,'window':0},'/install/SceneForge.exe',Fake())is None
assert module.owned_window({},'/install/SceneForge.exe',Fake())is None
assert module.install_desktop_icon('/tmp','/tmp')is None
for filename in ['index.html','studio.html','workflow.html','photos.html']:
 assert 'rel="icon" type="image/x-icon" href="./icons/SceneForge.ico"'in(root/filename).read_text()
print('PASS ICO 16–256px transparency/mark; favicon paths; stale PID/foreign installation rejected; Linux startup stays unchanged')
