# SceneForge .157

Remove permanent will-change:transform from the workflow world container. Chromium can otherwise retain a composited raster at a prior scale and enlarge text with the layer. Keep the existing 2D transform, camera coordinates, node/wire geometry and zoom bounds; do not force GPU layers or scale image buffers. Photo canvas does not have this declaration and is unchanged. No new model, runtime dependency or persistent media cache.

Checked the actual Chromium workflow sample at 25%, 50%, 100% and 180%, transform and translation remain correct and computed will-change is auto. Captured and inspected visible nodes before/after. Text rendering remains browser/device-dependent; small source thumbnails are not made higher resolution. Windows WebView output has not been verified. Cumulative updater preserves all .156 files except workflow.html and verifies payload hashes/launcher bytes.
