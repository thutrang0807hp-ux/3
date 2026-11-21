# .132 Gemini native sign-in before session capture

Evidence: user reports ordinary Chrome signs in successfully while the Settings-launched Gemini window reaches Google's unsupported/insecure-browser rejection. The error does not establish a password problem or a specific Google policy change. Git history confirms the Google-login/profile/Gemini modules are unchanged through .125–.131; their last changes were profile persistence, optional device parameters and cache limits (.90–.96). This patch is not claimed to prove why a previously working Google sign-in stopped.

The prior installed-browser path still enables remote debugging at launch. The profile manager may attach before credentials to apply saved cookies/device parameters. .132 adds a Gemini-only manual-sign-in mode: installed Chrome/Edge with an isolated persistent app profile, ordinary launch flags, no CDP/Playwright connection, no device script, and no saved-cookie injection while credentials are entered. It uses the browser's existing on-disk profile normally.

The user closes that window after reaching Gemini, allowing the browser to flush cookies. Only explicit Save session starts the same browser/profile at about:blank with loopback debugging, reads cookies and passes them to the existing Gemini session verifier/storage. No Google navigation occurs in the capture step. A lock serializes capture/close; lease release and persistent-profile retention are preserved. Cancel closes only the owned process/window; Windows WM_CLOSE callback declares pointer-sized argument types. An already listening old DevTools profile is rejected before native launch, avoiding forwarding the new window into an older controlled session.

UI instructions in the primary Settings account dialog explicitly describe sign in → close that browser window → save. Save before closure returns an actionable 409 and leaves the pending login intact for retry. The studio legacy bridge UI is unchanged because it does not contain this native-login dialog. Other provider modes and saved device configuration are unchanged.

Validation:
- `python scripts/analysis/check_google_manual_login.py`: isolated process/Playwright mocks verify no automation args on manual launch, no early read, deferred blank capture, original profile/browser, cookie injection bypass, no fingerprint application during credentials, idempotent cleanup/lease, persistent files retained and active old controlled profile rejection.
- `python scripts/analysis/check_google_manual_login_ui.py`: actual account dialog function in Chromium with mocked login/confirm endpoints; correct close/save guidance, no auto-confirm, early-save failure keeps same pending ID, explicit confirmation succeeds.
- JS parsing and embedded payload/source hashes verified. Cumulative .62+ release preserves latest .131 application sources and data.

Limitations: no real Google sign-in, SDK verification or Windows installer/WM_CLOSE execution was tested. Google acceptance remains a user-machine test. No anti-detection flags, browser-identity spoofing, personal-profile copying or collection of real cookies/passwords is introduced.
