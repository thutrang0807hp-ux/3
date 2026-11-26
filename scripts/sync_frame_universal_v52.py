"""Sync the canonical user template into the browser module and its existing HTML script slot."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'scripts/prompts/universal_reference_image_edit_v5_2.md').read_text()
module=ROOT/'scripts/ui/frame_universal_v52.js'
text=module.read_text();start=text.index(' const TEMPLATE=');end=text.index('\n',start)
text=text[:start]+' const TEMPLATE='+json.dumps(source,ensure_ascii=False)+';'+text[end:]
module.write_text(text)
page=ROOT/'workflow.html';html=page.read_text();marker='<script id="frame-universal-v51">';start=html.index(marker)+len(marker);end=html.index('</script>',start)
page.write_text(html[:start]+text+html[end:])
print('Synced V5.2 template; run check_frame_universal_v52.js and check_frame_studio_contract.py.')
