# SceneForge .75 — large video caption review and word limits

Requires .74. Close app, apply updater, reopen caption node → Xem video & phụ đề. Real selected clips play in a large portrait view, seek/fullscreen controls and live words/size/position. Missing clips shown explicitly; no fake videos, auto-generation or automatic export. Existing media is reused.

captionWords defaults to 5, options 1–20/common counts and whole sentence. Raw authored cues remain intact. Display/handoff/SRT/PNG layers split rows into word-count chunks and allocate each original cue interval proportionally by word count, preserving its endpoints and all words. This is approximate timing, not word-level ASR. Manual edits remain in raw cue editor. captionOptions.maxWords pins export snapshot.

Shared canvas drawing for new viewer and photo-mode export PNG captions (proper clean/yellowbox/box/tiktok styles), full transparent 1080x1920 overlay. Native clip/voice/music mix from current selections, using existing prepared ducking path when enabled. Preview may display stale cue text with a warning to help review; normal handoff/export stale/voice guards remain strict. Photo builder wrappers forward preview options; normal calls unchanged. Session cleanup closes media, cancels RAF, revokes URLs; room/page hide pauses or stops. Edits later made in Dựng use that editor's own state.

Validation: check_caption_video_viewer_ui.py real generated MP4 in workflow and photos, playback clock advances, live 3/5/8/full-sentence updates, size/position, all words and contiguous cue envelopes preserved, SRT/PNG/handoff pages, export guard, URL cleanup and missing-file messaging. Caption scale and voice picker tests retained. Fixture bridge/clip, no live Flow/model. Updater not executed on Windows.

EXE: SceneForge-Update-20261108-v46.75-Caption-Review.exe
SHA256: d11cbfbbc4cb3fda0fde22c6af064ff7b648bd55d4cb43d99ad0609e097b7561
