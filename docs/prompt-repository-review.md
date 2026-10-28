# Read-only GitHub prompt mechanism review · 2026-10-28

Initial review was discussion-only. The user subsequently authorized implementation; current application changes and tests are described in [prompt-pipeline.md](prompt-pipeline.md). No third-party runtime or model from these repositories was installed/executed. Public repo source was cloned to /tmp and read statically. GitHub search API was unavailable through this runner; these are three directly inspected examples, not an exhaustive search or ranking.

## Wan2.2

Repository: https://github.com/Wan-Video/Wan2.2
Inspected commit: 1ea34ff48f87168174e12956e200b1d908b1c5ff
Files: wan/utils/prompt_extend.py; wan/utils/system_prompt.py
License at snapshot: Apache-2.0.

PromptExpander selects instructions by task/model/language (text-to-video vs image-to-video). DashScopePromptExpander sends a system instruction and user text with the supplied image to a multimodal model. QwenPromptExpander is an alternate implementation. The English I2V rules emphasize dynamic action/camera rather than repeating static image details. Some T2V/empty-I2V instructions allow adding actions/details. Borrow task separation and explicit image conditioning; do not copy speculative expansion rules or Wan-specific length limits into a source-faithful Veo workflow.

## CogVideo

Repository: https://github.com/THUDM/CogVideo
Inspected commit: 7a1af7154511e0ce4e4be8d62faa8c5e5a3532d2
File: inference/convert_demo.py
License file at snapshot: Apache-2.0; check model weights separately if ever used.

convert_prompt combines system instructions and simple input. The text path includes examples and a configured LLM; the image path sends user text plus the actual image to gpt-4o. It returns the generated text for video inference. It has a retry loop and fallback to original text. Borrow the explicit text+image input/output separation, not the retry/fallback behavior or model-specific cinematography constraints. No need to adopt its provider or install its video model.

## ViMax

Repository: https://github.com/HKUDS/ViMax
Inspected commit: fd4b72e7731be6e5f88486206d25ea59849b0285
Files: agents/storyboard_artist.py; agents/reference_image_selector.py; interfaces/shot_description.py; pipelines/script2video_pipeline.py
License at snapshot: MIT.

Storyboard structures separate first-frame description, last-frame description, motion and audio. ReferenceImageSelector selects reference indices and produces text_prompt. The pipeline prefixes Image 0/Image 1 labels bound to the corresponding ordered reference files before image generation (around lines 415–435). Video generation waits on required frame events and sends motion_desc + audio_desc with those generated frame paths (around lines 504–532). This is a concrete example of a writing model producing structured content while code binds files and schedules provider calls.

Borrow explicit reference-index binding and frame→motion dependency handling. Do not import its multi-agent stack, candidate-image selection, unrestricted inferred details or extensive intermediate-result storage into SceneForge by default. The requested app keeps Gemini, current workflows and minimal required project/receipt state.

## Applicability

These repos demonstrate prompt rewriting and pipeline orchestration. They do not demonstrate that the same prompts work well with the user's products or with live Gemini/Flow/Meta/Muse accounts. They do not supply a universal account-login mechanism. Accounts are provider access; writing quality comes from instructions, evidence and validation. Authorized integration adopts these design principles with independently authored SceneForge instructions and the existing providers, without copying third-party runtime code.
