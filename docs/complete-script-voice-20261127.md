# SceneForge .195

Voice script extraction now uses every nonempty visible script row rather than ASR eligibility, preferring nonblank edited text, translation, then original. Source timing windows do not limit synthesized content. Display includes full row count. TTS responses must include matching IDs in order, continuous finite timings and duration before existing audio is replaced. Existing backend performs WAV integrity validation.

Voice length fitting reuses the existing local tempo effect, deriving speed from original duration with an upward 0.01 step within 0.5–2x. Out of range fails visibly. Accepting excess-voice truncation now requires an explicit confirmation. Complete measured generated caption timings are retained; existing timeline mapping handles clipping.

Test: check_voice_caption_handoff.py exercises actual TTS button and captured fixture payload including suspect edited rows, tiny source windows, final phrase, whitespace fallback, incomplete response retaining old audio, over-limit fitting and cancelled cut consent; previous handoff and subtitle tests retained. No live synthesis or Windows installer execution. Cumulative package verified unchanged from .194 for every other payload file. Missing words within a model-produced waveform cannot be detected by timing metadata alone; no claim of ASR quality verification.
