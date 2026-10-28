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


## Bản vá 2026.10.29.3
Lỗi đọc khung proxy: thay bộ đọc nhảy khung OpenCV bằng FFmpeg tuần tự, bộ nhớ giới hạn; nút Phân tích tiếp tục lượt CPU lỗi cũ cùng mã. Xem docs/proxy-reader-patch.md. Các sửa đăng nhập từ bản .2 vẫn được giữ; tài khoản Google thật chưa xác minh.


## Bản vá 2026.10.29.4
Kết nối Gemini Chat/Flow mặc định bằng tiện ích trên trình duyệt đang đăng nhập. Nạp thư mục scripts/browser-extension một lần; tạo mã trong app, nhập vào tiện ích để chuyển phiên. Không dùng proxy hoặc cửa sổ đăng nhập tự động. Xem docs/browser-session-bridge.md; tài khoản thật/tạo nội dung vẫn cần thử thật.


## Cập nhật 29/10/2026 — ảnh khung và chat theo dự án (v5)

Bản vá 2026.10.29.5 dùng cùng quy trình viết prompt theo tham chiếu cho nút tạo/tạo lại và Chạy tự động. Ảnh gốc chỉ cung cấp bố cục/tư thế; mã ảnh người, mặt chuẩn, trang phục, sản phẩm gắn đúng thứ tự. Giữ phần sửa tay. Tab ảnh tĩnh áp cùng chỉ dẫn vai trò cho ảnh từng cảnh.

Chat tạo ảnh được giữ theo dự án và tài khoản, lưu mã chat nhỏ trong vault mã hóa và xếp hàng từng lượt. Lần đầu dùng v5 tạo chat mới; các lần sau tiếp tục chat đó, kể cả sau khi mở lại app. Không thể tự nhận diện các chat rời từ phiên bản cũ. Phân tích và viết JSON dùng lượt riêng, không trộn vào chat tạo ảnh. Lượt ảnh chưa rõ kết quả chặn gửi tiếp; không tự tạo chat khác hoặc gửi lại.

Xem docs/frame-reference-chat-patch.md và docs/checks/frame-*. Đã kiểm bằng dịch vụ giả và SDK thật với transport giả; không coi đó là kiểm chứng Gemini thật thay đúng mặt/sản phẩm. Cần xem lại cảnh 2 thật sau cập nhật. Dùng bản vá nhỏ, không tải lại model/runtime. Kho kịch bản v5 vẫn tạm hoãn.


## Cập nhật v6 — thao tác node Ảnh khung và tải ảnh gốc

Bản vá 2026.10.29.6: Tạo/Tạo lại từ node là lệnh gửi, không mở hai bảng xác nhận trung gian. Đầu node có nút Tạo lại N khung, tiến độ theo cảnh và Dừng gửi thêm. Vẫn giữ ảnh cũ và không gửi trùng lượt đang chạy/chưa rõ. Các nút của tiện ích AI trực tiếp riêng và tạo video không đổi.

Đã tìm thấy worker dùng full_size=False, khiến SDK tải preview 1024. Nay dùng full_size=True để lấy bản gốc/lớn nhất nguồn cung cấp, giữ nguyên bytes và hiện kích thước thực nhận. Không bảo đảm mọi model/tài khoản trả đúng 1080×1920 chỉ vì prompt ghi vậy; không tự upscale. Ảnh cũ không được tự tải lại hay ghi đè. Xem docs/frame-node-run-patch.md và docs/checks/frame-v6-*.
