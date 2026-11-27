"""Actual workflow create -> SimpleFlow ledger -> original CLI process contract -> video import.
Provider is an isolated child-process double. No Google or paid requests.
"""
import asyncio,base64,io,json,sys,tempfile,shutil,zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
from contextlib import ExitStack
from PIL import Image
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
# The repository stores unchanged engine dependencies in its v46 source archive.
_deps=tempfile.TemporaryDirectory(prefix='sf-cli-e2e-')
with zipfile.ZipFile(ROOT/'downloads/v46/SceneForge-Veo-v46-Source.zip')as archive:
 for name in archive.namelist():
  if name.startswith('local_engine/') and name.endswith('.py') and '..' not in Path(name).parts:
   target=Path(_deps.name)/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(name))
shutil.copytree(ROOT/'veo-node-v46/local_engine',Path(_deps.name)/'local_engine',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
sys.path.insert(0,_deps.name)
from local_engine.simple_flow import SimpleFlow
from local_engine.request_ledger import RequestLedger
FIXTURE=r'''
import sys,json,pathlib,shutil,hashlib
args=sys.argv[1:]
assert args[:3]==['-m','gflow_cli','video'],args
assert args[3] in ('r2v','i2v')
assert '--project' not in args and '--project-name' in args
assert args[args.index('--profile')+1]=='fixture'
expected=json.loads(pathlib.Path('expected.json').read_text())
ref=pathlib.Path(args[args.index('--ref')+1] if args[3]=='r2v' else args[args.index('--')+1])
assert hashlib.sha256(ref.read_bytes()).hexdigest()==expected['hash']
assert args[-1]==expected['prompt']
with pathlib.Path('calls').open('a') as f:f.write('generate\n')
project='11111111-1111-4111-8111-111111111111';media='22222222-2222-4222-8222-222222222222'
for value in [dict(event='migrated.dispatch',project_id=project),dict(event='migrated.submit_observed',media_id=media,status=6),dict(event='migrated.status',status=3)]:
 print(json.dumps(dict(level='info',**value)),file=sys.stderr,flush=True)
out=pathlib.Path(args[args.index('--out-dir')+1])/'video.mp4';shutil.copyfile('fixture.mp4',out)
print(json.dumps(dict(command='video '+args[3],status='ok',succeeded=True,media_id=media,local_path=str(out))))
'''
async def main(mode):
 with tempfile.TemporaryDirectory() as folder,ExitStack() as stack:
  root=Path(folder);repo=root/'runtime';repo.mkdir();(repo/'python.exe').touch();(repo/'fixture_cli.py').write_text(FIXTURE)
  # Real media artifact; provider generation itself is simulated.
  import subprocess
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=180x320:d=8','-c:v','libx264','-pix_fmt','yuv420p',str(repo/'fixture.mp4')],check=True)
  import zipfile
  (repo/'gflow_cli').mkdir()
  with zipfile.ZipFile(ROOT/'veo-node-v46/vendor/gflow_cli-0.98.0-py3-none-any.whl')as wheel:(repo/'gflow_cli/cli_video.py').write_bytes(wheel.read('gflow_cli/cli_video.py'))
  binding={'email':'fixture@example.com','profile_key':None,'account_id':'account'}
  status={'installed':True,'enabled':True,'native_pipeline':True,'selection':{'available':True,'account_id':'account','token':'fixture'},'unresolved':[],'accounts':[],'logs':[]}
  vault=SimpleNamespace(secret=lambda key:None,set_secret=lambda *a:None)
  service=SimpleFlow(root,vault,RequestLedger(root));service.cli_driver_enabled=True;service.native_pipeline_enabled=True
  service.account_bridge=SimpleNamespace(background=True,selection=lambda:status['selection'],binding=lambda aid:binding)
  service.restore=AsyncMock(side_effect=AssertionError('SceneForge browser preflight used'))
  service.capture_preview=AsyncMock()
  stack.enter_context(patch('local_engine.flow_cli_bundle.bundled_runtime',return_value=repo))
  stack.enter_context(patch('local_engine.flow_cli_bundle.prepare_profile',return_value=(root/'profiles','fixture')))
  stack.enter_context(patch('local_engine.flow_native_pipeline.ensure_native_project',AsyncMock(side_effect=AssertionError('RPC preflight used'))))
  original=asyncio.create_subprocess_exec
  async def launch(*args,**kwargs):
   if args[1:3]!=('-m','gflow_cli'):return await original(*args,**kwargs)
   return await original(sys.executable,str(repo/'fixture_cli.py'),*args[1:],**kwargs)
  stack.enter_context(patch.object(asyncio,'create_subprocess_exec',launch))
  html=(ROOT/'workflow.html').read_text().replace('<script id="frame-studio-node">','<script>if(!project)project=blankProject();</script><script id="frame-studio-node">')
  image=io.BytesIO();Image.new('RGB',(180,320),'#254a59').save(image,'PNG');raw=image.getvalue();uri='data:image/png;base64,'+base64.b64encode(raw).decode()
  posts=[]
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page();page.on('dialog',lambda d:d.accept())
   async def route(r):
    url=r.request.url
    if '/local-api/' in url:
     if url.endswith('/flow/simple/jobs') and r.request.method=='POST':
      body=r.request.post_data_json;posts.append(body)
      import hashlib
      (repo/'expected.json').write_text(json.dumps({'hash':hashlib.sha256(base64.b64decode(body['references'][0]['data'])).hexdigest(),'prompt':body['prompt']}))
      result=await service.submit(body);await r.fulfill(json=result);return
     if '/flow/simple/jobs/'in url:
      await r.fulfill(json=service.lookup(url.rsplit('/',1)[-1]));return
     if '/flow/simple/files/'in url:
      record=service.lookup(url.rsplit('/',1)[-1]);assert record['state']=='done'
      path=service.root/record['result']['file'];await r.fulfill(body=path.read_bytes(),content_type='video/mp4');return
     await r.fulfill(json=status);return
    await r.fulfill(body=html,content_type='text/html')
   await page.route('**/*',route);await page.goto('http://127.0.0.1/workflow.html');await page.wait_for_function('window.SFVeoNode&&project')
   await page.evaluate('''async image=>{
    storeProject=async()=>{};save=()=>{};SFProviderReceipts.persistIntent=async()=>{};
    project=blankProject();project.id='room';project.source={poster:image};project.analysis.frameQualityRequired=false;
    project.script=[{id:'line',start:0,end:2.8,newText:'Lời mới của sản phẩm.'}];
    const blob=await(await fetch(image)).blob();assets.set('frame',blob);
    const s=sceneRecord(0,2.8,0,[image]);s.hasPerson=false;s.refsUsed=[];
    s.motion.en={camera:'Fixed camera',initial:'Hold still',action:'Rotate gently',final:'Hold still'};
    s.frames=[{id:'approved',asset:'frame',image,status:'approved'}];s.approvedFrame='approved';s.frameSelectionId='approved';project.scenes=[s];
    await SFVeoNode.refresh();SFVeoNode.openClipDetail(SFVeoNode.slots()[0]);
   }''',uri)
   if mode=='ingredients':await page.evaluate("project.veoNode.flowSettings={kind:'video',mode:'ingredients',ratio:'9:16',model:'lite',outputs:1};SFVeoNode.openClipDetail(SFVeoNode.slots()[0]);")
   await expect(page.locator('#vnDetail [data-vn=create]')).to_be_enabled()
   await page.locator('#vnDetail [data-vn=create]').click()
   for _ in range(150):
    await asyncio.sleep(.1)
    if posts and service.lookup(posts[0]['request_id'])['state']in ('done','failed','unknown'):break
   assert len(posts)==1,posts
   if service.task:await service.task
   result=service.lookup(posts[0]['request_id']);assert result['state']=='done',result
   assert result['result']['scene_id']==posts[0]['scene_id']
   try:await page.wait_for_function("project.scenes.some(s=>s.clips?.length)",timeout=15000)
   except Exception:
    print(await page.evaluate("({jobs:project.cloudJobs,text:document.querySelector('#vnDetail')?.innerText})"));raise
   service.restore.assert_not_called()
   assert (repo/'calls').read_text().splitlines()==['generate']
   duplicate=await service.submit(posts[0]);assert duplicate['state']=='done'
   assert (repo/'calls').read_text().splitlines()==['generate']
   await browser.close()
 print('PASS real Create click -> ledger -> child CLI -> actual MP4/ffprobe -> imported scene; one send, duplicate no resend; no SceneForge browser/RPC preflight; provider simulated')
asyncio.run(main(sys.argv[1] if len(sys.argv)>1 else 'frames'))
