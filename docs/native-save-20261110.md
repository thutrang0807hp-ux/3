# .99 — faster hashing and binary equality during saves

Use WebCrypto SHA-256 for blobs up to 64 MiB, with the previous streaming worker above that bound. Avoid the old SHA/CRC JavaScript worker when only SHA-256 is needed for the library. IndexedDB binary key comparison replaces JavaScript byte loops; compare in 1 MiB chunks, preserving exact byte checks. All library digest formats remain unchanged.

Close progress now refreshes every 2.5 seconds with preparation/media, metadata digest, SQLite/backups/exports, or verification phase. Actual save failures retain the previous safety prompt. Native Windows host is unchanged; no claim that all close delays are fixed.

Validation: 16 MiB native digest matched both Python hashlib and the previous worker (78.7 ms versus 685.7 ms in Linux Chromium fixture). Equality test rejects a changed final byte. IndexedDB/SQLite close regression covers updates, deletion, unchanged media exclusion and real save failure retention. Windows close latency and installer not tested.
