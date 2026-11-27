# SceneForge .196

Reference-video export now defaults to extending the last selected clip to the separate voice track end. Voice stays at its applied speed and source bytes; source clip order/durations remain untouched in the project. Tail source duration is capped at the chosen cut, exposed as optional mediaDuration to the renderer, then padded by FFmpeg. Default on; no extra user mode selection. Explicit previous trim consent remains respected.

Full separate audio and subtitles survive source video cuts and reorder mapping in extension mode. Preview clocks and subtitles use voice timeline time, preview tail holds and output length match the final export. Music without duck extends to match. Legacy trim mapping remains and is tested explicitly. Photo workflow unchanged. Existing whole-movie speed and genuine missing/changed asset validation remain.

Export now sends room_id for durable library capture and reports exceptions before preflight. No provider calls or model/API changes. The optional renderer field is backwards compatible and bounded.

Validation: check_export_save_as_ui.py uses Chromium plus real FFmpeg, library capture removing the temp MP4, native/browser save/retry. New case: source cut to 0.4s with 5.44s voice; click export with no mode selection, verify duration and audio stream via ffprobe, entire voice at speed 1, late caption, final pixels match selected cut frame. check_voice_caption_handoff.py passed. check_merge_order.py passed in explicit legacy trim mode. Other shipped payloads byte-identical to .195. No live provider or Windows installer execution.
