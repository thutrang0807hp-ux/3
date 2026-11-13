# Lightweight motion and video-edit research · 2026-11-13

## Scope

Research only. No model weights, SDK installation, account access or paid generation. No new provider or UI controls were added.

## Primary sources inspected

Google Gemini Cookbook, HEAD observed as `6c416d766328d125774e21f282e59dfdf12049c9`:

- https://github.com/google-gemini/cookbook/blob/6c416d766328d125774e21f282e59dfdf12049c9/quickstarts/Get_started_Omni.ipynb
- https://github.com/google-gemini/cookbook/blob/6c416d766328d125774e21f282e59dfdf12049c9/quickstarts/Video_understanding.ipynb

The Omni notebook explicitly identifies `gemini-omni-1.2-flash`. It documents uploaded-video editing through Files + Interactions API, image references alongside uploaded source video or previous interaction for character/prop/style edits, chronological prompts such as [0-3s], and concise targeted edit instructions. It separately describes short reference videos for new generation; those are not the same role as the source video being edited. Its reference-video restrictions must not be confused with editing-source input restrictions. Availability can depend on region and account. The notebook is documentation, not a generation performed in this session.

This corrects the earlier working assumption that external models might be necessary for all character-replacement workflows. Omni's documented API surface is relevant directly. It does NOT establish Flow UI or the installed SceneForge GFlow transport supports the same input roles. It also does not establish TobyFlow's implementation or motion quality.

## Supplemental prompt design

GFlow source reviewed at `96339be1b59f6cd1963c28cf076c317f89c37525`:

- https://github.com/ffroliva/gflow-cli/blob/96339be1b59f6cd1963c28cf076c317f89c37525/src/gflow_cli/tools/builtin/reverse-engineer.toml
- https://github.com/ffroliva/gflow-cli/blob/96339be1b59f6cd1963c28cf076c317f89c37525/docs/PROMPT_EXPANSION.md

Useful design: distinguish subject, action, context, camera and appearance. The built-in reverse-engineer takes textual descriptions, not raw video analysis by itself. Creative-director is an LLM-based text expansion tool, not motion control. Its tendency to add camera/brand/style flourishes is inappropriate for strict reference fidelity; do not adopt that behavior indiscriminately. It requires separately configured model access; studying its prompt structure does not imply adding API-key setup to the existing Gemini Chat workflow.

## Recommended application design

Preferred investigation: source scene clip + approved identity/product reference images + a short edit instruction, using a verified video-edit-capable transport. Preserve motion, camera and environment as requested; evaluate actual output, never promise exact motion or unchanged pixels. Flow support must be checked before enabling this path; API billing and API credentials are separate from browser-session Flow credits.

Fallback using the existing generation path: video-understanding model extracts observable time ranges, actor motion, hand/object interactions, camera motion and uncertainties. Produce a compact time-ordered prompt anchored to approved references; do not invent product features or change camera style. This approximates choreography, not frame-exact motion transfer. Retain user prompt edits and require explicit generation action. No automatic retries to obtain a better visual result.

For either path, validate a short product-handling scene before integration claims: identity, clothing, product label/geometry, hand contact, chronological action and camera behavior. No live benchmark has been run.
