# SceneForge integrated Flow UI engine — source review

This change connects SceneForge's existing **Tạo 1 video** action to the UI engine
used by the supplied working application. It adds no application, command,
upload confirmation or login workflow for the user. The selected SceneForge
account's existing browser profile is opened by the installed browser.

## Provenance

- Reference application: `thutrang0807hp-ux/5gdfgfd`, revision
  `09ab05b190ddad0b3bbed80439ecbc6739d5abce`.
- Its portable Windows archive SHA256:
  `03ae9541fefa55e4f917f87db794cd2b26f61d5d215a754b333b5dfc3d686292`.
- Bundled `gflow-cli` version 0.92.1, upstream `ffroliva/gflow-cli` revision
  `1619429f12e31a806590a19e1a3f3218f291d582`. The archive's client, video model
  and UI video driver sources match that revision byte for byte. The runtime
  retains distribution metadata and licenses, including gflow-cli's MIT license.
- The reference application's visible wrapper uses text-to-video. The integrated
  SceneForge path uses the same SDK's **R2V** support: one approved reference,
  prompt, Lite, portrait, 8 seconds, one output. This mode has not been verified
  with the user's live Flow account.

## Code

- `veo-node-v46/local_engine/flow_gflow_runtime.py`: fixed HTTPS URL, full archive
  checksum before extraction, bounded size and safe paths, atomic installation
  of runtime files only. First use downloads the ~80 MB runtime automatically;
  later runs use the private cache under SceneForge data. No pip or global
  dependency replacement. Python executables from the archive were not run here.
- `flow_gflow_worker.py`: private JSON subprocess entry point, ordinary headed
  installed browser, existing profile, expected account email verification.
  Uses SDK UI transport rather than SceneForge's hand-written generation RPC.
  The adapter overrides browser executable selection and disables the SDK's
  cookie preread/reseed helpers; the browser uses its own profile directly.
- `flow_gflow_adapter.py`: existing RequestLedger remains the send authority.
  Saves an ambiguity boundary before granting generation; records returned IDs,
  matches completion identity, validates download location and video properties,
  then saves the result for the original room/scene/part. No RPC fallback or
  automatic generation retry. Cancellation asks the owned worker to close before
  terminating only that child if it does not exit.
- `simple_flow.py`: enables the integrated driver before the old native pipeline;
  retains existing validation, account selection, duplicate receipt behavior,
  task gate, cancellation and cleanup. Uses a separate live-verification badge
  so earlier engine successes cannot mark this engine verified.

The worker protocol exports only fixed status fields, provider IDs, file paths
and allowlisted public error codes. Third-party stdout/stderr is not included
in reports. No tokens, cookies, signed download URLs or credentials are exported.

## Verification and delivery status

Passed 9 local tests using a real child process and SDK doubles:

```
python -m unittest discover -s veo-node-v46/tests -p 'test_gflow*.py' -v
```

These cover correct result association, errors before/after the durable grant,
failed grant persistence, cancellation, mismatched IDs, wrong account and
absence of a parent grant. Also verified the actual pinned Windows archive's
checksum, extraction, cached reuse and preserved SDK source; Python compilation
and diff whitespace checks pass.

**Not yet tested:** Windows executable launch, existing Windows profile login,
live reference upload, live generation or actual video download from Flow.
Local fixtures do not demonstrate that the earlier unusual-activity rejection
has been resolved.

This is source for review, following the user's request to review code before
packaging. Published .45 executables are unchanged. A subsequent update must
include all three new modules and the modified SimpleFlow, with a new release
number; the old .45 builder deliberately rejects modified source.

## Packaged after user approval

The user subsequently requested an EXE. Version `2026.11.03.4646` is packaged
under `downloads/v46-flow-ui-engine/`; the .45 release remains unchanged.
All 13 embedded files were checked against the manifest, embedded Python modules
compiled, and the 9 tests passed again against modules extracted from this EXE.
Runtime download remains automatic on first use. Windows installation and live
Flow generation are still unverified.

## v46.46 dispatch defect — corrected in v46.47

The initial integration put the engine branch in `run_upload_only`, not `run`.
Thus normal Create Video still reached the legacy RPC pipeline. The earlier
nine adapter/worker tests did not exercise this application dispatch boundary;
passing them did not validate that the shipped button reached the new engine.

The branch now lives in `SimpleFlow.run` before browser restore/native RPC.
Upload-only no longer references the generation payload or calls generation.
`check_gflow_dispatch.py` exercises the real submit/run/RequestLedger chain,
checks scene/account association and duplicate receipts for success and errors
before/after sending, and checks that upload-only never generates. It fails
against the actual .46 source and passes with the correction. Runtime status
and request metadata identify the active engine. Live Flow remains unverified.

## v46.48 — limit replacement to the create/send boundary

User clarified that the preparation steps already work and must remain intact.
The .47 early engine branch bypassed those steps. This revision moves the branch
to after existing preparation and validation, immediately before legacy sender
selection. An AST comparison with .45 confirms the rest of `run` is unchanged.
Account/login, native workspace warmup/upload, prompt/config validation and UI
source are unchanged.

The adapter requires the existing preparation receipt to match the room, scene,
part, account, image hash and prompt hash. It passes that receipt's project ID
and unique uploaded filename to the SDK. The SDK request uses R2V `ref_names`,
not local `reference_images`, so it selects the uploaded asset in the existing
project rather than creating another project or taking the upload path. Returned
video IDs must belong to that same project. Reports now include the engine name.

Ten adapter/worker checks pass, including a changed prepared image being rejected
before worker launch. Four application-dispatch scenarios check the ordering
restore -> existing prepare -> validate -> new engine, durable receipts and the
upload-only path. These are local fixtures; live Flow and Windows remain
unverified. This revision does not replay earlier failed/unknown requests.

## v46.49 — preserve the startup failure instead of hiding it

The user's .48 report proves that the new engine branch was reached and the
existing upload completed, but the worker failed before its ready event, so no
generation grant was sent. The parent discarded the worker's `error_type` and
reported only "Engine Flow dừng"; that log cannot identify the Windows failure.
The integration uses the SDK from the supplied portable repo, not its original
app.py CLI wrapper. These are distinct facts; using the same SDK does not prove
identical startup behavior.

This change keeps generation behavior intact and adds startup-stage events,
exception type, up to eight basename/function/line frames, and error detail
scrubbed by the reference repo's own redactor. Reports expose `engine_diagnostics`.
If the redactor cannot import, no raw detail is exported. Parent tests verify
that startup details survive into ledger metadata.

In addition to ten local protocol tests, exercised the actual pinned SDK's
request/config objects and full worker/browser startup with real Chromium and
all HTTP intercepted. Startup reached ready; the test canceled without granting
generation. Also checked the real SDK redactor removes fixture bearer/cookie/
signed-URL secrets. This Linux fixture does not reproduce or identify the user's
Windows error. **This is a diagnostic update, not a claimed fix for that error.**

## v46.50 — direct original CLI, per explicit user instruction

User rejected the SDK worker and requested the original `python -m gflow_cli
video r2v` invocation, with cwd pointing at their working copy, located somewhere
in Downloads. Production create dispatch now imports only `flow_gflow_cli`;
it no longer invokes the worker, imports the SDK, subclasses FlowApiClient,
overrides session methods, or downloads a second runtime.

The adapter searches Downloads (including the Windows known-folder override)
with bounded depth, recognizes the supplied app.py by its normalized source
hash, and selects an existing profile recording the same selected account email.
For the portable application it invokes that folder's `runtime/python.exe` and
uses precisely the GFLOW_CLI_HOME layout from its MO-UNG-DUNG.bat. For a plain
repo it uses `py`. Both execute `-m gflow_cli video r2v` with the repo as cwd.
The CLI uses its own existing session unchanged. No profile is copied or created.

The CLI requires --ref (confirmed with the actual original CLI's --help). The
adapter passes the approved image with the already-uploaded filename, same
project, Lite, portrait, 8 seconds, one output, output directory and --json.
Prompt is one argument after --; no shell is used. stdout and stderr are both
captured and their scrubbed contents retained in engine_diagnostics. CLI JSON
completion is parsed, output location/video validated, and saved to the original
scene using the existing ledger. Nonzero exit is reported, never auto-retried.

The .50 update contains only SimpleFlow and this direct CLI adapter and requires
.48 or newer. Earlier preparation modules and frontend are not replaced.
Four direct CLI local process tests and four real application dispatch scenarios
pass. Original CLI help also ran successfully in the isolated Linux environment.
Windows execution with the user's Downloads copy and live Flow remains unverified.

## v46.52 — download recovery after confirmed generation

The uploaded .51 report contains CLI exit 6 / MediaDownloadError, signed-media
HTTP 302, and a recommendation to run `gflow data download` for a specific video
ID. This is a failed download after creation, not missing generation status.
The two uploaded reports are duplicates. The parser identifies the exact existing
video ID from the report; no generation retry is appropriate.

Keep the working generation command unchanged. On this specific error, record
the video ID before attempting one CLI `data download <ID> --profile ... --out
... --json` operation. Validate the returned media, project, profile, local path
and actual video before finishing the original request and scene. Preserve both
generation and download diagnostics. If downloading still fails, retain the ID;
never issue another `video r2v` command automatically.

For already-stored failed-download requests, the existing Check old video /
Download report action now opts into download-only recovery. The backend checks
store/room/account, shares the submission gate, and ignores already-completed
requests. The UI reads the completed record and invokes its existing receive
path; no new create action is introduced. No preparation/login changes.

Validation: seven local CLI process cases, including auto recovery, existing
request download-only recovery and repeated download failure; a real FastAPI
report route + RequestLedger + ffprobe + file download test with a local CLI
fixture; wrong-room rejection and completed-request deduplication; and execution
of the actual UI report handler verifying download-only opt-in and result sync.
No real Flow calls were made, and the current user's download remains untested
here. CLI data download --help and implementation were checked against the
original pinned SDK.

## v46.53 — one reference upload per CLI generation

User confirmed .52 creates and downloads videos, but Flow lists two identical
still assets. Source inspection found the concrete cause: native prepare_inputs
uploads via maseQ, then the original CLI R2V driver uploads --ref again. The
SDK's _attach_references defaults prefer_existing=False, explicitly documenting
upload-every-time for R2V. The previous filename-reuse assumption was incorrect.

For CLI mode only, keep the existing account/project/session warmup and local
image/prompt checks but defer media upload entirely to CLI --ref. Preparation
records a truthful cli_reference_pipeline receipt with project_id and the local
image hash, no uploaded_media_id or remote-verification claim. Pair validation
checks this receipt, account, scene, image/prompt hashes and current project.
Native preparation's default upload=True behavior remains unchanged for other
callers. The CLI still receives exactly one --ref and --count 1; SDK/CLI code is
not changed. Completed records mark that the single-reference CLI succeeded.
Old download-recovery records and new project_id records are both supported.

Validation: actual preparation/receipt checks assert native.upload is never
called in CLI mode, reject changed images/projects, and verify no invented image
ID. Eight local CLI tests and existing submit/ledger/download-only recovery
checks pass. Applied only to future requests; no existing Flow assets are deleted.
Live Flow execution of this new change is unverified here.

## v46.54 — auto-sync the settings selectors

Changing a Flow settings selector now saves and schedules the existing settings
API after 500 ms. Rapid edits coalesce into one request containing the latest
selection. The normal Apply button is removed; failed/unverified attempts offer
an optional retry. The UI polls for actual backend verification and resumes a
pending settings-status read after returning to the room or reloading.

Queued changes are scoped to their room and selected account. Account or room
changes cancel/reject stale work, existing generation blocks setting changes,
and creation is disabled while settings are queued/being applied. No generation,
reference upload, CLI command or video-download implementation changes.

Validation executes the actual change handler/settings functions against local
API/timer doubles: coalescing/current settings, actual verification polling,
room/account changes, busy operation exclusion, visible error/retry, creation
blocking and reload status recovery. All ten inline frontend scripts parse;
the existing download/report UI check still passes. Live settings sync on the
user's Flow page is unverified here; the existing backend apply route is reused.

## v46.55 — compact settings dock on the Workflow toolbar

Moved the settings controls out of the tall video node into a collapsed Flow
summary beside the Workflow tabs. In the hosted app the active workflow iframe
mounts the dock into its same-origin shell toolbar. Parked/background workers
cannot take over the visible dock. Standalone workflow uses its own toolbar.
The popup preserves the existing settings state/API and auto-sync change handler;
it closes on outside click/Escape, fits narrow viewports and cleans up its event
listeners on iframe exit. The two settings-only Retry and Download settings report
buttons are removed. Errors remain visible; changing a selection triggers a new
sync. Video tracking/download recovery controls are unchanged.

The panel explicitly states the existing creation limit: Ingredients, Lite,
portrait 9:16, one output. Applying other settings to Flow does not add support
for generating those combinations in SceneForge. No backend/CLI behavior changes.

Validation: real Chromium same-origin parent/iframe fixture checks collapsed
placement, four controls, auto-sync from the parent document through the existing
workflow API, verified/error statuses, absence of the two buttons, Escape/outside
close, parked-worker isolation and narrow-screen bounds. Existing auto-settings
and clip-recovery UI checks pass; all inline scripts parse. No live Flow calls.

## v46.56 — selected settings drive the original CLI

The settings panel now configures the generation request rather than trying to
click Flow's Settings trigger. Edits save locally, with explicit text saying they
apply when Create is pressed. No settings-only browser request is made, and an
old Settings-trigger failure is not displayed as a failure of this new path.
The compact dark panel uses segmented mode/aspect/output controls and a model
selector. Unimplemented multi-output choices are disabled; duration remains
Flow's default (workflow video validation is still eight seconds), download
quality is original, and no unverified PRO/ULTRA credit prices are shown.

Supported: Ingredients -> original CLI video r2v with one --ref; Frames -> video
i2v with the image positional argument. Both support portrait/landscape and
Lite/Fast. Quality is allowed only in Frames, matching the pinned CLI/SDK's
capabilities. There is no --duration or --resolution flag. No SDK/session override.

One pure options validator is shared by admission, preparation, CLI argument
construction and result metadata. Settings are snapshotted into the existing
request payload/ledger, checked against the prepared receipt, shown in the send
confirmation, passed to CLI and saved with the received clip. Non-default models
and ratios get accurate model identifiers. Backend ffprobe and frontend receive
validate the request's ratio; a landscape result is not rejected as portrait.
Later dropdown changes do not reinterpret an already-submitted result. Legacy
records without a settings snapshot retain the old portrait/Lite defaults.
Existing single-upload and download-only recovery paths are preserved.

Validation: eleven direct CLI process tests (including Frames/Quality and
Ingredients/Fast landscape, rejected Quality/Ingredients or multiple outputs);
real submit/prepare/receipt/CLI/ffprobe/done scenarios with local provider doubles,
including duplicate receipts and conflicts on changed settings; actual UI create
and receive functions verifying selected options and landscape import after a
later dropdown change; real Chromium panel tests verifying controls, capability
disabling and local-only editing; existing completed-video recovery API/file/UI
checks. Original pinned CLI source was consulted for argument/model support.
No live Flow generation or Windows installation was verified in this environment.

## v46.57 — early video IDs and live CLI stages

Original CLI defaults to WARNING logs, and SceneForge previously waited for
communicate() before examining any output. Enable the supported INFO/JSON log
settings and drain stdout/stderr concurrently while the same original CLI runs.
The pinned SDK already emits migrated.dispatch, submit_observed (or its adopted
submit variants), status, result and download events. No SDK/session override,
catalog guessing, extra Google RPC polling or generation command is introduced.

Only allowlisted events from this owned process are accepted. Confirm the
expected project from dispatch before adopting a migrated video ID; never treat
uploaded reference-image IDs as video IDs. Persist media/workflow IDs immediately
and expose them through existing job lookups while the CLI is still running.
Persist real status stages (submitted 6, running 2, done 3 per the pinned parser),
show the ID and real elapsed wait in the node, and keep the progress bar
indeterminate when the source provides no percentage. A late running event cannot
regress a completed stage. Final/download-recovery IDs must match the live ID.

INFO diagnostics are projected onto public event/ID/status fields; arbitrary
session/signed-URL fields are not retained. Warnings/errors and stdout remain
captured as before. Both pipe readers are canceled/awaited on errors so owned
process shutdown cannot race an outstanding read. Download-only recovery keeps
WARNING verbosity and its existing behavior.

Validation: 13 CLI cases, including a real child blocked before exit while its
video ID/status is observed, ignored image IDs and rejected mismatched final ID;
four monitor/pipe checks for project scoping, monotonic stages and sensitive-field
projection; actual submit/prepare/CLI/ffprobe/lookup scenarios proving durable
submitted IDs before process exit; actual UI sync/progress rendering and existing
configuration/old-download recovery checks. These use local fixtures, not live
Flow or Windows. Classic-host terminal events are supported, but early IDs rely
on the migrated-host events emitted by the user's pinned Flow CLI.


## v46.58 — clip grid, automatic receipt and explicit step estimates

Redesign only the reference-workflow node and its inspector. The original CLI,
account binding, request ledger, single-reference upload and download recovery
are unchanged. Existing clip planning supplies scene parts; no new splitting or
unsupported model/duration/watermark controls are added.

Group parts by scene, use small tiles above six clips, filter clips needing review,
and open a video/prompt inspector with version/source playback, 0.5x and loop.
Keep all imported versions. Warnings with timestamps are shown only when present
in existing local-review data, never invented identity detection. Quality approval
continues to check frame, prompt, timing and continuity; receiving a file is not
an automatic quality approval. The inspector's previous receive action is now
labelled approval, because verified files already attach to the originating scene.
Mark automatic receipt, display the video immediately in an open matching inspector,
and continue polling when the workflow document is hidden. Closed inspectors are
not reopened by receipt. Failed saves leave the job awaiting import instead of
claiming persisted success.

A per-clip percentage is explicitly labelled an estimate by stage (image 20,
submit 30, waiting 40, generating 60, download 85, verification 95). Real UI
percentages are labelled as such and capped below 100 until imported. Unknown,
missing, failed and stale states receive no fabricated completion bar. 100 means
the verified file was imported/saved. Aggregate count is based on actual clips.

A user-confirmed session-only queue sends ready clips one at a time, retaining the
original once-only per-request generation. It stops after uncertain or failed
results, changed room/account/settings/inputs, or user cancellation; it never
replays a generation. Continuity-dependent parts wait for their normal prerequisite
approval. No queue is silently resumed after restart. Credit amounts and logo
removal are not presented as working capabilities without provider evidence.

Validation: actual full workflow in Chromium with intercepted API responses and
real local 8s MP4: tile/filter/detail edits do not submit, durable IDs/stages are
rendered, receive attaches automatically to the right scene without approval,
repeated reads do not duplicate, approval remains explicit, missing is translated,
exactly two queue requests for two clips, first uncertain result stops the rest.
Settings/configured create/import and existing download-report checks retained.
No live Flow or Windows installer verification.


## v46.59 — locate original GFlow and release terminal inspector controls

User report: failed/checking_prepared, zero original-app candidates, no CLI or
upload attempt. This is local installation discovery, not a Google rejection.
The prior finder required an exact app.py digest and stopped at depth three.
Use successful same-account ledger history before bounded scanning, verify its
current email/profile, and recognize updated upstream wrappers using the actual
CLI module or pinned CLI requirements. Keep original digest compatibility, search
up to six levels/3000 folders, include both Windows Downloads registry values,
OneDrive Downloads, current app/runtime location and Desktop. No new SDK worker,
session override, dependency install or generation retry is introduced. Multiple
matching installs without history remain ambiguous; never choose another account.
If the original runtime has been deleted, discovery cannot recreate it; the error
explicitly says to restore the known working installation.

Persist discovery outcome and report submitted=false only for this proven
pre-launch failure. The inspector previously updated its progress section but
kept stale running labels and disabled controls. Rebuild the matching open
inspector on a pending-to-terminal transition; show the actual failure reason.

Validation: 20 CLI/local-process tests including changed wrapper/deep nesting,
successful history outside Downloads, wrong-account history rejection, ambiguity,
missing install and rejection of a generic wrapper without the CLI. Actual
backend submit/lookup verifies missing install fails with submitted=false and no
upload/CLI call; configured happy paths still complete. Actual Chromium verifies
running-to-failed refresh exposes the error, releases buttons and removes the
running overlay. All local fixtures; user Windows disk/Flow not directly inspected.


## v46.60 — offline original CLI/runtime in the updater

Default generation no longer resolves a GFlow installation in Downloads or uses
system Python. The update embeds the exact original Windows portable archive
(revision 09ab05b190ddad0b3bbed80439ecbc6739d5abce, SHA256
03ae9541fefa55e4f917f87db794cd2b26f61d5d215a754b333b5dfc3d686292).
The archive has only application/runtime files, no account/profile data. All
upstream package files and licenses remain intact. The existing verifier extracts
runtime only from the LOCAL embedded archive; no network/pip/install step occurs
at application runtime. Explicit developer path overrides remain optional; normal
UI usage never scans Downloads.

Invoke the unmodified original `python.exe -m gflow_cli` with the existing argument,
stdout/stderr, progress, identity and file-validation paths. Release the managed
browser before granting the CLI ownership of the same selected profile. An NTFS
junction (ordinary filesystem alias, no cmd/shell/admin) maps its profile name
under private Data/flow-cli to the existing managed profile. POSIX fixtures use a
symlink. Validate profile/email and never replace an alias pointing elsewhere.
Write only the original CLI's account/browser-strategy metadata, not cookies or
session tokens; existing session files are never copied or rewritten. This CLI
uses system Google Chrome for these existing Chrome profiles; unsupported browser
strategies fail before generation rather than overriding SDK session methods.
No custom SDK worker, session override or executable-path monkeypatch is used.
Download-only recovery for new bundled requests uses its saved private home and
bundled interpreter, with the same ID association checks.

The generic managed updater originally had a small fixed resource slot. Append a
new readable data resource to its final PE section and update only section/CLR
resource sizes and pointers. Preserve all original code, entry point, imports,
metadata and old resource bytes. Validate the resulting PE, exact resource ZIP,
all embedded hashes and unmodified upstream archive. Windows execution remains
unverified in this Linux environment; local process/real-backend fixtures verify
bundled selection, no Downloads calls, account isolation and download recovery.


## v46.61 — one settings location, all missing clips and responsive node updates

UI-only patch requiring .60; bundled CLI/runtime/session integration remains byte
for byte unchanged. Remove the node's duplicate settings footer/button. Keep the
single shared Flow settings dock in the workflow toolbar.

The node's create-all action targets missing, never-attempted clips across the
whole node, independent of the current filter. It confirms once, writes missing
prompts through the existing Gemini pipeline, then uses the existing durable
intent/signature/configuration checks and single-send CLI path sequentially.
Completed clips and uncertain/previous failed requests are not regenerated.
Continuity parts remain queued until the previous clip has been manually approved;
room/account/frame/timing/settings/user-prompt changes stop further submission.
No silent draft rebinding or retry is added.

Fix redraw costs rather than introduce a new canvas framework. Compute row state
once per paint, keep keyed thumbnail elements, patch changed DOM only, and skip
identical view snapshots. Materialize diagnostics only when the user opens them;
keep their selected scene in sync. Preserve video playback and image nodes during
status polling. Identical job responses no longer clone/write the whole project
and assets into IndexedDB. Changed states and durable pre-submit intent are still
saved. Actions yield a browser frame for immediate button feedback and update only
the Veo node; receipt/approval updates editor readiness without rebuilding all
canvas nodes. Layout/wires update only when node height changes. The old 12-second general
workflow poller also considered managed Veo jobs active, then called an empty
legacy recovery pass that redrew the canvas. Exclude managed Veo jobs there; the
Veo poller remains their sole polling owner.

Reproducible local Chromium benchmark (`scripts/analysis/measure_veo_node.py`):
18 distinct ~284 KB base64 JPEG references. Baseline refresh 62.9/64.3/65.2/69.5 ms,
click handler 42.7 ms, thumbnail elements replaced. Optimized refresh
6.6/4.1/4.4/2.7 ms, click handler 0.9 ms, thumbnails preserved. These are local
fixture measurements, not a claim about the user's machine or Google latency.

Actual browser tests cover unchanged polls with zero saves and preserved images,
lazy diagnostics, the sole toolbar settings control, create-all from an empty
review filter, missing prompt preparation, skipped completed clips, no whole-canvas
redraw during queue execution, automatic import, uncertainty stop, and manual
approval before submitting continuity part b. Existing settings/configured import
and download-report checks remain. No live Flow or Windows installation test.


## v46.62 — make the legacy-history gate actionable

The user's 4.2s part-a inspector was disabled by legacyUnresolved(), while the
new inspector exposed neither the old review action nor a way to reconcile its
receipts. Do not erase that history or assume it never submitted.

Read old receipts automatically when opening the blocked clip (rate-limited),
using read-only existing diagnostics/legacy receipt endpoints. Auto-release only
matching request/store/room/scene/part evidence with submitted=false and terminal
failed/not_submitted state. Refresh account status after that authoritative update.
Missing, unknown, different-store or mismatched-scene evidence does not release it.
Keep explicit negative receipt evidence in the old job; never delete/reuse its ID.
The core create path also performs this read for queue callers before its guard.

If legacy history is the only blocker, enable a contextual Check old attempt then
create button. It reads first; unresolved history requires the existing user
review/acknowledgement, followed by the normal new-generation confirmation.
Expose read/review/history actions in the same inspector, preserving the old
request and warning about possible additional credits. Cancelling sends nothing.
Other prerequisites (frame, prompt binding, account, active or uncertain current
jobs) remain enforced. Receipt updates patch controls without losing typed text.

Validation: full Chromium fixture reproduces a 4.2s clip with legacy unknown jobs;
negative receipt auto-unlocks without any POST, genuinely unknown and wrong-scene
receipts remain unresolved, cancelling create confirmation sends nothing, explicit
review persists without deleting history, then create submits exactly one new ID
and imports its video. Prior queue, continuity, no-redraw, settings and receipt
checks remain. UI-only update on .60+, no engine/runtime/session changes. Local
fixtures only; Windows/Flow live execution not verified.
