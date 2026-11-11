# SceneForge .118 — Order controls stay visible

The .117 controls were attached by the outer render wrapper, but SFReferenceNodes.refreshHandoff calls the private merge renderer directly, replacing the strip and removing controls/draggable bindings. Embed both controls and per-item data/draggable attributes directly in that renderer. Outer control still supplies accessibility text during full renders.

Add an explicit order button to the assembly viewer header. It closes/stops the current viewer, opens the ordering list, and Done closes the list and reopens assembly. Block entry during export. Closed ordering markup remaining in the generic modal no longer causes subsequent undo/drop to reopen that modal; only an open ordering modal refreshes after moves.

Validation: expanded check_merge_order.py uses real MP4/WAV in Chromium; order button inside viewer -> list -> Done -> viewer, direct handoff refresh preserves button and drag attributes, undo/Alt arrows continue to work after viewer close. Existing checks for actual first red clip pixel, caption/voice offsets, persisted order and a/b parts all pass. Inline parsing/payload checksum validated; no Windows updater run. Cannot establish installed version on user's computer from their text alone.
