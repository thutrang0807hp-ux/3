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
