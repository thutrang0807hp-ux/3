# Motion Studio · planned separate branch

Name agreed with user: **Motion Studio**. Status: design, not enabled or released as a working generator.

Keep sample-video recreation and photo-to-video intact. Reuse scene analysis, shared Settings accounts, durable receipts, version import, merge/export and media storage rather than duplicating those implementations.

Proposed sequence: source video → scene analysis → role-specific references → approved character/wardrobe/product reference set → source-clip editing → merge/export. Reference-set views may include front, side or back only where supplied or explicitly generated/reviewed; generated unseen sides are estimates, not verified 360-degree product truth. Keep product images separate from character/wardrobe images and preserve their attachment roles.

Each scene requires a cut source clip and selected reference image bytes, a bilingual edit instruction, a clear replace/retain scope, and ownership tied to room, scene and request. Stage clips locally, verify actual uploaded attachment roles before submit, persist intent before sending and never resend an ambiguous job automatically. No Wan or Depth model is required for this design.

Blocker to enabling generation: the existing SceneForge GFlow adapter takes a single start image, and the inspected GFlow CLI does not expose the uploaded-video editing path used by the user's Flow chat. The official Omni API examples document video editing, but API credentials/billing cannot be substituted silently for browser-session Flow credits. Confirm and implement the actual browser Flow editing transport before exposing a working Generate button.

Existing app does not have access to the user's live Flow session in this workspace. No claim about TobyFlow internals or exact motion fidelity is made.
