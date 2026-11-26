# Gemini native transport (.175)

Requested behavior: close the ordinary Gemini tab/Chrome while SceneForge continues sending the frame prompt, uploading the source/reference images and receiving the result through an app-owned hidden browser.

Based on the native profile/headless and download workflow in https://github.com/thutrang0807hp-ux/test-gemoni-chat at commit 75f43c9 (`gemini-try-on/browser_bridge.py`, `runtime/gemini.mjs`). The async Python port uses the existing Playwright dependency rather than adding a second Node runtime. The original sender remains available for saved extension accounts.

Sign-in: Settings -> Accounts -> Gemini Chat -> Đăng nhập Gemini chạy ẩn. Enter credentials in the ordinary app-owned Chrome/Edge profile. Close that sign-in window, or use the explicit finish button. Verification then opens the same persistent profile headlessly. No Gemini API key, exported cookies or SDK auth import is used on this path. The newly verified native account is selected explicitly by this user-initiated sign-in. Extension discovery does not replace an active native account.

Transport: same existing submit API, queue, account locks, receipt IDs, original files/order and V6 prompt. Native image requests accept the full validated prompt (up to the existing 160k API limit), with up to 8 source/reference images. The image download sequence follows the reference repo: authenticated download button, authenticated browser request, rendered canvas pixels. Every saved result is verified as an actual PNG/JPEG/WebP. Download failures retain their request-specific hidden page for receive-only retry; missing receipts never send a new prompt. Closing SceneForge completely stops its browser; X-to-tray retains it under the existing native host behavior.

Verification:
- `check_gemini_native_e2e.py`: real persistent headless Chromium, production service/ledger, unrelated browser closed during processing, >20k prompt, three exact attachment byte streams, image committed, receive after a simulated download failure without duplicate send, normal-login handoff without SDK import, saved cookie retained across a headless restart. Gemini/auth are fixtures.
- `check_native_login_ui.py`: real shell routes sign-in and finish to native endpoints rather than the extension.
- Existing extension full node/backend E2E passes; legacy browser sender is pinned unchanged.
- V6 16-role-combination and frame packing/contract checks pass.

Windows native sign-in and generation with a real Google account have NOT been run here. User should sign in once using the new button, then create one scene to verify real-site compatibility. There is no live-generation success claim. No watermark tool or unrelated model/Flow/UI changes are part of this update.
