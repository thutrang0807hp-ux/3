# SceneForge v46.87 — Application branding icon

Requires .86. New lime/graphite SceneForge S/clapper/play icon generated for this task. PNG source retained; ICO includes 16,20,24,32,40,48,64,128,256px RGBA entries.

The native host binary is preserved. A Windows-only optional backend worker applies WM_SETICON big/small icons to the matching installed desktop window after verifying desktop-state HWND/PID and QueryFullProcessImageName against this installation's SceneForge.exe. DPI metrics select icon sizes. Branding failures cannot prevent startup. Browser and Linux startup skip the worker. No package installation/compiler or model changes are required.

The normal verified updater additionally updates IconLocation only for SceneForge shortcuts whose targets belong to this installation (including its outer launcher). Shortcut permission failures are cosmetic and nonfatal. Old pinned icons may require unpin/re-pin because of Windows caching. The executable file's Explorer resource icon is unchanged; live application window/taskbar icons and shortcut icons are the targeted surfaces.

Favicon links are added to index/studio/workflow/photos. Payload is these four HTML files, ICO, server.py and desktop_icon.py. Existing server source is preserved with only the optional branding registration appended.

Validation: real nine-size ICO decoding, transparent exterior and visible lime mark; favicon paths; ownership tests reject stale PID, invalid HWND and other installation. Linux startup unchanged. Payload sources/checksum verified. Native Windows UI and shortcut updates have not been exercised in this Linux environment.

SHA256: 858f7f4a591bbae99e210bce1e182f2023bc859f43ed6e429827b37d39bc3622
