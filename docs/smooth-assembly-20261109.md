# SceneForge .80 — buffered playback and compact assembly node

Requires .79. Close app, apply updater, reopen same project. Reuses original clips; no generation, credit, transcode or changes to exported media. Fix is for local timeline preview decoding/joins. Does not remove intentional black frames already present inside source media.

Player previously reset the sole video.src at each boundary and exposed the cleared decoder before the next frame. New player alternates exactly two video elements, preloading only the next clip. An in-memory canvas holds a decoded old frame until the next decoded frame is available; then it bridges to the new video compositor frame via requestVideoFrameCallback (two-RAF fallback). No synchronous image encoding at joins. Clock and independent audio tracks pause during decode/seek waits, avoiding audio running ahead. Non-active decoder muted/paused. Tail holds use decoded final frames; source offsets respected. Seeking, gaps, room guards, style canvas and URL/callback cleanup retained. Actual missing clips remain labelled gaps.

Assembly layout: full-width stacked mode cards with icon/title/subtitle/check, narrower thumbnail strip and thin scroll, one grouped track-inclusion block with readable style labels, full-width primary play and secondary editor link. Duration is computed from current clip slots. No selected mode/include data migration.

Validation: check_buffered_assembly_ui.py uses real red/blue/green H264 clips and samples composited screenshot pixels at joins. Forces the second decoder ready-state delay: old red frame remains visible, timeline does not advance, audio is paused/muted; resumes blue then green with sampled pixels nonblack. Checks video compositor resumes, only two decoders, seeking/cleanup and readable mode bounds; screenshot /tmp/sceneforge-assembly-node-v80.png. Assembly-mode, caption/style tests and near-8s Veo receipt regression also run. This is Chromium fixture evidence, not user source-video/Windows validation.

EXE: SceneForge-Update-20261109-v46.80-Smooth-Assembly.exe
SHA256: 37d61a22ee1a4510daea981f6ddbd1d632036757bb40c6c5307351342ee29f27
