# SceneForge v46.186 — one-click bulk frame review

Add Duyệt nhanh N cảnh có ảnh below the frame grid. Snapshot each scene's selected generated-frame ID, skip already-approved/no-result scenes, and invoke the existing v46.185 original-file manual approval sequentially. Guard the batch against changing rooms or selected frames. Display actual successful approval count and individual failures; one missing file does not block other scenes. A retry targets only scenes still unapproved. Preserve frame versions, receipts and all transport behavior. No confirm dialog, automatic media generation, OCR or image receive is triggered.

UI keeps the batch busy guard through individual approval calls, reports progress and partial failures, and avoids replacing an active generation's progress. Main input changes reset the old batch summary.

Validation: actual production node button in Chromium with selected older version, valid scenes, missing original file, source-only scene and an already-approved scene. Exact approved set, retained versions, zero media provider requests, partial-failure message, retry remaining only and disabled button after completion. Single-scene approval regression and embedded-source contract also pass. Packaged workflow/runtime and EXE SHA-256 checked. Native Windows installer execution and live provider generation are not exercised for this UI-only action.
