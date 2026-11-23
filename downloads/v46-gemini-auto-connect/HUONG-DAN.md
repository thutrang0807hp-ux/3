# Gemini tự kết nối — app .162 + tiện ích 1.7.1

1. Đóng SceneForge, chạy cập nhật .162 rồi mở lại.
2. Giải nén ZIP mới đè vào thư mục tiện ích SceneForge cũ. Mở chrome://extensions hoặc edge://extensions rồi bấm Tải lại ⟳. Nếu chưa cài: bật Chế độ nhà phát triển → Tải tiện ích đã giải nén → chọn thư mục chứa manifest.json.
3. Mở Chrome/Edge đã đăng nhập Gemini và mở SceneForge. Tiện ích tự tìm app, mở/dùng tab Gemini và đưa kết nối vào danh sách tài khoản. Không tạo mã, không nhập mã và không cần bấm kết nối trong app. Nếu chưa đăng nhập Google, vào gemini.google.com/app đăng nhập một lần.

Node, prompt, ảnh tham khảo và bước duyệt giữ nguyên. Giữ trình duyệt mở lúc tạo. Có thể mất vài giây; khi Chrome đã tạm ngưng tiện ích nền, chu kỳ đánh thức tối đa khoảng 30 giây. App mặc định cổng8840. Nếu dùng cổng khác, mở địa chỉ app đó một lần trong Chrome/Edge để tiện ích tự nhận cổng, vẫn không cần mã.

Kết nối cũ và các lượt cũ được giữ. Kết nối tự động mới được chọn khi chuyển từ SDK hoặc mã Gemini cũ. Lượt đang chạy giữ nguyên kế hoạch, không tự gửi lại hay tạo thêm ảnh. Flow giữ cách kết nối riêng hiện có; mã trong mục Flow nâng cao chỉ dành cho Flow.

Kiểm thử xuyên suốt đã qua với backend, SQLite ledger, account pool và node thật; tiện ích và trang Gemini trong phép thử được mô phỏng. Môi trường kiểm thử chặn cài tiện ích unpacked bằng chính sách quản trị, nên chưa thử bước cài thật hoặc tài khoản Google thật của bạn.
