# Gói code Lưu trữ / Thu gọn sau xuất

Snapshot mã hiện tại 25/10/2026, nền bản công khai 59cc255. Mục tiêu là mang đi phân tích, không thay đổi logic hoặc tự dọn dữ liệu khi đóng gói.

Đọc `review/BAN_DO_CODE.md` trước. Danh sách file trọng tâm và số dòng nằm trong `review/core-files.json`. `review/CAU_HOI_CAN_RA.md` nêu các giới hạn và điểm cần kiểm thêm; không coi mô tả trong docs là bằng chứng code đã làm đủ.

Code gốc giữ nguyên đường dẫn trong `scripts/` và `local_engine/`. Các module của app khác đi kèm là phụ thuộc dùng chung để shell/backend có thể dựng và khởi động nguyên vẹn; không phải toàn bộ đều là logic lưu trữ. Có bản web trong `dist/web-demo/`. Không kèm model, tài khoản, cookie, vault, venv, video người dùng, dữ liệu phòng hoặc EXE phần mềm khác.

## Chạy / kiểm

- Kiểm hash: `python review/verify_package.py`.
- Dựng: `npm ci --prefix scripts/watermark-builder`, rồi `python scripts/demo-web/build.py`.
- Backend local: `local_engine/start.bat` trên Windows, hoặc tạo venv Python 3.11/3.12, cài `local_engine/requirements.txt`, chạy `python -m local_engine`.
- Dùng thư mục dữ liệu thử riêng qua `SCENEFORGE_LOCAL_DATA`; không dùng kho đang có dữ liệu quan trọng để thử xóa. Các bài kiểm có temporary directory / profile riêng.
- Bài kiểm trọng tâm: `python -m local_engine.check_archive_release`, `python -m local_engine.check_export_commit`, `python scripts/app-shell/check_archive_local.py`, `python scripts/app-shell/check_photo_archive_lifecycle.py`.
- Chromium checks hiện dùng `/usr/bin/chromium` trên Linux; cần điều chỉnh trình duyệt nếu kiểm trên máy khác. Không chứng nhận Windows/online E2E.

`review/TEST_RESULTS.json` chỉ ghi kết quả đã chạy cho gói này. Manifest chứa SHA-256 từng file, không là đánh giá code an toàn hoàn chỉnh.
