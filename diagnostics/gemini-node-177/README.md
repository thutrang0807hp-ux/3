# .177: original Node/CDP connector, not a Python translation

User report: Gemini creates images, but only some requests return to SceneForge. The upstream test app returns images. This release replaces the .175 Python implementation with the actual `gemini-try-on/runtime/gemini.mjs` implementation from thutrang0807hp-ux/test-gemoni-chat commit 75f43c9.

`veo-node-v46/scripts/gemini-native/upstream-gemini.mjs` is the untouched upstream snapshot. The adapted `gemini.mjs` retains these ten functions byte-for-byte: imageSource, imageInstruction, editorFor, submit, waitForText, waitForImage, downloadImage, downloadFromGemini, copyImagePixels, saveResult. Send/find/download selectors, timeout values and three download fallbacks are not rewritten. Runtime uses the upstream exact playwright-core 1.62.1 plus official Windows Node 22 LTS. Node/CDP connects to ordinary Chrome launched with the same separate-profile/headless flags as upstream. Python only starts the process, queues jobs and imports result files.

SceneForge additions are isolated to attachment upload, raw text task dispatch, and request-specific durable receipts. Receipts store the Chrome target ID and response index before a send. Successful turns clear their page as upstream does. Failed downloads keep their exact page for receive-only retries; subsequent tasks use a blank/new page, not a failed turn. Completed bytes are cached until the production ledger commits them. Cache/receipt cleanup follows successful commit. Missing targets never cause a new generation.

A reproduced integration bug was fixed: native receive_image previously started a receiver but returned the old unknown/error state, causing the UI polling loop to stop. It now returns downloading while that receiver runs, displays a receiving message instead of the stale error, and clears the active flag when finished. Phase names are included in failed native status for diagnosis.

Checks:
- check_original_gemini_node.py compares all ten functions against the saved upstream and verifies the runtime checksum/dependency version.
- check_gemini_node_cdp_e2e.py runs the actual Node connector against actual Popen headless Chrome/CDP and the production service/ledger, with a fixture Gemini page. It tests queued work, two accounts in parallel, exact per-request images and input reference bytes, >20k-character prompts, closing an unrelated browser during work, a download failure followed by another successful request, then receive-only recovery of the failed request with no extra send. Completed cache files are retired.
- Native sign-in UI and legacy extension tests remain supported; V6, image node, logo tool and model/API choices are unchanged.

This does not establish a single root cause for every failure on the user's machine. No live Google account generation or Windows sign-in has been run here. Older Python-port jobs have no durable target receipt; they are not silently rebound to an arbitrary conversation or regenerated. Their existing images can be downloaded/imported manually if needed. Newly submitted jobs use the Node runtime and durable receipts.

The runtime is distributed as a checksum-pinned archive; no npm install, Node install or Chromium download runs on the user's computer. It unpacks locally on first use. Component licenses are included. Build inputs are pinned by package_gemini_node_runtime.py and gemini-native-node.json.
