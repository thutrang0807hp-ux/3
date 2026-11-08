# SceneForge .77 — Veo receipt refreshes assembly node

Requires .76. Close app, run updater, reopen project. No video generation needed. This fixes a concrete UI refresh defect; does not claim a backend-only Flow result has already downloaded. If only provider status is done, explicitly read existing job to import its file.

Root cause: receive()/acceptClip() called refreshVeoHandoff(), which searched #node-merge .nodeBody > p. Current reference-node design uses .ndBody and dynamic header/tiles/footer; no current assembly renderer ran. Data contained the clip/chosen ID while handoff DOM kept old counts.

Expose room-bound SFReferenceNodes.refreshHandoff() that renders only assembly node and requests layout. Receipt (new and existing/idempotent) plus explicit acceptance invoke it. Update approved-count run bar separately. No full render, prompt/image reset, new API generation, auto-quality approval or overwrite of existing Dựng. Existing chosen version, frame/prompt/duration/continuity/file checks remain. Existing editor gets its prior explicit new-version notice via refreshed snapshot.

Validation: check_veo_redesign_ui.py real MP4 metadata/import via intercepted CLI endpoints; 1/9 assembly tile/header/footer updates immediately without another render; no implicit reviewDecision and readyCount remains 0 until explicit accept; repeated read repairs a deliberately stale header without duplicate file; current-room guard; frame/Veo DOM identity retained; existing editor notice appears and no workflow-open-editor message sent. Broader Veo checks retained. Not live Flow or Windows updater validation. Payload only workflow.html.

EXE: SceneForge-Update-20261108-v46.77-Veo-Assembly.exe
SHA256: 0af2ecefd7888fbbe9ea6f1493e0541ab44498fcebab5e24fbaa337f20ca7634
