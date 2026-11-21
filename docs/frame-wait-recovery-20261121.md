# SceneForge .146

Allow read-only scene inspector navigation during pending generation; retain per-scene action/provider errors across inspector closure. POST text wait is bounded at 90 seconds, POST media at 180 seconds, status requests at 15 seconds. Active receipt polling stops locally after two minutes; this is not remote cancellation. Ambiguous requests retain receipts and are not automatically resubmitted. Shared product references attach by default unless explicitly disabled; selected per-scene subsets remain honored.

Validation: inspector close/reopen while request pending; accelerated transport timeout with persistent scene error and no duplicate POST; source/product attachment and one writer/one image with real MP4; native fallback and version retention; node stop/restart regression; all inline JavaScript syntax; cumulative payload byte and hash verification. No live Gemini account or Windows installer execution. Remote provider latency is not claimed fixed.
