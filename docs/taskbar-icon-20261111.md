# SceneForge .109 — Windows taskbar identity

Retains the existing lime SceneForge branding. Sets explicit process AppUserModelID SceneForge.Desktop before creating windows, explicitly enables ShowIcon/ShowInTaskbar, and falls back to the executable icon if the external ICO is absent. Native executable is rebuilt with the multi-resolution ICO. Existing updater refreshes only owned SceneForge shortcut icons. Stale pinned shortcuts may require unpin/re-pin; no global Windows cache deletion.

Cumulative update from .62 includes unchanged .108 application sources. No account/model/project files shipped or modified. Compiled with existing Microsoft Roslyn/Framework references; package bytes and ICO resources verified. Native Windows taskbar and updater execution have not been tested in this Linux environment. The screenshot alone does not establish the exact cause of the missing taskbar image.
