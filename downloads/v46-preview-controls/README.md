# SceneForge v46.81 — Preview controls

Requires v46.80 or newer. UI-only patch: workflow.html and photos.html.

- Stable dialog, video screen and transport geometry; sidebar scrolls independently.
- Preview playback rates: 0.75, 1, 1.25, 1.5 and 2; external audio follows rate with pitch preservation.
- Optional per-clip preview tail trim: off (default), 50, 100 or 150 ms. Held tail is removed first; trimming real footage may remove final speech. Original media and export settings are unchanged.
- Original cue and voice timing is mapped across removed tails. Turning trim off restores the original duration.

Validation: Chromium with real MP4 and audio; stable rectangles under long labels/status and sidebar scrolling, actual video/audio rates, reversible trimming, cue mapping, unchanged source scene/cue/voice data. Buffered joins regression checks retained decoded frame during delayed loading and synchronized clock/audio waiting. Embedded EXE sources and browser download checksum verified. Windows updater has not been run.

SHA256: `ae1df46e9cb36acc3497408abab00585d0ec698532d745dc4cb2d3c26d4b4ae7`
