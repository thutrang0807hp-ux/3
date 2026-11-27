# SceneForge v46.182: ordered references from working Gemini 0.4.11

Baseline user repository af0c748 (0.4.11); multiple-reference extension b5ed789 (0.4.12). Preserve the ten original send/read/download helpers. Native runtime now uses that uploader with an ordered path list; no legacy DOM sender, image-mode override or custom result selector. SceneForge maps its prepared base64 references to temporary files in exactly the order used by V6 bindings. Existing account profile leases, queue, cached-result import and cleanup remain.

No changes to frame prompt/editor, progress, output sizes, watermark button, common requests or per-scene reference controls. Existing limit is eight references per request. No model/API changes.

Validation: actual production SceneForge queue + Chromium/CDP with five distinct references, >20k V6 prompt, exact file order/content, two-account parallel and same-account sequential runs, result handling, failed download without resend, cache-only recovery, next request success, page-open failure phase, full packaged EXE payload equality and checksum. Provider pages are fixtures; no live Google generation or native Windows SceneForge UI check claimed. Standalone 0.4.12 additionally runs browser roundtrip and Python multi-reference checks in Windows CI.
