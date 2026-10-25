# Bản đồ lưu trữ v2

| Vùng | File |
|---|---|
| Ba thao tác, chọn nhiều, lấy lại/thử lại, setting dung lượng | scripts/app-shell/storage-actions.js |
| Quyền xóa ở backend, plan/CAS, release/deleted, quarantine/revive/cancel/expedite | local_engine/storage_lifecycle.py |
| Registry job, nhập đúng job/room/hash, alias, dự phòng dung lượng | local_engine/storage_jobs.py |
| Hash store/SQLite/backup/ZIP/restore và chuyển thư viện | local_engine/library.py |
| Các API kho mới | local_engine/library_api.py |
| Khóa một bộ chạy trên máy | local_engine/library_lock.py, instance.py |
| Claim chống gửi trùng và nối catalogue | local_engine/request_ledger.py |
| Browser checkpoint, worker hash, binary assets, cache | scripts/app-shell/library-runtime.js, library-portable.js |
| Đường browser cũ và lịch chốt; local chuyển sang backend | scripts/app-shell/archive-lifecycle.js |
| MP4/WAV/results vào catalogue | local_engine/timeline_export.py, exports.py, server.py; provider adapters |

Đọc docs/storage-lifecycle-v2.md trước, sau đó TEST_RESULTS.json. Những phần phụ thuộc app đi kèm để dựng/chạy; gói không kèm model, tài khoản hoặc dữ liệu phòng thật.
