# SceneForge .149

Retain an open frame inspector when image creation starts rather than unconditionally closing the modal. Disable submission controls immediately, preserve local preparation progress, and redraw the resulting image after completion. Other bulk dialogs retain their existing close behavior. A late error cannot reopen an inspector the user has closed.

Generic receipt polling now labels image failures as image creation rather than Gemini prompt writing, includes the request ID, and preserves the no-auto-resubmit policy for unknown results. This release does not claim to fix the provider-side cause of unknown.

Validation: actual Create frame click with delayed image response keeps modal visible while pending and after MP4-backed output import, disables submission and sends one image request; retained writer history and pending-image protections; optional writer/close-reopen regression; unknown image error label and request ID; inline JavaScript syntax; cumulative payload hash verification. No live Gemini or Windows installer execution.
