# Bản đồ luồng lưu trữ

| Bước | File cần đọc | Vai trò |
|---|---|---|
| Xuất xong → lưu Blob → báo Đã xuất | `scripts/native-preview/room-shell.js`, `scripts/app-shell/app.js` | `queueRoomExport`, `saveRoomExport`, ACK về editor; retry lưu không dựng lại |
| Chép bền từ IndexedDB xuống máy | `scripts/app-shell/library-runtime.js` | Theo dõi transaction, serialize Blob/data URL thành hash, checkpoint; localStorage dirty flag, lease/recovery |
| SQLite + file theo hash | `local_engine/library.py` | commit/revision, asset_ref, backup, pin, verify, relocate, cleanup/release_compacted |
| API kho | `local_engine/library_api.py` | `/local-api/library/*`; upload/restore/cleanup/release-compacted/bundle |
| Chuyển Lưu trữ | `scripts/app-shell/home-archive.js` | danh sách, restore, trạng thái, thống kê. Chuyển Lưu trữ chưa tự xóa tư liệu |
| Thu gọn chỉ giữ thành phẩm | `scripts/app-shell/archive-lifecycle.js` | archiveCompactPlan, archivePerformCompact; hash video, text-only snapshot, journal prepared/committed, giữ export/SRT và file chia sẻ |
| Lịch / ghim / dùng lại kịch bản | cùng file archive-lifecycle | archiveRunDue, archiveLifecycleDialog, archiveSaveScript; app mở mới xét lịch; không giữ timeline đầy đủ sau final-only |
| Sao lưu / chuyển máy / Thùng rác | `scripts/app-shell/library-panel.js`, `library-portable.js`, `local_engine/library.py` | UI và snapshot/bundle; refs trong backup có thể giữ media khỏi bị xóa |
| File tạm FFmpeg và job | `local_engine/timeline_export.py`, `exports.py`, `local_jobs.py` | nguồn export tạm, output tạm, cleanup/cancel/restart. Khác với Blob thành phẩm đã commit vào kho |
| Bản sao ra thư mục ngoài | `scripts/app-shell/app.js` | mirrorRoom, writeImmutableFile; thu gọn không xóa bản sao ngoài app |
| Tệp gen ở backend | `local_engine/flow_provider.py`, `muse_provider.py`, `gemini_chat.py`, `request_ledger.py` | các thư mục results/journal riêng; chưa dọn thống nhất với final-only |
| Bootstrap/quyền | `local_engine/server.py`, `runtime_safety.py`, `schema.py` | đăng ký route, dữ liệu local, same-origin/session, migration |

API đúng path/method xem `review/storage-routes.json`, trích từ inventory của app cùng bản dựng. Mã frontend giữ nguyên, gồm các wrapper/hàm được ghi đè ở cuối module; cần theo đúng thứ tự ghép trong `scripts/demo-web/build.py` khi phân tích.
