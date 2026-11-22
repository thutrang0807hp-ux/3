# SceneForge .156

Restore extension pairing as the Gemini account connection default. Both the main connect function and openAccountWebLogin Gemini branch go to connectBrowserSession with separate:true, covering connect, account profile/reconnect and Google connection controls; Flow and other providers retain their prior handlers. Label the main action accordingly. Use existing 3-minute one-time loopback bridge, Origin validation, session verification and encrypted storage without changing its protocol. No changes to the image download engine.

Publish a standalone ZIP containing byte-identical scripts/browser-extension files from the released v46 source. Preserve extension 1.6.9 public key/ID for bridge Origin compatibility and its existing Flow features. No personal credentials or session data included. Older app users can already open the same pairing path from advanced login controls.

Chromium test checks main and profile/reconnect entry points, generated code display, Gemini-only pairing default and no native Gemini login call. ZIP bytes verified against baseline archive. Cumulative updater changes only index.html relative to .155; embedded files and launcher bytes verified by builder. No live Google sign-in/image transfer or native Windows updater test; restoring cookie import is not a proven remedy for the user's HTTP403.
