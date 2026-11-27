# Flow reference comparison — 2026-11-27

Read-only comparison; no runtime or release modifications.

Reference: https://github.com/thutrang0807hp-ux/5gdfgfd at 09ab05b190ddad0b3bbed80439ecbc6739d5abce (fresh shallow clone).
SceneForge reviewed: 0a17548 (.190).

| Boundary | Reference application | SceneForge |
|---|---|---|
| Entry | app.py build_args/execute invokes python -m gflow_cli immediately | SimpleFlow.run invokes restore and assert_ready before flow_gflow_cli.generate |
| Browser | README and execute describe normal browser with Windows minimize watcher, not headless | BackgroundFlowSession.launch_background uses headless=True |
| Identity | CLI handles its selected profile/auth | Added AccountWebSession -> BackgroundFlowSession checks WIZ email in page before CLI; .190 adds bootstrap-script fallback |
| Profile | portable/MO-UNG-DUNG.bat sets GFLOW_CLI_HOME=data/profiles | flow_cli_bundle.prepare_profile aliases selected SceneForge profile into data/flow-cli; does not automatically use reference application's profile |
| Generation | video t2v | video r2v or i2v with approved image, selected project/model; reference upload/preparation precedes generation |
| Runtime | portable bundles original 0.92.1 SDK per earlier verified archive review | bundled runtime upgraded by flow_omni_runtime with 0.98.0 wheel |

Actual call sequence:
SimpleFlow.run -> restore -> AccountWebSession.attach -> BackgroundFlowSession.attach [reported failure] -> native project/preparation -> receipt validation -> flow_gflow_cli.generate -> CLI subprocess.

Report flow-b3b6f824-a1e1-4c53-94e0-a49a90260488: failed/opening, identity-verification timeout, native_inputs/generation_engine/cli_discovery/provider_task all null. It demonstrates failure at the added headless identity boundary, not a CLI generation failure. Reference success is consistent with this because reference does not execute that preflight. It does not prove headless is the root cause: need current page origin/readiness and nonsecret identity-probe result from the failing machine. No live user session accessed.

Next implementation should align browser/profile ownership with the CLI, eliminate redundant browser initialization where possible, retain account binding and correct approved-frame/project association, and test the complete create-button-to-subprocess boundary (not only the parser). Do not silently switch r2v/i2v to t2v, skip account checks, or claim generated-video success from fixtures.
