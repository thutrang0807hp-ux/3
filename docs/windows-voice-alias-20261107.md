# SceneForge .70 — Windows voice aliases

Requires .69. Close SceneForge, run updater, choose existing installation, reopen and try voice sample. Do not reinstall the model. A previous unsuccessful sample may need one explicit new synthesis because frontend never saved it.

Root cause in source: StorageJobs.capture stores str(Path.relative_to(data)) in backend_alias, which uses backslashes on Windows. voice_file searched only media/filename. TTS captures canonical WAV then deletes original; subsequent GET media can return 404 even when canonical audio exists. Lookup now accepts both media/filename and media\filename, preserving old Windows catalogue entries without database mutation.

Test: scripts/analysis/check_windows_voice_alias.py uses real SQLite Windows/POSIX aliases and PCM WAV; demonstrates old query fails Windows alias, fixed StorageJobs plus actual server media handler returns exact bytes and audio/wav over ASGI HTTP. Missing aliases/files remain missing. Lifecycle import dependency is stubbed because this test isolates lookup; no model inference. Browser voice regression passes with mocked TTS. Builder verifies embedded storage_jobs.py matches source and launcher unchanged. No Windows/model end-to-end test. User machine logs have not confirmed that this source defect is their only failure.

Only app/local_engine/storage_jobs.py patched. UI/model/runtime/Flow adapters unchanged.

EXE: SceneForge-Update-20261107-v46.70-Windows-Voice.exe
SHA256: 6ea664c7d6fed0f697be64d8415fd417c09195dfc8d1696185ec5615c34b6f38
