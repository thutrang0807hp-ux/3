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
