# SceneForge .115 — Real batch source entry point

Existing batch endpoints already route Gemini Chat gchat request IDs to gemini-chat/jobs and files. No new backend or simulation-as-real path added. Source chooser now defaults to Gemini Chat when no explicit saved choice exists, persists preferredSource, gives simulation an explicit valid value and labels it as a UI test. Explicit simulation choices survive reload. Source hint explains real send steps and scope to new prompts. Old queued jobs retain their immutable bound source; opening/changing source never dispatches generation. Account availability=false is shown as unavailable, and enqueue toast names real run action correctly.

New optional preferredSource validated during batch load. Same script embedded in index and studio. Existing consent/checkpoint/account-token/receipt/unknown recovery gates remain in place. No online send performed by this development task.

Validation: scripts/analysis/check_batch_source.py runs Chromium with real library HTTP/SQLite and IndexedDB plus intercepted Gemini provider. Default real source, explicit source persistence, old simulation job isolation, no send before confirmation, one image POST, actual PNG file stored with Gemini provenance, reload without resend and explicit simulation restoration all pass. Provider website selectors and real account generation not verified here.
