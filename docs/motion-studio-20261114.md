# Motion Studio v46.129

Separate room variant `motion`, reusing reference analysis and merge/export. Does not replace the sample or photo branches.

Implemented: role-specific references with explicit approval; optional generated reference angles via selected Gemini Chat account; local source upload and exact scene cuts; editable bilingual instructions; downloadable ZIP containing actual clip, images, English prompt and reference map; selected Flow profile opening; validated result import, append-only versions and explicit preview approval before merge.

Flow uploaded-video edit submission is manual. Legacy image-generation submission is blocked in Motion rooms. No API billing fallback, no local diffusion/depth weights, no promise of 4K or reference fidelity. Source audio preservation is requested in the edit instruction, not independently restored by this feature.

Temporary service: 128 MB source/output limits, 384 MB managed total, 1-hour expiry checked on subsequent activity, room-scoped clearing. Central storage statistics do not yet include this temp folder. Original assets and imported result assets remain in the existing project store.

Validation: 2 backend integration tests with real MP4/audio and ZIP bytes; browser fixture tests for separate-room persistence, exact durations, role approval, writer receipts, generated-angle approval, result import/version preservation and readiness gating; existing sample prompt-layer regression passed. Embedded installer payload and SHA-256 verified. No live Flow/Gemini generation or Windows installer execution tested.
