# .179: keep the old send step, use the repo's receiver

User scope: retain the previously used source/reference upload and prompt send; replace image receiving with test-gemoni-chat's receiver. Preserve all per-scene UI, V6 prompts, progress, dimensions, common instructions, references and logo cleanup.

`scene-send.js` contains the exact attachment block from the existing SceneForge `frame-studio-tab.js` (DataTransfer, file-input change, custom upload-preview elements and filename checks) and the exact DOM `sendMessage` block from its vendored `studio-gemini-original.js` (focus/execCommand/input event/send button). It uses the same image instruction and ratio text. The narrower .178 setInputFiles upload waiter is removed, not retained as another fallback layer.

The bridge returns a dynamic locator for newly added assistant replies, equivalent to the old sender's `latest()` callback. Existing reply nodes are excluded. This prevents a transient thinking reply from fixing the receiver on an earlier placeholder when the actual image reply arrives later. There is one send; wait/read never resend the prompt.

The upstream `waitForImage`, `downloadFromGemini`, `downloadImage`, `copyImagePixels`, `saveResult` and remaining source functions remain byte-for-byte from test-gemoni-chat 75f43c9. They read the response handed over by the existing sender. Source Python workspace/start/request/create_image/close and hidden browser profiles remain as in .178. No model, external API or scene editor change.

Validation:
- Source comparisons pin the exact old upload and DOM-send blocks and exact upstream image wait/download functions.
- Actual Node/CDP + production queue tests use `uploader-file-preview` custom elements with no filenames/ARIA. The old .178 preview selector sees zero matching previews, while the restored selector sees both uploads and sends exact file bytes and >20k prompt.
- The fixture supplies a thinking response before a separate final image response; the repo receiver receives the correct final image. Tests include repeated scenes on one account, two accounts concurrently, closing unrelated Chrome, failure then later success, cached completed-file recovery without resending and original-file validation.
- Frontend scene UI and logo backend are pinned unchanged from .178.

Gemini/auth are fixtures. Actual Google-account generation on Windows has not been run here; this is not a claim that all live timeouts have been reproduced. New requests use this send/receive split; old remote results are not guessed or regenerated.
