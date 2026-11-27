# SceneForge .197

Replaces .196 last-frame extension with proportional allocation of additional duration across remaining selected source motion, capped at sourceDuration minus sourceIn. Recomputes contiguous clip starts without modifying saved project scenes or source assets. Keeps separate voice and measured subtitles on their continuous clock at the applied speed. No frame holding, looping, generation or automatic voice acceleration used to cover excess speech.

If required duration exceeds summed source capacity, preview reports the shortage and final export rejects it before job creation. Existing explicit trim mode remains. No provider or backend change in this release; every payload except workflow.html byte-identical to .196.

Real Chromium/FFmpeg test in check_export_save_as_ui.py: two 3s sources cut to .2s each, 5.44s separate voice; single export uses 2.72s per source, audio speed 1 and last caption retained. Export pixels at 4s match source at 1.28s and differ from 5s (moving). 7s voice with 6s source capacity rejected with no renderer job. Existing save/cancel/retry and library capture tests passed. No live provider or Windows installer execution.
