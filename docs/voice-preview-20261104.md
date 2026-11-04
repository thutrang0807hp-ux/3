# Voice preview .69

User report: pressing sample play has no sound; all voices expand the canvas node vertically.

Shared audio nodes in workflow.html/photos.html now call play immediately after source assignment, retain cached samples on playback rejection, surface persistent errors and allow explicit replay. Voice selection uses a searchable, bounded, scrollable modal. Optional effect-status failure no longer discards successful TTS status. No model/provider/backend changes.

Browser test: `python3 scripts/analysis/check_voice_playback_picker_ui.py`. Real PCM WAV playback clock verified with mocked TTS endpoints; tests autoplay denial, cached retry without another synthesis, full narration storage, optional status failure and worker error recovery. This is not current-model or Windows validation.
