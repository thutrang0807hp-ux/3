# SceneForge .73 — independent voice picker and sample wait state

Requires .72; close app, apply updater, reopen. UI only, workflow.html/photos.html. Preserve model, prepared samples, warm runtime and all .72 backend changes.

Voice name selection bypasses global audio busy lock, updates in memory, closes picker and paints immediately, then uses existing debounced autosave. Workflow AI-mode change also does not wait for full-project persistence; photos keeps its transactional photoSetVoiceMode guard. Existing navigation/flush sees current choice.

Sample operations have their own pending state; choosing/opening/closing picker remains possible while read/generation is pending. Only sample button waits; competing narration/CPU synthesis is blocked explicitly, not queued. Completed stale samples may cache in the same room but cannot change voice or autoplay after different choice/mode, room change, page hide or workspace pause. Cached/shared/new sample paths all check intent. Samples no longer wait for project-save promises; errors restore controls and remain visible for current request only. Latest selected voice remains in autosaved project; no automatic synthesis or retry on choice.

Validation: check_voice_picker_pending_ui.py deliberately blocks storeProject promises, POST TTS and GET shared WAV while exercising real clicks, AI-mode switch, selection B/C, closing/reopening picker. Verifies exactly one TTS request, stale results cache without autoplay/selection overwrite, frame DOM identity, cached replay while saves remain blocked. check_voice_playback_picker_ui.py verifies actual WAV playback clock, autoplay recovery, sample vs narration storage, worker error recovery, compact 25-voice search and cross-room cached playback. Model endpoints are fixtures, not a current model/Windows timing benchmark.

EXE: SceneForge-Update-20261108-v46.73-Responsive-Picker.exe
SHA256: 940c0f9842e0b94ad77515b3a76d6a7273be58f4820adf1ab07211110f7c173b
