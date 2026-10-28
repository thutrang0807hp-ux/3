# SceneForge · mã nguồn đầy đủ · 28/10/2026

Đây là gói để chuyển sang máy/môi trường khác tiếp tục phát triển. Bao gồm frontend có thể chỉnh sửa, backend Python, tài nguyên giao diện/editor, tài liệu và thiết kế gốc, kiểm thử, cùng source làm bộ cài Windows. Gói không kèm môi trường Python/Node đã cài, model AI, dữ liệu dự án cá nhân, key/cookie hoặc tài khoản.

Đọc `BAT-DAU-TU-DAY.md` để chạy/build. Đọc `NGU-CANH-BAN-GIAO.md` trước khi sửa tính năng. `MANIFEST-SHA256.json` ghi kích thước và SHA-256 của từng file.

**Kho kịch bản v5 đang tạm hoãn theo yêu cầu người dùng.** ZIP thiết kế v5 được giữ trong `design/original-uploads/`; nó không phải bằng chứng tính năng v5 đã được triển khai.

- Frontend nguồn: `scripts/recovered`, `scripts/app-shell`, `scripts/workflow`, `scripts/photo-studio`, `scripts/shared` và các thư mục tính năng khác trong `scripts`.
- Trang đã dựng và tài nguyên chạy: `dist/web-demo`.
- Backend và requirements: `local_engine`.
- Source installer Windows: `scripts/windows-installer`.
- Tài liệu và test reports: `docs`, `docs/checks`.
- Thiết kế/tệp người dùng đã gửi: `design`, `design/original-uploads/INDEX.json`.
- Thông tin file EXE đã phát hành và link tải: `releases/windows-release.json`.

Bộ cài Windows v2 cho chọn nơi cài/dữ liệu/cache, kèm công cụ CPU/FFmpeg/Whisper và chuẩn bị SDK Gemini/Flow mặc định. Có mục gỡ trong Windows Apps và shortcut riêng, mặc định giữ dữ liệu. Giọng VieNeu là tùy chọn tải thêm. Báo cáo kiểm Windows hiện hành nằm trong `docs/checks/windows-check-report.json`; không suy từ kiểm SDK/fixture thành đã tạo media bằng tài khoản online.

Bộ cài Windows v2 đã qua kiểm chọn ổ/thư mục thật, chuẩn bị Gemini/Flow bằng nguồn ghim, Whisper nhận dạng tiếng nói thật, xuất MP4 H264/AAC, mở lại/cài lại và gỡ giữ dự án. Xem báo cáo hiện hành; kiểm SDK dùng fixture và không xác nhận tạo media bằng tài khoản online. VieNeu là tùy chọn tải thêm.

## Cập nhật cửa sổ riêng · 29/10/2026

Bản đang phát hành là bộ cài nền v2 cộng bản vá nhỏ `SceneForge-Update-20261029.exe` (khoảng 3,9 MB). Bản vá đổi launcher sang cửa sổ WinForms/WebView2, ẩn backend và worker, sửa nút Phân tích gọi đủ pipeline CPU, giữ model/dữ liệu và lưu trước khi đóng app. Source của cửa sổ/bản vá ở `scripts/windows-installer/DesktopHost.cs`, `build_desktop.py`, `build_patch.py`, `apply_update.ps1`. Xem `docs/windows-desktop-patch.md` và `docs/checks/desktop-patch-release.json` để lấy link/hash và bài kiểm Windows. `build.py` cũ dựng bộ cài nền v2; cửa sổ riêng được áp qua bản vá, không suy rằng bộ cài nền đã đổi launcher.

Đã thử trong cửa sổ thật bằng cách bấm nút Phân tích: video mới, dự án chỉ có cảnh cắt, kết quả CPU cũ thiếu lời; kiểm Whisper/OCR/chuyển động/mờ-rung, không gửi trùng khi bấm lại, xuất MP4, mở tab ảnh, đóng app dừng backend, gỡ giữ dữ liệu. Chưa kiểm tạo ảnh/video online bằng tài khoản thật.


## Bản vá 2026.10.29.2
Sửa lấy khung cuối khi audio dài hơn hình; cập nhật kết quả chia cảnh cũ; trạng thái khung gốc/Veo trung thực; mở Google bằng Chrome/Edge cài trên máy. Xem docs/scene-login-patch.md và docs/checks/scene-source-check.json. Đăng nhập Google tài khoản thật vẫn chưa xác minh.
