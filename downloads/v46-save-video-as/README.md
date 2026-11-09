# SceneForge v46.86 — Save completed node video as a user-selected file

Requires .85 or newer. Payload: workflow.html, photos.html, timeline_export.py and new export_save_as.py. Preserve render/speed/caption/logo behavior, voice/Flow runtimes, models and source assets.

## Behavior

- Windows capability detection enables a native WinForms SaveFileDialog via installed Windows PowerShell, STA, hidden console. After final rendering, choose an MP4 name/folder. A cancel leaves the completed final available for another save, without FFmpeg rerendering.
- Lưu video thành… reuses the completed MP4. Selected names become the next suggested name. Status reports the actual Windows destination.
- Browser File System Access picker is invoked directly on a fresh save-button click, before await, so rendering cannot consume its required activation. Writable failure aborts the stream and preserves the completed blob. A canceled picker never falls through to an automatic download.
- Unsupported/browser-restricted environments get a separate explicit browser-download fallback. Native errors also offer a browser picker when supported. No silent default-directory download.
- Native save copies the known completed job file through a temporary destination, flushes/syncs, checks that the previous destination did not change and atomically replaces it. Original destination survives failed copies. Existing-file confirmation is supplied by the Windows dialog.
- New save route accepts only a suggested filename; it never accepts a client-supplied destination or source path. Local header/origin checks, bounded body, one dialog at a time; ready job resolution reuses managed storage/file behavior.
- Completed node video remains cached in the current viewer session. Closing the viewer or changing content settings ends/retires that cache as before.

## Verification

Real Chromium/FFmpeg MP4 with native selection mocked at the platform boundary: auto native cancellation preserves destination and final; manual native save writes exact bytes to a Unicode filename and replaces the mock-approved old file; failed save retains cache; browser picker has current click activation, supports cancel / failed write / abort / retry, and writes an identical SHA256; no render reruns or automatic downloads. Explicit browser fallback verified. Route rejects untrusted origin, missing local header, destination injection and oversized input. Injected copy failure preserves previous file and removes the partial temporary file.

Speed/review actual MP4, FFmpeg syntax compatibility, live-caption and shared-module/scale regressions passed. Embedded artifact sources/download SHA verified. Actual Windows dialog UI and Windows updater were not run in this Linux environment.

SHA256: 149ba877f17485e02b114adad1b5eb682b113a418d534dfacdce51972c564011
