"""Rebuild this recovered release. No network, dependencies or cloud generation."""
from pathlib import Path
import re,json,runpy,hashlib
r=Path(__file__).resolve().parents[2];src=r/'scripts/recovered';dist=r/'dist/web-demo'
def expand(text):
 def include(m):
  path=(r/m.group(1)).resolve()
  if not path.is_relative_to(r):raise ValueError('Include outside project root')
  return path.read_text()
 return re.sub(r'/\* @sceneforge-include ([^*]+?) \*/',include,text)
for key,entry in json.loads((src/'pages.json').read_text()).items():
 html=(src/(key+'.html')).read_text()
 for ext in ['css','js']:html=html.replace('__RECOVERED_'+ext.upper()+'__',expand((src/(key+'.'+ext)).read_text()))
 p=dist/entry['output'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text(html)
(dist/'studio.html').write_bytes((dist/'index.html').read_bytes())
for helper in ['patch_notification_center.py','patch_workspace_shell.py','patch_batch_image_workspace.py','patch_recipe_workspace.py','patch_image_concurrency_settings.py','patch_video_intake.py','patch_recipe_v4.py','patch_audio_nodes.py','patch_reference_nodes.py','patch_photo_post_nodes.py','patch_media_nodes.py','patch_merge_export.py','patch_storyboard_modes.py','patch_photo_input_script.py','patch_prompt_pipeline.py']:runpy.run_path(str(r/'scripts/demo-web'/helper),run_name='__main__')
panel=(r/'scripts/shared/simple-flow-panel.js').read_text()
for name in ['index.html','studio.html','storage-demo.html','batch-design-demo.html','workflow.html','photos.html']:
 p=dist/name;s=p.read_text();s=s.replace('</body>','<script id="simple-flow-panel">'+panel+'</script></body>',1);p.write_text(s)
editor=hashlib.sha256((dist/'native/index.html').read_bytes()).hexdigest()[:12]
for name in ['index.html','studio.html','storage-demo.html','batch-design-demo.html']:
 p=dist/name;s=p.read_text();s=re.sub(r'native/index\.html\?v=[0-9a-f]+','native/index.html?v='+editor,s);p.write_text(s)
# Recompute frame keys after all patches, including media controls/prompt pipeline.
for entry in ['workflow.html','photos.html']:
 digest=hashlib.sha256((dist/entry).read_bytes()).hexdigest()[:12]
 for name in ['index.html','studio.html','storage-demo.html','batch-design-demo.html']:
  p=dist/name;s=p.read_text();s=re.sub(re.escape(entry)+r'\?v=[0-9a-f]+',entry+'?v='+digest,s);p.write_text(s)
print('Built editable production pages; refreshed cache keys and isolated preview overlays.')
