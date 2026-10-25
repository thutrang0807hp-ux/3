# ĐỌC TRƯỚC — gói kiểm tra code Video mẫu

Mục tiêu: kiểm toàn bộ đường chọn video ở trang chủ → phòng Video mẫu → CPU/Whisper/OCR → Gemini hiểu cảnh và viết → ảnh khung được duyệt → clip Flow/Muse → giọng/phụ đề/nhạc → Dựng → MP4 → trạng thái phòng.

Đây là mã nguồn + bản web dựng sẵn để rà liên kết, không phải chứng nhận đã chạy một video thành phẩm bằng tài khoản online thật. Snapshot sau đợt lưu trữ v2 ngày 26/10/2026; manifest ghi hash chính xác từng file trong gói.

## Nên đọc theo thứ tự

1. `review/DE_BAI_DANH_GIA.md`: phạm vi cần rà, câu hỏi cụ thể và các nghi vấn từ lần đọc code gần nhất.
2. `review/LIEN_KET_TUNG_BUOC.md`: bước, file, endpoint, động cơ, tài khoản và đầu ra.
3. `review/KET_QUA_VA_CHO_CHUA_CHAC.md`: phép thử thật/fixture và các khoảng trống đang biết.
4. `review/THU_BANG_TAI_KHOAN_THAT.md`: cách thử một phòng với tài khoản của bạn, ghi chi phí và kết quả; không tự gửi yêu cầu.
5. `review/routes.json`: endpoint lấy từ chính FastAPI app trong môi trường dữ liệu rỗng.
6. `review/manifest.json`: SHA-256 từng file nguồn, giao diện và báo cáo.

## Chạy và dựng lại

- Bản chạy đã có trong `dist/web-demo/`. Chạy `local_engine/start.bat` trên Windows để mở app qua backend local; không mở HTML bằng file:// để thử đăng nhập/AI.
- Gói không kèm Python venv, cookie, tài khoản, vault, dữ liệu phòng người dùng hoặc model. Giữ model đã cài trong thư mục dữ liệu SceneForge. Có bộ model trong gói đầy đủ trước đó thì `install-and-check-local.bat` sẽ nhập và kiểm; gói review này không tự mang trọng số.
- Model local/thư viện: `local_engine/install-and-check-local.bat`. Thiếu model thì báo thiếu, không báo sẵn sàng giả. SDK và thư viện vẫn cần mạng để cài lần đầu.
- Dựng lại giao diện: Node/npm và Python 3.11/3.12; chạy `REBUILD.bat`, hoặc `npm ci --prefix scripts/watermark-builder` rồi `python scripts/demo-web/build.py`. Build không gọi AI.
- Kiểm gói: `python review/verify_package.py`. Build làm thay đổi file đã đóng gói thì manifest phải được tạo lại cho snapshot mới.
- Các bài Chromium/CPU trong source có fixture và một số đường dẫn Linux. Kết quả chạy kèm là trên Linux phát triển; không coi chúng là đã kiểm trên Windows. Cài gói nhỏ không đồng nghĩa đã cài trên PC người nhận.

## Phạm vi mã nguồn

`scripts/workflow/` là canvas Video mẫu. `scripts/app-shell/` giữ chọn file/phòng, lưu trữ và Cài đặt tài khoản; `scripts/native-preview/` + `scripts/demo-lite/` là Dựng/xuất. `local_engine/` là backend và adapter. Các module dùng chung, kể cả photo-studio, vẫn đi kèm để shell dựng và mở được nguyên vẹn. Đây không phải app ảnh tĩnh riêng; phần chính cần rà đã đánh dấu trong bảng liên kết.

Không kèm EXE/bridge của phần mềm khác. Các SDK Flow/Muse/Gemini/VieNeu được cài riêng từ revision trong `docs/engine-audit`. Source/notice/license của phần watermark, codec và font được giữ cùng gói.
