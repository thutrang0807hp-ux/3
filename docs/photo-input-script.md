# Ảnh đầu vào và Kịch bản · Từ ảnh & ý tưởng

The two nodes use the existing room, files, scene IDs, storyboard and merge workflow. No new pipeline node is added. The old formula node is folded into the script AI panel.

## References

The product box is primary. It has a file picker/drop target, current-product library import and add-more controls. People/background are optional. Named people live in `refs.person.people`, while original image records remain in `refs.person.images` with `personId`. Each person has an optional primary image. The reference prompt supplies ordered named groups; identity is still a provider output requiring review, not a guarantee. Legacy refs keep their exact original signature until explicitly edited.

Uploads preserve original files, create a bounded thumbnail, compute SHA256, enforce PNG/JPEG/WebP, 15MB/file, 40MP, 12 images/group and reject room switching during upload. Person controls support multiple images/primary selection/removal. There is always an add target. Product imports clone only the product group into this room, leaving chosen people/background alone. Saving refs to the product library merges by known hash, file key or identical preview and preserves existing library images; other room refs remain private copies. Empty product refs block actual image/video generation, including storyboard frames, but do not block writing, pasting or saving scripts.

## Plain script and scene reconciliation

`photoDraft.scriptInput.raw` preserves the exact document; `applied` tracks the last scene application. Blank lines split scenes; a single newline stays inside its scene. Leading `[Cảnh ...]`/`Scene ...` or `Cảnh N:` annotations remain in raw, enter stage directions and are excluded from speech. No synthetic scene separators enter the source. Parsing runs locally after 300ms. Original imported rooms are not reparsed just by opening/flushing.

Exact unchanged scenes match first, including reorder and recoverable removed scenes. Equally sized unmatched edits retain existing IDs and durations. Ambiguous insert/delete gaps get new IDs; old scenes are archived instead of guessing away media. Existing images/clips and frozen part plans remain. Changed scenes retain media for comparison; changed dialogue clears per-part text overrides. Reordering or editing invalidates the assembled draft plan/final approval; the existing editor timeline is untouched. Unknown active video receipts block affected edits while the raw draft remains saved. Removed/previous scene versions are stored in `scriptSceneArchive`, with explicit recovery controls. Undo restores prior raw text through the same reconciliation, not by rolling back the entire room over newer jobs.

The inline library uses all active script/formula items (the legacy formula-only bridge is not reused). It searches title/body, initially filters current/shared product items, shows only recorded positive feedback, copies scripts with source snapshots and records usage separately. Editing the copy does not mutate its source. Formula selection opens the inline AI panel without sending. Save to Kho creates a raw V4 script, no model calls. Clipboard permission failure focuses the real textarea for normal paste.

## AI and optional storyboard

`POST /local-api/ai/script-library` adds action `write` with idea, product name, 15/30/60-second approximate target and optional formula. It uses the configured AI routing and durable request ledger, with expected store/source checks. Output is one validated plain-text document, at most 60 scene blocks. The prompt treats product/idea/formula as data and forbids fabricated efficacy/prices/testimonials.

There is no fabricated streaming animation. The UI waits for a real response, stores its receipt before sending and flushes managed storage. Stop only stops receiving into the UI; it does not claim to cancel a remote job. A late response remains an explicit candidate. Read-only recovery uses the same request; unknown requests cannot be silently resubmitted. Confirmed `submitted:false` failures can be dismissed locally and retried explicitly after fixing the connection. Candidate acceptance preserves the previous raw text. Product photos are not sent by this text-only action.

“Tiếp → Storyboard” applies text and focuses the existing optional storyboard node. It does not send image generation or auto-approve anything.

## Verification

- `scripts/app-shell/check_photo_input_script.py`: actual Chromium + IndexedDB, raw/annotation parsing, IDs/media/reorder/archive, pending receipt edits, V4 save/search/source copy/usage, multiple people, dedupe/library merge, product-only generation guard, explicit AI wait/stop/recover/accept and no-send storyboard handoff.
- `python -m local_engine.check_script_library`: actual HTTP routes + Chat adapter/SQLite ledger against an SDK fixture; split/topic regression, write validation, same-receipt recovery, no duplicate cloud call and no paid fallback.
- Storyboard, production and real FFmpeg merge regressions retain their previous successful outcomes; see `artifacts/input-script-*-regression.log`.
- Offline focused preview: `scripts/demo-web/package_input_script_preview.py`, based on the real embedded photo UI with an isolated sample document, no provider calls.

Online generation/accounts and Windows have not been exercised in this environment. Targets are estimates, not measured TTS duration. End-frame support remains governed by the existing model contract.
