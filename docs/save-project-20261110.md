# .102 — explicit project save

Add an always-accessible rail save control with loading/pending/saving/saved/error states and Ctrl+S on the shell, workflow, photo director and timeline. Calls the same save-only frame flush and verified library checkpoint used by native close; no separate unverified write or export-JSON substitute. Browser-only mode is labelled Bản nháp rather than durable saved.

Child editors report actual draft dirtiness and completion to their own same-origin parent. The shell validates message origin and iframe ownership. Detached frame references are removed from status tracking. Do not report success when further drafts/IDB changes remain. Display actual save errors. Manual requests coalesce while saving. Status changes avoid rendering the main workspace.

Schedule ordinary durable autosave from the first mutation instead of continuously postponing on every new write. Keep the existing periodic fallback and error safeguards. Clean checkpoints remain no-ops. A new edit after saving still requires another save; background operations are not falsely declared complete.

Regression uses Chromium with real IndexedDB and SQLite. Ctrl+S from workflow produces durable project metadata; the following native close handshake sends zero snapshot POSTs. Failed saves show Lưu lỗi and retain the draft. Existing navigation tests preserve active-tab and retained-frame behavior. No Windows GUI/close-latency run. Cumulative package retains the native .101 loading host unchanged.
