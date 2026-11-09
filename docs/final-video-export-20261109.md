# SceneForge v46.83 — Media clock and final MP4 export

Requires .82 or newer. Two HTML files only: workflow.html and photos.html. Existing native editor, backend, models and original assets remain unchanged.

## Playback and comparison

- Individual clips now drive timeline time from media.currentTime. A stalled decoder cannot advance a separate wall clock and trigger periodic catch-up seeking. Wall time is used only for explicit missing segments / short-source tail holds, capped at clip boundaries.
- Existing two-buffer decoded-frame bridge and single-file FFmpeg preview remain. Source comparison opens the selected original file at its final two seconds, pauses assembled playback, and cleans up the extra player/URL on close.
- Readable diagnostics show player wait, reported dropped frames and planned tail hold. These are measurements, not an automatic classification of intrinsic source motion.
- No transition or destructive crop is inserted; source-content discontinuities can remain.

## Final export

- After preparing the joined preview, Export video creates 720×1280 or 1080×1920 / 30fps MP4 from original source files, not the 360p preview.
- Strict voice/caption preflight still applies. Saved per-version endpoints map separate voice and caption timing. Native clip sound honors inclusion/volume; background music repeats to the end. Custom caption colors/background alpha are burned into transparent PNG layers and rendered into the final MP4.
- Preview-only rate never changes final speed; preview-only bulk trim must be off. Visual caption intervals follow the output frame grid; audio fragments respect the renderer minimum interval. Duration covers all layers, including floating-point interval boundaries.
- Progress, cancellation, recovered editing controls, and download again without another render. Editing a saved cut/style/color/size/word limit retires the old final. Closing the viewer cancels its active export; switching to a hidden app view pauses preview only.
- This exports node settings. Separate native-editor timeline edits must be exported from the editor. Existing editor-overwrite protection remains.
- Renderer limits remain 10 minutes / 512 MB sources / 120 timeline rows. A readable error leaves settings intact.

## Verification

Real Chromium + MP4/WAV, FastAPI timeline protocol and FFmpeg: simulated ready-but-stalled media clock remains synchronized; original-tail comparison cleanup; stale caption guard and recovered controls; actual 720p and 1080p H264/AAC MP4 files with a non-frame-aligned 2.117s saved cut, mapped voice, repeated one-second background music and burned custom-colored captions; decoded frame/color checks before and after the join; nonzero music after voice ends; preview rate does not alter final duration; cached redownload; cancellation. Buffered-join, per-clip/caption-color, live-caption and shared-module/scale regressions also passed. Artifact sources and browser download checksum verified. Windows updater not run.

SHA256: f3237a3dc4199ce80eddbda6d7f63440f52ef4df017727af49b5103808ec01ac
