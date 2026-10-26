# SceneForge — code tập trung luồng Từ ảnh & ý tưởng

Mục đích: mang đi đánh giá code và cách nối từng bước, không phải gói cài app.
Snapshot ứng dụng đã công bố: `b3fe48e` (26/10/2026). Đóng gói không sửa logic.

Đọc theo thứ tự:

1. `review/LUONG_VA_BAN_DO.md`: luồng và file/hàm nối từng bước.
2. `review/DE_BAI_DANH_GIA.md`: yêu cầu đánh giá, tình huống cần kiểm.
3. `docs/photo-clip-flow.md`: cách dùng và giới hạn đã công bố.
4. `scripts/photo-studio/` theo thứ tự trong `scripts/demo-web/build.py`.
5. Backend, shell, editor theo bảng liên kết; kiểm chứng ở các báo cáo trong `review/`.

Các file JS/Python/CSS được giữ nguyên, không rút gọn/chuyển thành ví dụ.
Các module dùng chung có nhánh ngoài phạm vi: chỉ rà đường Từ ảnh & ý tưởng.
Không đánh đồng code tồn tại hoặc transport fixture PASS với generation online đã chạy.

Gói không chứa HTML đã build, ảnh/video/giọng mẫu, font, trọng số model, SDK đã cài,
venv, cookie, API key, vault hay dữ liệu dự án người dùng. Nó KHÔNG dựng/chạy app
độc lập. `template.html` là mã nguồn UI. Những tài nguyên/UI ngoài phạm vi bị bỏ
chủ đích; đường dẫn không có ở gói này không có nghĩa app đầy đủ bị thiếu file.
Các bài test được giữ để đọc; nhiều bài cần media/Chromium/backend của gói đầy đủ.

Kiểm ZIP sau giải nén: `python review/verify_package.py` (chỉ cần Python stdlib).
`manifest.json` ghi SHA-256 từng file; `review/core-files.json` chỉ ra file trọng tâm.
Báo cáo kiểm chức năng/build là lần chạy trên app đầy đủ trước khi đóng gói này,
không phải chứng nhận gói gọn chạy được. Chưa kiểm Windows/tài khoản thật.
Muse hiện là muse.ai, chưa phải Meta AI.
