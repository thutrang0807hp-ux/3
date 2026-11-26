# .176 local visible Gemini logo processing

Frame result toolbar: `Xóa logo Gemini`, next to `Mở ảnh lớn`. Full original PNG/JPEG/WebP assets are required; thumbnails are never substituted. The action calls a local processing endpoint, creates a pending frame version, selects it for review and retains the original frame/asset in history. An indeterminate indicator is shown while processing. Repeated clicks and already-processed copies are blocked; selecting an original with an existing processed version reuses that version.

Fixed Windows x64 GeminiWatermarkTool v0.3.2 from allenk/GeminiWatermarkTool, the same release used by test-gemoni-chat 75f43c9. Archive SHA256: 1c6734a6503ee6e34a424e8bf6c8db2db18e2afb286cb0c8622b8a1015abb6eb. Binary checksum/provenance and MIT license are bundled. No runtime download, Gemini call or new Python dependency.

Endpoint: POST /local-api/gemini-chat/remove-watermark, {image: base64}. The wrapper validates format/size, converts to a temporary PNG, runs the bundled tool with a 30s timeout, requires matching dimensions and valid PNG output, then removes temporary files. Exit code 1 returns `changed:false`. Tool errors/timeouts leave the original untouched. Input/output limits match the existing full-frame importer: 15 MiB and 16 MP, max edge 8192.

Checks:
- check_gemini_watermark.py executes the actual wrapper with controlled CLI outputs: dimensions, unchanged original bytes, no logo, invalid input, tool failure, timeout and invalid output.
- check_watermark_ui.py executes the actual frame node in Chromium: exact original bytes passed once to the local endpoint; new frame selected but not auto-approved; original frame/asset retained; duplicate clicks do not create more calls; no Gemini generation request.
- Updated package verifies every embedded file, tool checksum and prior .175 transport/prompt preservation.

The Windows executable is checksum-verified and packaged, but was not executed on Windows in this environment. Real-logo detection/removal quality is delegated to the pinned upstream tool, not claimed as a live test here.
