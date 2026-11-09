# .98 — incremental library reads and visible close failures

Ordinary checkpoints previously traversed all IndexedDB stores, including unchanged media, before encoding dirty rows. Read only dirty keys, or the dirty store after clear. Preserve full scans for initial reconciliation. Build into a temporary map and commit only if the mutation epoch is stable. Missing dirty keys remove deleted records.

Close steps now display their stage after 2.5 seconds and show actual save errors, also stored locally in sceneforge-close-error. Native host still uses its existing close handshake and still asks on failed save. This release does not claim to resolve all Windows shutdown delays.

Regression checks use Chromium, IndexedDB and SQLite: no unchanged project/media cursors for a prefs-only update, deletion propagation, durable edits, active-work save-only guard and failure retention. No Windows installer or native host run.
