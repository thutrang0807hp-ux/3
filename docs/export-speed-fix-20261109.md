# SceneForge v46.85 — Export compatibility, inline caption review and whole-video speed

Requires .84 or newer. Payload: workflow.html, photos.html, local_engine/timeline_export.py. Preserve installed voice/Flow runtimes, models, native editor and source assets.

## Confirmed failures and corrections

1. User screenshot: FFmpeg rejected filter_complex_script. Renderer now prefers modern -/filter_complex and falls back to legacy -filter_complex_script only on an explicit unrecognized-option error. Supported file mode is cached by executable. Encoding/filter/codec failures are not retried. Both forms keep filter graphs out of the Windows command-line length limit.
2. Caption preflight rejected a stale draft but left the user outside the review flow. The viewer now exposes editable raw text/start/end cues and an explicit reviewed confirmation that stamps current signatures, preserving manual text and timing. A one-off no-caption export skips only caption inclusion/its stale guard and leaves the project draft and stale status unchanged. Native-editor handoff guards remain.
3. Preview speed did not affect output. New persisted Final speed presets (0.5, 0.75, 1, 1.25, 1.5, 2, 3) retime all video/audio intervals and image layers together. Source offsets and authored cues remain in original time. Audio uses pitch-preserving tempo. The viewer rate follows a final-rate change; independent preview-rate changes do not alter final speed.
4. Actual accelerated-export test exposed a dark frame just before a fractional join. FFmpeg visual filters retain one hidden guard frame past the enabled interval, keeping EOF repetition off; an epsilon at interval boundaries avoids floating-point gaps. The enable expression still ends the visible layer at the cut. Decoded-frame regression now passes across that boundary.
5. Cached final MP4 checks context and caption inclusion mode. Source/settings changes cannot silently reuse a stale or no-caption final. Controls recover after validation errors/cancel.

Caption and logo images are quantized to the output 30fps grid after speed mapping. Duration covers all output layers. Logo position/opacity/background and direct export from original sources remain.

## Validation

- Actual MP4 using patched exporter with modern-only and legacy-only option shims, paths with spaces, supported-mode caching, and a deliberately failing filter graph (one attempt only).
- Chromium + actual FFmpeg: inline review retains edited uppercase text/end mark; one-off no-caption output preserves saved captions/stale state and retains logo; a later normal export does not reuse the no-caption cache.
- Actual 720p 1.5x and 1080p 0.5x MP4s, expected durations and retimed voice offsets, looping music, colored caption pixels and logo/background pixels. Background music remains about 880Hz at 1.5x, verifying pitch preservation. Frame checks straddle the previously dark fractional cut. Cancel/download-again and logo persistence/remove regressions pass.
- Existing direct-export/logo, live-caption and shared-module/scale regressions pass. EXE payload bytes and download checksum verified. Windows updater not run.

Original exporter baseline SHA256: d27c6852775acdc4f5e19560ab03d687ed210a1f7934db88f690e4960f278b8e
Release SHA256: 9cdc394e41e693c2d64f43cf740da8aa42a468452a11f95f1f30801da8504d0f
