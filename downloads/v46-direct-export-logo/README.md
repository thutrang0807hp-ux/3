# SceneForge v46.84 — Direct export and optional logo

Requires .83 or newer. Two HTML files only; installed runtime, native editor and models are preserved.

## Export correction

The .83 export button was disabled until the low-resolution joined preview existed, although final rendering uses original assets independently. Remove both the disabled-state prerequisite and early-return guard. Complete clips can export immediately; missing clips show a readable reason. Busy / logo-loading controls still prevent overlapping work. Strict source, voice, caption, cancellation and stale-result checks remain.

## Optional logo

PNG/JPEG/WebP up to 8 MiB / 16 million decoded pixels. The image asset and settings are saved with the project. Four corner presets plus horizontal/vertical position, width, opacity, optional opaque background and background color. A compact expandable section shows enabled state; enable/disable and remove are independent operations. Replaced/removed assets use existing reference-aware derived-asset cleanup.

A separate 1080×1920 transparent canvas previews the overlay without replacing video/caption DOM. Export uses the same aspect-preserving drawing function to produce a full-canvas PNG above captions. Logo settings changes invalidate the cached final. Missing logo assets cause a readable error rather than a silently unbranded export. No remote generation or upload is used.

This logo is applied in the node viewer and direct MP4 export. Existing native-editor timelines are not rewritten.

## Verification

Real Chromium + FastAPI timeline API + FFmpeg: direct 720p and 1080p H264/AAC exports with no 360p preview job; original cuts, voice, looping background music and custom captions retained. Compare actual logo and background pixels in decoded MP4; alpha/position controls on preview canvas; reopen, disable, re-enable and remove persisted logo; source/caption guards, cancel recovery and cached download; missing clip disables export with a reason. Buffered joins, live captions and shared-module/scale regressions passed. Embedded EXE sources and download checksum verified. Windows updater not run.

SHA256: e6ddcde95e5f2b6951380d9efe33c50c806e06efe6ae801b6120b091fceaaf24
