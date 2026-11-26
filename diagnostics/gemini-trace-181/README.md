# .181 diagnostic release: preserve the actual timeout and current stage

The user reports no visible prompt/reference submission, but the .180 screenshot only says "Hết thời gian chờ Gemini". The upstream main() deliberately replaced all Playwright TimeoutError messages with that one sentence. Consequently it was impossible to distinguish CDP connection/navigation from later image waits using the screenshot. This release is diagnostic, not a claim of a live fix.

No upload/send/receive algorithm is replaced. Instrumentation around existing calls records only stage, timestamp, failure boolean and error class. It never records prompt text, references, cookie values, email, HTML, image URLs or signed URL parameters. Files are private per-request JSON under the existing native-turns directory; successful jobs retire them, failed jobs retain the last stage. The existing status endpoint/UI displays the current stage and error location. Full first-line errors are preserved with URL strings redacted, instead of replacing every timeout with a generic sentence.

Stages: preparing the account profile; connecting CDP; opening Gemini; checking session; finding the editor; selecting image mode; attaching references; filling/clicking Send; confirming a new turn; waiting for image; downloading image; file received.

The native wrapper supplies a trace path only for image/text jobs. The original Python workspace stays byte-for-byte. Existing scene editor/progress, V6, dimensions, shared instructions, references and logo tools are unchanged.

Tests retain the existing actual Node/CDP fixture flow plus a navigation failure: it produces native_trace.stage=open_gemini and an [open_gemini] error, with no recorded send. The receiver/download functions remain byte-for-byte; privacy fields are allowlisted by the backend. Google/auth and Windows are not tested live here.

Use a NEW turn after installing to obtain a new trace. A stored error from an old request cannot gain missing diagnostics retroactively. This build is intended to obtain the real failure location on the user's machine before another functional change.
