# .123 incomplete extractor metadata and source diagnostics

The user's TikTok screenshot shows the old generic no-candidate error. It does not identify the actual extractor formats or prove login is required. Source review found the selector excludes `None` codecs and only defaults protocol when the field is absent; a missing audio codec or explicit null protocol therefore rejects a potentially complete HTTP file.

After known muxed and known split streams, the importer now tries HTTP(S) formats with incomplete codec metadata, excluding explicit audio/video-only declarations, DRM, fragments and manifest paths. Protocol may be inferred from the URL when missing/null. Actual MP4/WebM signature and FFprobe checks still decide whether downloaded content is video; incomplete-metadata media exceeding 1080p is rejected after probing. Complete formats and direct file imports retain their original path. Existing public-address checks, header filtering, limits and cleanup remain.

Jobs retain a bounded summary of up to 30 extractor formats (codec/protocol/ext/height and boolean flags). Raw media URLs and HTTP headers are excluded. When a failed import has that summary, both shipped intake pages expose a local JSON report download with job ID, state, error and the summary. This supports evidence-based follow-up if the TikTok link is segmented, blocked or otherwise unsupported.

Validation:
- `python veo-node-v46/local_engine/check_video_import_metadata.py`: real complete MP4 with audio and mocked HTTP, missing video/audio/both codecs/protocol, positive ffprobe; explicit audio-only/DRM/segmented rejection; HTML file rejection and cleanup; no URL/header in summary.
- `python veo-node-v46/local_engine/check_video_import_merge.py`: existing split stream merge/direct import/size/cancellation regressions passed.
- `python scripts/analysis/check_video_source_report_ui.py`: actual embedded intake module in Chromium with a failed-job fixture; error visible, report button enabled and JSON download safe, no generation calls.
- Builder verifies embedded manifest, source bytes/hashes and unchanged generic launcher. Cumulative .62+ payload includes .119–.122.

The actual short TikTok link in the screenshot and the Windows installer were not live-tested. This release does not claim to support HLS/DASH playlists or solve every TikTok download failure.
