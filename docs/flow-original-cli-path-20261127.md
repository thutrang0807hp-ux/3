# Original CLI owns the video path — .193

Reference reviewed: thutrang0807hp-ux/5gdfgfd commit 09ab05b190ddad0b3bbed80439ecbc6739d5abce, app.py build_args/execute/worker. The reference starts `python -m gflow_cli` with its selected profile and GFLOW_CLI_HOME; the CLI handles its own browser/project/generation/download. SceneForge previously inserted a second browser/account/project preflight before that command. User reports demonstrated failures at email, RPC metadata and UI project recognition within that preflight.

Production SimpleFlow.run now calls the existing CLI adapter immediately after saving the input image, before restore/assert_ready/native project/native preparation/pair validation. The adapter uses the selected profile (or matching configured original repo profile), validates local input/account binding, then starts `python -m gflow_cli video r2v/i2v --project-name SceneForge ...`. It no longer requires SceneForge to open a browser, read WIZ email, create a project by RPC/DOM, warm up RPC or upload the reference first. The CLI owns all those provider-facing operations. UI HTML/layout is unchanged.

Intentional input differences from the supplied GUI wrapper: its video button sends text-only t2v; SceneForge passes the approved image with r2v/i2v and the current selected model/aspect so frame identity is retained. The unchanged bundled SDK is 0.98.0 (required for current Omni option), rather than the reference portable archive's older 0.92.1. This is the same original CLI entrypoint architecture, not a claim of byte-identical arguments/SDK versions. No SDK source modification or alternate SceneForge RPC sender is used by this path.

Project identity comes from the CLI's first valid migrated.dispatch event. A later different project is rejected. Actual media IDs, exit state and validated file remain required before importing. The durable request ledger, chosen account, source-image hash, settings, per-request output directory, cancellation, uncertain-result retention and download-only recovery remain enforced. No automatic replay of prior failed/unknown requests.

Verification:
- Actual Chromium workflow Create click -> actual SimpleFlow submit/run/RequestLedger -> a real isolated child process implementing the original CLI JSON/event contract -> real eight-second MP4 -> actual backend ffprobe validation -> actual UI scene import. Passed frames/Omni and ingredients/Lite. Exact prompt and image hash verified in the child. Repeated request ID did not launch a second child.
- Backend configuration cases: ingredients/Fast/landscape, frames/Quality/portrait, bundled Lite; early ID persisted, settings retained, duplicate blocked, missing runtime does not send.
- Dispatch failure before/after grant, upload-only never generates; CLI project binding/progress mismatch tests.
- Provider is simulated. No live Google login, paid Flow generation or Windows updater execution was performed. Local success proves the application boundary, not provider availability.

Update: fully exit SceneForge, run cumulative .193 and select the folder containing SceneForge.exe, reopen and try one new clip. Supports .62 onward. Existing UI, projects/accounts/models retained. CLI browser may appear while it works. Do not delete profile/cookies or replay old requests automatically.
