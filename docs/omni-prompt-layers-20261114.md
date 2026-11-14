# SceneForge v46.120 · Omni and layered sample prompts

## Completed code

- Added the pinned gflow-cli 0.98.0 wheel (SHA-256 f35eedf1e167e5cf5e2837ad2a7d3455f1bc1c205b22ea98a350f3dbaebb77d3), with its original MIT license inside the wheel. Core routing source files match reviewed upstream revision 96339be1b59f6cd1963c28cf076c317f89c37525. All base dependency requirements match the existing Windows archive's installed versions, including python-dotenv.
- The private runtime replaces only its CLI package and distribution metadata, using staging, checksum validation, rollback and an install lock. Existing interpreter, dependencies, browser profile and project data are not copied to a second runtime. Added payload is about 1.7 MB. No model weights or new accounts are included. A crash leaving an install lock needs diagnosis rather than automatically deleting a possibly active lock.
- Omni is explicitly routed to `omni-1.2-flash`, with --duration 8. Added the bundled runtime's actual Lib/site-packages path to preflight. The backend catalog declares both orientations for four single-clip models. New sample/photo settings default to Omni in frames mode; existing explicit settings are retained. Older explicit engines that lack the alias stop before generation. A new verification key prevents previous engine success from marking the new SDK live-tested.
- The sample branch writer now uses layered, original SceneForge instructions for reference responsibilities, source geometry, visible identity/clothing/product detail, grip/occlusion, physically compatible motion, source lighting, low-noise natural detail and self-checks. It does not assume that writing 4K sets actual output resolution.
- English-only generation directions and matching Vietnamese review text remain separate. Inspectors provide a Vietnamese revision editor and an explicit AI optimize/update action for image or video prompts. The English editor is in a collapsed section. Writer-only actions do not create media. Compatible Vietnamese user notes are given to the writer rather than appended verbatim to AI-generated video prompts; exact Vietnamese spoken dialogue remains a deliberate audio input.
- Older applied prompts remain current if only the template version changed. Manual ownership and prior approved files are retained; explicit rewriting is separate from generation. New reference notes are supplied as writer context, while generation reference bindings use stable English role labels.

## Verification

- 37 existing GFlow adapter/CLI/worker tests passed.
- Six Omni routing/runtime tests passed, including actual wheel extraction, idempotence, checksum rejection, rollback and profile/dependency preservation.
- Chromium check_prompt_layers.py passed: actual image attachments, old-template/manual protection, explicit writing, Vietnamese revision context, English generation text, no Flow generation POST, inspector UI and retained approved media.
- Existing check_frame_identity.py passed (ordered original image bytes, clothing priority, source/appearance distinction, invalid/missing anchor guards).
- Existing check_photo_veo.py passed (single and serial jobs, actual MP4 import fixture, wrong room, ambiguous response and cancellation guards).
- Embedded script parsing and package byte/checksum verification passed.

These are local fixture tests. No live Gemini/Flow request was sent, no credits were spent, and Windows installer/runtime execution was not tested. Actual fidelity, noise and sharpness improvements are not yet demonstrated. Actual 4K controls are not added by this patch. Browser status-route 404s in static fixtures are expected.

## Remaining work, not represented as completed

Motion Studio is the agreed name for the separate source-video editing branch. Its Flow source-video + image attachment path still needs implementation and live input verification; the new branch is not enabled by this release. Script categories, layered prompt rollout to photo/storyboard/batch-image workflows and quality comparisons are also pending, rather than silently changed here.

## Package

SceneForge-Update-20261114-v46.120-Omni-Prompt-Layers.exe

SHA-256: 6ec34b4d3d0c04cae096a6501d6c42d838c41767b33f16c596542435172311e4
