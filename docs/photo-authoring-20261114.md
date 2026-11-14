# v46.128 · Photo script styles and layered prompts

Completed: the photo-to-video script node's AI writing panel now offers general, advertisement/introduction, problem–solution, how-to, review/advice, story and offer/close formats. Optional user-confirmed product facts are saved with the draft. Each explicit Write creates an immutable request body containing the selected kind and facts. Recovery uses that original body even if future preferences change. Existing script text is untouched until the user accepts a candidate. The backend rejects unknown/malformed kinds and oversized/non-string facts. Instruction text for already-sent legacy receipts without the new fields is unchanged. Review does not authorize invented firsthand experiences; offer does not authorize fictitious prices, scarcity or promotions.

Photo prompt layering is now opt-in for existing rooms, under Storyboard → Phong cách chung. New drafts default on. It separates image identity/wardrobe/product constraints from static composition/light/material detail, and motion planning from appearance and clip timing. Existing reference-order mapping, fixed IDs/dialogue and provider routing are preserved. Manual camera/composition text remains before the additional instructions. Explicit toggling changes the image fingerprint and marks prompts for review without deleting image/clip versions or dispatching jobs. Editing the shared look preserves the layer preference. Generation directions are English; no claim is made that the existing photo branch now has a new bilingual editor.

Tests passed: three backend admission/legacy-contract tests; actual Chromium authoring UI fixture (format/facts payload, unchanged script, frozen recovery, legacy opt-in, manual directions); existing storyboard-guide and photo-Veo lifecycle fixtures. Static script parse and updater embedded-source/checksum verification pass. No live AI generation, visual-quality comparison or Windows updater execution was performed.

Motion Studio remains pending its real uploaded-video editing transport. Batch-image prompt rollout is not part of this release. No new models or dependencies are added; the package remains cumulative with the pinned Omni SDK from .127.

Package: SceneForge-Update-20261114-v46.128-Photo-Authoring.exe

SHA-256: f76891597ac99f96f5385ff27f2177091704ab02020d87eec22be4269810ce7b
