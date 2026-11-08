# SceneForge .74 — caption node preview scale

Requires .73. Close app, apply updater, reopen caption node. UI-only workflow/photos update; runtime/model and prior voice fixes preserved.

Screenshot showed value 37 but paragraph still covered image. Preview used max(10,size*.16) pixels, unrelated to thumbnail width. Replaced with fontSize/1080*100 container-width units and an inline-size container, matching editor 1080-based font semantics. Slider updates same units. Preview limited to two lines, clipped only visually; full source text preserved in DOM/title, content list/editor and exported cues. Relative preview outlines avoid disproportionate thick strokes at small scale. No font-size, position, cue text, timing or export behavior migration.

Validation: check_caption_preview_scale_ui.py: Chromium long paragraph, sizes 28/37/64/100 strictly increasing, width-derived 37px scale, two-line height and bounds inside preview (<16% height at max), original manual text/settings/timing retained; workflow/photos shared script/CSS equality. Tests target screenshot/node display, not a change to subtitle segmentation or exported video typography. Updater Windows not run.

EXE: SceneForge-Update-20261108-v46.74-Caption-Preview.exe
SHA256: 72028c1cf293209a3aa9e0298c1473ca745696318096458322b52cedaf332bf8
