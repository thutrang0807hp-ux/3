# .180: real submit, acknowledgement, image mode and text-only replies

User evidence: app said "Đã gửi nhưng chưa thấy phản hồi mới" while Gemini history had no new prompt/reference request. Another visible response explicitly said the image tool was unavailable and returned text. A DOM HTMLElement.click() call is not acknowledgement that Gemini accepted a request.

Keep the existing DataTransfer attachment block. Remove DOM prompt insertion/HTMLElement.click from scene-send.js. Use the upstream submit() function's browser fill and trusted click instead. This replaces any stale editor draft, waits for a usable send control, and then requires a new user-query or assistant reply before proceeding. If no new turn appears within 30s, the error says the request was not confirmed, never "Đã gửi". No automatic resend.

For image jobs only, check the Tools menu when available and select Create images if offered. Never click upgrades or change model/account. Missing optional menu entries retain natural-language creation; disabled image mode fails before prompt submission. All mode-selection errors are distinguished from submission errors.

Upstream image read/download functions remain byte-for-byte. A separate observer detects stable explicit image-tool-unavailable/prompt-only text with no image and no active stop control, reporting that situation rather than waiting for an image timeout. Normal image generation continues through the upstream receiver. The scene editor and V6 prompt are untouched.

Validation uses real headless Chromium/CDP and the production adapter/ledger against a fixture Gemini page. Its Send handler ignores untrusted clicks, its editor starts with a stale draft, its Tools menu requires image mode selection, and its uploads use the previously unsupported custom preview shape. Successful jobs use trusted submission with the exact new prompt and reference bytes; repeated/simultaneous jobs return their own images. Explicit Vietnamese text-only refusal is reported; a click producing no turn reports unconfirmed submission, without resending. The test fixture has an explicit UTF-8 declaration so Vietnamese refusal matching is actually exercised.

This does not prove that Gemini's real page enforces isTrusted, nor identify every cause on the user's machine. Windows and real Google-account generation are not available here. It fixes the reproduced integration defects and provides accurate failure states; live verification remains necessary. Existing failed jobs are retained and are not silently regenerated.
