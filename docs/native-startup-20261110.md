# .101 — native Windows startup surface

Replace the pre-WebView label with a double-buffered WinForms card: SceneForge branding, lime indeterminate animation, actual backend/window/page phases and expanded failure details. Keep the surface above WebView until a successful navigation to the app URL. About:blank cannot dismiss it. Dispose the animation timer with the control. Use the existing icon at startup with an embedded icon fallback.

Rebuilt SceneForge.exe from the v46.50 published DesktopHost.cs source using Microsoft Roslyn 4.11, .NET Framework 4.8 references and the original WebView2 SDK 1.0.3537.50. No compiler/SDK/new runtime shipped in the update. Existing WebView DLLs retained. Existing singleton, process ownership, loopback navigation restrictions and close-save handshake preserved. This update targets loading visuals, not the remaining close-delay investigation.

Build command: `python3 veo-node-v46/scripts/windows-installer/build_native_host.py --dependencies /tmp/sf-native-build`. Build metadata records package/source/output SHA-256. Dependencies are official Microsoft runtime 8.0.22 (compiler host only), Microsoft.Net.Compilers.Toolset 4.11.0, Microsoft.NETFramework.ReferenceAssemblies.net48 1.0.3 and Microsoft.Web.WebView2 1.0.3537.50 packages. Extract runtime into dotnet/, others into compiler/, refs/, webview/.

Static validation confirms x64 GUI PE, .NET Framework references, exact published-source close/process methods, and all packaged hashes. Native Windows UI and installer have not been executed. The prior Chromium startup and storage tests cover the unchanged web payload.
