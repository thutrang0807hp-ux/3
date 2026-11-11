# Inline assembly clip order · v46.119

The assembly viewer now mounts a compact Thứ tự clip card at the top of the Ghép panel. It has numbered thumbnails, drag and drop, up/down controls, a staged draft, Reset and Apply. The old header link is removed. Applying closes and reopens the viewer through existing cleanup; playback restarts. Existing outer-node ordering remains available.

The .117 shared ordering path still maps captions and separate voice segments, preserves original scenes and supports undo. No generation request is added.

Validation: check_merge_order.py passed with actual generated MP4/WAV fixtures in Chromium. Covers draft isolation until Apply, reopened viewer order, header removal, node refresh, drag, keyboard, persistence, undo, caption and audio mapping and crossing-boundary word conservation. Windows installer and backend final MP4 rendering were not executed.

Package: `downloads/v46-inline-merge-order/SceneForge-Update-20261111-v46.119-Inline-Merge-Order.exe`

SHA-256: `9f2942d9c7783b19d66db93891a359a7dd17067c1811269713dc8700d5e6bec2`
