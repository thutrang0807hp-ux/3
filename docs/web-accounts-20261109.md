# SceneForge .90 — Đăng nhập web trong các tab tài khoản

Đóng SceneForge rồi cập nhật trên .89. Vào Cài đặt → Tài khoản.

- Sáu tab đều dùng nút chính Đăng nhập trên web. Flow giữ nguyên cơ chế tự nhận phiên đã có.
- Gemini Chat dùng đường mở Chrome/Edge và xác minh phiên qua SDK đã có. Khi chưa đăng nhập xong hoặc kiểm tra lỗi, giữ cửa sổ để thử Lưu phiên lại.
- Muse dùng đường mở web của companion, lưu cookie đúng muse.ai vào vault rồi kiểm tra bằng Muse adapter. Không cần nhập email/OTP vào app; OTP của dịch vụ vẫn có thể xuất hiện trên web. Kiểm tra SDK thất bại vẫn giữ phiên dưới trạng thái chưa xác minh.
- Grok, ChatGPT, Meta dùng bộ đăng nhập web và kiểm tra ô chat đã có; thống nhất màn mở/lưu/quay lại. Mỗi dịch vụ giữ phiên riêng.
- Tiện ích/mã kết nối Google và Muse email/OTP cũ vẫn ở mục nâng cao. Không đổi cơ chế xác minh của dịch vụ, không giả định đăng nhập đồng nghĩa quota hoặc tạo nội dung đã thành công.
- Đóng/chuyển màn dọn lượt đăng nhập chưa lưu; phản hồi mở cửa sổ đến muộn được đóng đúng lượt. Muse save/cancel dùng cùng lock, hủy không xóa tài khoản đã lưu.
- Phiên lưu mã hóa như trước, không gửi prompt hoặc tạo ảnh/video khi đăng nhập. Không tự chuyển tài khoản cho công việc đã gửi.

Kiểm tra: Chromium sáu dịch vụ với API giả lập; không tạo mã ở đường chính, Gemini lỗi rồi lưu lại cùng cửa sổ, dùng lại tài khoản, hủy/mở muộn, Flow giữ đường cũ. Kiểm tra hàm backend thật với cửa sổ giả: lọc cookie Muse, save/cancel đồng thời, giữ phiên đã lưu, không đóng Gemini khi kiểm tra lỗi. Regression quản lý dung lượng đã qua. EXE kiểm tra payload và checksum nút tải. Chưa kiểm đăng nhập tài khoản dịch vụ thật hoặc trình cài trên Windows.
