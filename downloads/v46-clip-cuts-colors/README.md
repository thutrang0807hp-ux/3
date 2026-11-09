# SceneForge v46.82 — Per-clip endpoints, caption colors and joined preview

Requires .81 or newer. Three HTML files only: workflow.html, photos.html, native/index.html. Installed runtime/models are untouched.

## Behavior

- Save individual clip endpoints by scene/part/version identity, with slider, numeric input, 1/30-second nudges, two seconds before/after audition and restore. Minimum retained duration: 200ms. Endpoints are relative to the selected slot's source offset; original media remains intact.
- Preview and assembled editor handoff use these saved endpoints. Caption pages, standalone voice and ducked music are intersected with retained intervals and shifted; uninterrupted background music stays continuous. Original authored cues remain untouched. Source offsets are retained by the editor; split audio shares one source and one role track.
- Text/background colors, background toggle and alpha update the canvas immediately and are passed to native editor text items and its export renderer. SRT retains timing/text only.
- Explicit “Chuẩn bị bản xem liền” uses existing local FFmpeg timeline API to produce one 360×640 / 30fps MP4 of clip picture/native sound. Caption overlay and separate audio remain live. Playback uses one video's clock across joins. Original export resolution stays unchanged.
- Cache holds two preview blobs in this app session. Endpoint changes invalidate the active joined file; stale/closed requests cancel their jobs and cannot replace a newer player. No generation is triggered. Existing source-content motion defects are not repaired by re-encoding.
- Legacy bulk trim and rate controls remain preview-only. Saved per-clip endpoints affect assembled handoff; library handoff still supplies source media for manual editing. Existing editor overwrite confirmation remains.

## Verification

Chromium + actual MP4/WAV: cuts over 150ms, nudges, restore/reopen, canvas color/alpha pixels, caption/voice mapping, native-editor import timing/colors/source offsets and shared audio. Actual FastAPI timeline renderer plus FFmpeg: single-file playback crosses join without changing source; cache avoids another render; audition stops after the next two seconds. Existing assembly-mode, buffered-join, live-caption and shared-module/scale regressions passed. EXE resource bytes and download checksum verified. Windows updater was not run.

SHA256: `3e4dad98f7d3142d63e3e90b8a269d449b7db2790cfd61703c8e49a93d02a3e3`
