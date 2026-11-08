# SceneForge .76 — live caption style controls

Requires .75. Close app, apply updater, open Phụ đề → Xem video & phụ đề. Kiểu chữ controls now live inside the player. Existing node controls use the same fast path. UI-only workflow/photos payload; no model/runtime change.

Style selection bypasses the generic global-busy/await-store/render cycle. It updates post style, selected/aria-pressed buttons and thumbnail class, redraws the existing overlay canvas immediately, then uses existing debounced autosave. No video source/player/canvas/scene DOM replacement. The playing/paused state and seek time remain intact. Choosing TikTok no longer silently overwrites the user's size with 88; font size, position and word limit remain unchanged. Re-selecting current style does no work. Shared caption renderer/export pipeline still reads saved style; existing room/flush persistence remains. Fonts-ready redraw prevents an early interaction from leaving fallback-font pixels cached.

Validation: check_caption_video_viewer_ui.py now deliberately blocks storeProject promises while rapidly choosing all styles in real MP4 playback. Verifies canvas pixels/color/background updates, 900-weight request for TikTok (fixture font may map 700/900 glyphs alike), same video/canvas/frame elements, no busy lock, ongoing playback, paused immediate redraw without seek, size/position preserved. Tests node buttons during pending saves and photo-mode selected style in export payload. Caption-scale and independent voice picker regressions passed. This is Chromium fixture evidence; Windows updater not executed.

EXE: SceneForge-Update-20261108-v46.76-Live-Caption-Style.exe
SHA256: 16aa535ca2cd44aaf1883179791da1da121353d6f3e28c552d16d494ccd322f9
