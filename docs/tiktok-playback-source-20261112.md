# .124 TikTok playback-source selection

Repository search found `watermark/engine.js`, vendored GargantuaX/gemini-watermark-remover for the Gemini logo pattern, not a general TikTok remover. It is intentionally not reused on TikTok.

Upstream code inspected: https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/tiktok.py (read 2026-11-12). `_extract_web_formats` supplies `play` and explicitly labels `download` with `format_note: watermarked`; API parsing supplies `play_addr`/variants and marks `download_addr` when appropriate. No upstream implementation code is vendored; this update interoperates with those format fields via the already installed yt-dlp dependency.

The old selector maximized height/bitrate and could choose a known watermarked download over a playback source. .124 classifies extractor evidence as playback, declared_unwatermarked, watermarked or unknown, and chooses a usable source tier before applying the existing complete/split/incomplete codec selection. Audio-only formats remain available for merging. Explicitly unplayable bytevc2 sources are excluded. Only TikTok hosts/extractors use this preference; other platforms keep existing ranking. The size filter is orientation-aware (1920×1080 or 1080×1920) and actual extractor downloads are checked after probing, rather than rejecting portrait 720p/1080p just because their height exceeds 1080.

Metadata includes source kind, `watermark_pixels_checked: false`, a source-policy version and a clear notice for marked/unknown fallback. The UI persists source evidence with the room and shows that notice after import. TikTok URL-cache reuse requires the new policy, so a previously imported legacy result cannot silently prevent rechecking the source. A byte-identical result can reuse an existing room, updating its evidence; a different result follows normal new-room intake.

No inpainting, cropping, pixel watermark detection or removal is performed. No guarantee is made that creators' baked-in logos disappear, or that every TikTok URL exposes a suitable alternate source. Unknown/marked fallback never becomes a false 'logo removed' success. Source diagnostics include derived classifications, not signed CDN URLs/cookies.

Validation:
- `python veo-node-v46/local_engine/check_tiktok_watermark_source.py`: real MP4 with audio and HTTP fixtures; playback beats higher-resolution marked download; downloaded bytes preserved; incomplete and split playback priority; unusable split fallback; explicit API flags; unknown notice; non-TikTok ranking unchanged.
- Existing `check_video_import_metadata.py` and `check_video_import_merge.py` pass metadata, probing, merge, byte-cap and cleanup regressions.
- `python scripts/analysis/check_tiktok_source_notice_ui.py`: actual intake module in Chromium; legacy same-link room is not blindly reused; marked-source notice and policy are persisted/displayed; no generation or third-party service calls.
- Embedded EXE manifest/source bytes/hashes verified. Cumulative .62+ payload retains previous fixes. Live TikTok and Windows installer not tested.
