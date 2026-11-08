# SceneForge .72 — warm CPU voice runtime and responsive audio controls

Requires .71. Close app, apply updater, reopen. Prepared preview namespace is unchanged; no model or sample reinstall. Cold first inference still loads the model. Subsequent narration/samples/preparation use a single private SDK child while active; auto release after 180s idle. Full CPU inference is not made instantaneous and there are no measured Windows speed claims.

Private stdio protocol with nonce, no socket. Offline flags and existing two-thread ONNX load_model retained. Child redirects SDK stdout away from protocol. Parent serializes work; fingerprint changes start a fresh child. No inference retries; timeout/cancel/failure kill process tree, clean partial outputs and require explicit next request. Shutdown stops preview work then runtime; idle releases RAM. Original WAV mono PCM16, duration/timing/beat IDs/SHA checks preserved in background thread. Preview batches now use the same runtime as narration instead of a separate loaded model.

Async status/media API sends filesystem scans and hashing to asyncio.to_thread. Ready WAV integrity is cached against path, size, nanosecond modification/change times, receipt hash/voice ID; modified files revalidated. Main status endpoint also awaits TTS checks in a thread.

Workflow/photos audio controls update audio bodies instead of recreating scene frame/video DOM. Mode UI paints before saving full project; animation yield has timer fallback and room guard. Shared/new samples begin playback before saving large project; cached sample persists even if autoplay is denied. Existing data/prompt/room guards retained.

Validation: check_warm_voice_runtime.py uses actual subprocess and stdio protocol with fixture model; verifies single load for two requests, model changes, asynchronous heartbeat, failure/no retry, timeout/cancel/idle/shutdown, parent WAV/timing/hash checks and failed-output cleanup. check_voice_preparation.py covers cache/lifecycle/lock. Chromium check_voice_playback_picker_ui.py retains actual scene frame element across voice-tab change, playback clock advances, cross-project shared samples avoid inference. Video UI regression also passed. This is not real SDK throughput or Windows validation.

EXE: SceneForge-Update-20261108-v46.72-Warm-Voice.exe
SHA256: 6c93d1c97616a322bf7ccb151e67fc7d85039d29205a66c893606b97a1608185
