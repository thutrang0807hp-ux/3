# SceneForge .194

Automatic unedited subtitles use persisted VieNeu spokenRows and measured segments, including applied tempo changes. Manual and previously audio-aligned captions remain protected. Preview and editor handoff read the same cues. No forced recognition or provider request.

Handoff displays preparation/import failures in the merge node, prevents duplicate clicks while awaiting the host, and awaits editor acknowledgement. Existing validation remains: missing files, stale manually edited captions, changed voice, and length acceptance are not bypassed.

Also includes the previously prepared local default video prompt restoration. Gemini rewriting is optional; manual nonempty drafts remain. Provider transport unchanged.

Validation: check_voice_caption_handoff.py (actual iframe UI, fixture media/host); check_merge_order.py (real MP4/WAV, reorder/remap); check_video_default_prompt.py (fixture Flow request, original image bytes). No live provider call or Windows installer execution. Embedded payload verified byte for byte against sources, including unchanged Gemini native archive.
