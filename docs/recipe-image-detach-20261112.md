# .122 recipe image retirement

The user-supplied .121 report identifies the remaining 15,699-byte JPEG as a live reference in `sceneforge-app-shell / prefs / recipe-library`, not a pending video download. This is an independently saved recipe-library image, retained across room deletion by design.

The lifecycle owner function now identifies only that exact prefs key with the reserved `library:recipe-library` owner. Public detail reports label it Kho kịch bản and enumerate the specific recipe names/IDs and marker paths. A candidate image in a live expired purge operation exposes `can_detach_recipe`; other MIME types, future retention, completed and cancelled operations do not expose the action.

`detach_recipe_image` requires explicit confirmation, a mutation ID and an unchanged detail token (now including canonical revision). It replaces only matching blob/file/dataurl markers with null inside the one recipe-library record, preserving all text, list order and unrelated fields/media. The existing CAS commit records a checkpoint receipt. Existing room_release policy for the reserved owner records explicit retirement of that hash, so old backups restore the image marker as released. Normal protected processing then attempts physical deletion; no pin, lease, unresolved job or other current project reference is bypassed. No schema or backup database edits are required.

The UI flushes before mutation, rejects a changed revision, records a checkpoint intent for interrupted-operation recovery, pauses writers, hydrates the returned canonical snapshot and reloads. This prevents stale in-memory recipeCache/IndexedDB content from writing the image back. It lists all affected recipe names before confirmation and explains the effect on old backups. Existing .121 backup-only retirement and current-owner diagnostics remain available.

Tests:
- `python scripts/analysis/check_recipe_image_detach.py`: exact recipe names; duplicated image refs across active/trash entries; confirmation/stale-token checks; actual file removal; script text and unrelated images untouched; old backup restore; another project's live image retained.
- `python scripts/analysis/check_recipe_image_detach_ui.py`: actual SQLite/library API and Chromium interaction; names and action visible; confirmation, physical deletion, canonical hydrate/reload and script-cache correctness, plus .120/.121 regressions.
- `check_storage_holders.py` and original full-source `local_engine.check_storage_lifecycle` passed with patched modules.
- Builder verifies embedded source bytes/checksums and unchanged generic launcher, cumulative .62+ payload includes importer and prior fixes. Windows installer and user-machine file deletion not directly tested.
