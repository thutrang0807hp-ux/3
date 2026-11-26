# .178: direct upstream workspace, unchanged scene editor

Explicit user scope: retain the per-scene prompt editor, progress bar, visible Gemini logo removal, output dimensions, common edits and reference controls; replace the transport underneath.

The .177 custom page selection/receipts were removed. `upstream-browser-bridge.py` is byte-for-byte from test-gemoni-chat commit 75f43c93a5670acc65ce1411ffb2ea298db348f0 (SHA256 a861ddfc4ec841fcbac0adccde9b779bece38caa2ee3327e57bbaf40a71592fa). SceneForge instantiates its GeminiWorkspace, maps its profile to the existing account-owned profile and calls its original start/verify/request/create_image/close. The only subclass hook adds the current source/reference list to the request. Original normal sign-in and profile ownership UI remain.

The entire Node run() path, including blank-tab choice, submit, response choice, download and final page cleanup, equals upstream after removing exactly two inserts: reference attachment and the raw-text action needed for existing scene analysis/prompt tasks. Original main() and all ten send/read/download functions are unchanged. No custom target matching or receiveExisting is used. Runtime remains pinned to playwright-core 1.62.1 and official Node 22.23.5, with included licenses.

Existing UI files and V6 prompt are unchanged byte-for-byte from .177: index.html, workflow.html, frame_studio_node.js, frame_universal_v60.js, frame_settings.js, frame_image_flow.js. Logo processing and all previous runtime payloads are preserved.

Upstream error behavior is preserved: the page is reset after a request, including failed downloads. SceneForge does not fabricate a receipt or silently re-run a failed request. Receive-only import works when an actual completed file is cached; otherwise the endpoint says there is no file available and does not submit a generation. Original upstream error text is surfaced in native status. Provider calls run on a thread so the existing UI progress/polling loop remains responsive.

Validation: check_original_gemini_node.py verifies whole run() equivalence, all ten source functions, original Python workspace bytes and runtime pinning. check_gemini_node_cdp_e2e.py exercises the actual upstream Python workspace and Node CLI against real headless Chrome/CDP with a fixture Gemini website: two accounts concurrently; repeated scenes on one account; >20k prompt and exact reference bytes; closing unrelated Chrome; a failed download followed by a successful request; no implicit generation on receive; cached completed-file import. Existing scene UI, V6 and logo tests remain.

No Windows Google login or real Gemini generation was performed here. This is a faithful integration plus fixture validation, not a claim that every timeout on the user's machine has been reproduced or fixed.
