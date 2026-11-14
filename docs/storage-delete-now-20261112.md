# .120: immediate explicit deletion and overdue operation actions

The existing backend already supports `days=0` and `lifecycle/expedite`, which deletes eligible files synchronously. No backend deletion protection is weakened in this update.

The UI defaulted all cleanup dialogs to seven days, including the “delete permanently” route. It hid expedite actions as soon as the operation due date passed, even when a retry or newly unprotected file needed processing. The operation's `created` timestamp (seconds) was passed directly to JavaScript Date (milliseconds), displaying January 1970. Counts and deadline labels treated blocked operations as merely waiting.

Both index.html and studio.html now initialize delete to zero days and keep retention an explicit choice; bulk dialog opening is awaited before setting its mode/days (the former click returned before its asynchronous modal was built). Live pending operations expose an explicit expedite action regardless of deadline; completed/cancelled operations do not. Processing reports freed bytes, remaining protected files and errors. Failed/protected state labels describe their actual state. Only waiting future operations count toward upcoming retention deadlines. Operation timestamps are normalized at the API-to-UI boundary.

`python scripts/analysis/check_delete_now_ui.py` validates real browser UI with actual library API/SQLite/files, including immediate defaults for single and bulk, opt-in retention, overdue operation execution through the visible button and actual file removal, no missing assets, existing shared asset counts and cleanup guards. The existing storage-manager test is included as setup/regression coverage. JavaScript parses on both shipped HTML pages. No production user data was deleted during development.

.120 is a cumulative .62+ payload based on .118, with the .119 importer retained. Builder reads back the embedded ZIP, checks its manifest/source bytes and launcher invariance. Source and EXE metadata live under downloads/v46-delete-now. Windows installer and real user machine deletion have not been tested.
