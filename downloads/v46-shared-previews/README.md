# SceneForge .71 — shared offline preview preparation

Requires .70. Close app, apply updater, reopen Giọng AI and click Chuẩn bị mẫu nghe nhanh. This is explicit CPU preparation, not a shipped pack of 25 pre-generated voices. It may take time on first run. Once ready, samples are durable across projects/restarts and playback does not load/synthesize through the model. Full script narration still runs local TTS.

API: /tts/previews/status, POST /prepare, POST /cancel, GET /file/{voice_sha256}, under /local-api. Uses existing local session middleware and TTS lock. No preparation at boot/status/file GET. One isolated offline worker loads model once then processes missing presets. Per-preset WAV/receipt atomic completion; cancellation kills process tree through existing run_command, keeps completed files; restart is idle until explicit resume. Cache bound to model-status fingerprint + preview revision; verifies voice ID and WAV hash. 64MB free-space guard; no model downloads or paid fallback. Samples stay under engine/previews, independent of room cleanup. Preparing blocks competing TTS, never queues a hidden generation request.

Both workflow/photos share UI, bounded picker, explicit prepare/progress/stop; current-room sample cache first, then shared preview, otherwise original one-time sample synthesis. New project shared playback creates no TTS POST. Hidden workspace poll does not repaint.

Validation: check_voice_preparation.py (fixture PCM with real FastAPI/httpx, locks/cancel/resume/integrity/restart/model namespace), check_voice_playback_picker_ui.py (real Chromium media clock, UI button/shared sample in second room, no extra TTS POST), Windows alias regression. Model SDK absent in test runtime; no real 25-preset synthesis or Windows updater run. Existing SDK voice_worker copied byte-for-byte from baseline ZIP. Models/providers/settings unchanged.

EXE: SceneForge-Update-20261107-v46.71-Shared-Previews.exe
SHA256: f0925de5f580f1e02d87b348bec16efddeac49a0fc2b5477844f39223386d5b2
