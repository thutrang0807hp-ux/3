# SceneForge v38 — worker trình duyệt theo tài khoản

- Giữ kết nối CDP theo tài khoản; hàng đợi riêng cho mỗi worker.
- Đọc lại binding sau khi chờ; kiểm tra tài khoản và tab trước tác vụ.
- Hủy/lỗi loại bỏ worker liên quan; không tự gửi lại video.
- Đóng app ngắt driver, giữ Chrome và profile.

Vẫn dùng Playwright + DOM hiện có. Chưa chuyển toàn bộ Puppeteer/API như Phoma. Không thay runtime, không sửa việc Google từ chối đăng nhập. Chưa xác minh tạo video thật trên Windows/Google. Nếu đang kẹt đăng nhập, bản này không được kỳ vọng giải quyết lỗi đó.

Đã kiểm tra worker lifecycle, login startup/failure, toàn tuyến ảnh+prompt→một lượt gửi→video trong trang Chromium bị chặn mạng và thay bằng fixture; hash/compile payload đạt.
