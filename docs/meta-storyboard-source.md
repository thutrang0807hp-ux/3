# Meta AI as a storyboard image source

The photo-to-video workspace now offers **Meta AI** alongside Gemini Chat and the retained manual Muse option. This reuses the existing Meta browser adapter from batch image generation. It does not infer that a Muse session/cookie works at Meta AI, does not send Muse cookies to Meta, and does not claim corporate ownership from a hostname.

In a local installation: Sources for this room → Meta AI → Connect Meta AI. The account action opens the existing Meta account manager and browser login. Stored sessions, account selection and image concurrency are shared with batch images. Source selection remains staged until Done. The source pill and bottom next-action status reflect Meta connection checks. Both creative account statuses are read so an existing Meta connection can be displayed before choosing it.

Only **images** change source. Scene-prompt writing remains Gemini Chat, named explicitly in the source panel, automation plan and sending preflight. The script node's separate text writer still follows its existing Settings routing. No automatic text fallback is introduced.

## Dispatch and receiving

- Overall images use Meta's `web-images/jobs` with source `meta`, aspect `16:9`, original reference files, selected-account token and an explicit confirmation. Frame images use the same endpoint with their exact scene/part/input fingerprint and default portrait aspect.
- Meta jobs retain `webimage-UUID` request IDs in the existing room job collection; Gemini jobs retain `gchat-UUID`. Routing for reads/files uses that captured identity, not whichever source is currently selected. Switching source does not resubmit or move an old job.
- Jobs are persisted/flushed before submission. Changed source/account selections invalidate a preflight. Source changes are blocked during a frame send/read. Ambiguous jobs remain pending and do not trigger automatic retries or account switching.
- All returned Meta image alternatives (up to the adapter's eight-image limit) are imported as separate actual-file versions. The first becomes the default candidate; other versions remain selectable. Repeated receiving deduplicates by request ID and result index. Input changes retain old images and prevent silently applying stale frames.
- Whole-storyboard receiving shares the same multi-version importer. Dialogue and the existing timeline are not rewritten. Gemini receiving continues to use its original endpoint and job IDs.
- Provider/source/account/room/scene metadata and logs stay attached to the original job. When available, a validated HTTPS Meta conversation URL is retained and shown in sent-job history for manual reconciliation. No arbitrary URLs from provider output are offered as links.

Muse video remains connected through the existing separate Muse adapter. The manual Muse image option is retained for old rooms; no unverified image protocol is invented for that SDK.

## Verification and limits

`check_meta_storyboard.py` runs the actual application/IndexedDB in Chromium with controlled HTTP receipt and PNG fixtures: Meta account button and staged selection, stale token no-send, original references/scene IDs, provider-pinned recovery after source changes, multiple original-file versions, dedupe, whole overview receiving, unchanged dialogue and the explicit Gemini text route.

`python -m local_engine.check_web_images` uses real Playwright against intercepted login/generation pages: guest rejection, encrypted isolated sessions, one send click, new-image detection, reference upload, original PNG download, selected account, duplicate and unknown no-replay. `check_web_images_api` covers real HTTP/SQLite/storage promotion and lifecycle safeguards. Existing storyboard, production, clip and plain-script browser regressions pass.

**No online Meta/Muse account was supplied or exercised.** Live service selectors, region/account availability and generation need verification on the user's local machine; an authenticated session is not proof of a successful generation. Static GitHub Pages/offline previews show the UI only and cannot open the local account browser or generate images. Limits/charges remain those of the service; this adds no quota bypass.
