# .121 exact file holders and backup-only retirement

The reported .120 screenshot proves a protected file remains; it does not establish whether it is a backup, project, upload lease, pin or unresolved job. .121 adds evidence for that distinction rather than assuming a root cause on the user's computer.

Restored and tracked baseline modules `library_api.py` and `storage_lifecycle.py` from the v46.50 Full Source archive. Existing lifecycle deletion/protection remains; new detail/release methods are additive. `process` now also reports `freed_this_attempt` alongside cumulative `freed_bytes`, so repeat clicks do not misleadingly repeat old freed bytes.

`GET library/lifecycle/detail/{op_id}` returns up to 200 actual asset rows with physical paths, hashes, sizes and holder details. It identifies current record owners, pins, upload-lease expiration, unresolved jobs, competing purge operations, and precise backup filenames and room IDs. Each backup is read once per report. No cookies, account credentials or unrelated process information is read.

`POST library/lifecycle/release-backup-file` is a narrow, explicitly confirmed operation. It rechecks a content-derived detail token under the library lock, rejects any live holder, backup pin, unowned/shared backup reference, cancelled/done operation or future retention. For a backup-only asset it records existing `room_release` now:unused policies for the enumerated backup owners, then runs normal protected deletion. Old backup restoration already respects these policies and marks the retired asset released. No backup DB is edited or deleted, and no new database schema is needed. A concurrent new live reference is rechecked by normal processing and remains protected. Existing upload leases are never silently cleared.

The shared UI module `scripts/ui/storage_file_holders.js` is embedded verbatim in index.html and studio.html. It offers exact holder descriptions, per-file backup-only retirement with a specific loss-of-restore confirmation, pin removal, opening known current owners and downloading local JSON evidence. Pending purge rows have a detail action; an expedite result that still reports protected files opens it automatically.

Validation:
- `python scripts/analysis/check_storage_holders.py`: real SQLite/assets; backup filenames and paths; explicit consent; stale-token rejection after a new live owner; rejection of force deletion while live; actual backup-only file deletion; safe old-backup restore; pin note; upload expiry; unresolved job identity; future-retention guard; per-attempt freed-byte accounting.
- `python scripts/analysis/check_storage_holders_ui.py`: actual library API + Chromium UI, including original storage manager/.120 regressions, exact backup/path modal and consented file deletion through the new button.
- Original `local_engine.check_storage_lifecycle` from full source with patched lifecycle/API: passed quarantine, restore, shared/live references, fresh leases, crash/retry and backup-release regressions.
- Builder verifies embedded ZIP source bytes/hashes, template checksum and unchanged launcher code. .121 is cumulative from .62 and includes .119/.120. No Windows installer or specific user-file repair claim.
