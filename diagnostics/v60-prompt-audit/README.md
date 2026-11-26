# V6.0 prompt audit

The supplied UTF-8 document is preserved verbatim at `scripts/prompts/universal_reference_image_edit_v6_0.md` (30 sections, six dynamic slots). Only slot contents are filled; headers and static text stay intact. No provider, model, browser sender, image encoder or UI changes.

`actual-node-request.json` captures the actual `gemini-chat/jobs` body prompt and manifest from the production Frame Studio UI in Chromium with provider replies mocked. Seven distinct fixture images were checked byte-for-byte in source / product / primary person A / primary person B / secondary person A / clothing / environment order. One image request, no writer request, one imported fixture result, no duplicate dispatch. This is not a live Gemini quality test.

`multi-person-prompt.txt` is the unit-fixture comparison prompt. Tests cover all 16 role combinations; all static sections; hands/nails; per-person image groups; primary/secondary; clothing wearer; environment lighting; unselected roles; placeholders; missing text; and incorrect bindings.

V5.2 restoration sources remain unchanged: `scripts/prompts/universal_reference_image_edit_v5_2.md` and `scripts/ui/frame_universal_v52.js`, also included under `app/scripts/prompts` and `app/scripts/prompt-backups` in the .174 payload. Baseline release/source: v46.173, commit fae0af5. These backups are not concatenated into requests. A restoration should be published as a new version using the saved module and matching integration, without downgrading other fixes.

Existing group descriptions identify people/garment targets. Multiple-person positional defaults use source left-to-right order only when descriptions do not specify another target. Clothing without a wearer description when multiple person groups are active is blocked before sending. References do not provide a deterministic guarantee of generated likeness; that remains a model result to review.

Unfinished V5.2 jobs retain their submitted English prompt for receipt/signature checks; newly prepared jobs use recipe marker 174. Completed/approved frames and historical prompt records are retained.
