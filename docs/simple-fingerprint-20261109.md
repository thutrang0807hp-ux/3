# SceneForge .95 — Fingerprint gọn, bấm một lần

Đóng SceneForge rồi cập nhật trên .94.

- Icon vân tay cạnh trạng thái tài khoản: xanh bật, xám tắt; title và aria-pressed thể hiện lựa chọn đã lưu. Không mở hộp thoại ở thao tác thường.
- App tự tạo cấu hình mặc định và profile do app quản lý cho tài khoản hỗ trợ chưa có profile; không bắt người dùng nhập CPU/RAM. Flow vẫn cần binding profile đăng nhập web riêng, không sửa trình duyệt cá nhân của tiện ích.
- Toggle chỉ đổi enabled trong cấu hình, giữ seed và các thông số đã chỉnh. Được lưu khi browser đang chạy nhưng chỉ áp dụng lúc mở lại browser, không thay script của phiên đang chạy hoặc ngắt công việc.
- CPU/RAM/màn hình nằm trong Chi tiết → Fingerprint · nâng cao, mặc định thu gọn.
- Trạng thái tải theo một request cho mỗi panel tài khoản, cập nhật thuộc tính icon trực tiếp; toggle không render lại sơ đồ hoặc bảng. Chặn bấm lặp khi đang gửi, giữ lựa chọn cũ nếu lỗi; version per-account tránh phản hồi cũ ghi đè lựa chọn mới.
- Giữ sơ đồ, gỡ trực tiếp, mở phiên và luồng đăng nhập .94. Không mở rộng phạm vi fingerprint (CPU/RAM/screen/viewport); không bảo đảm chống đăng xuất hoặc xác minh.

Kiểm tra: Chromium và API fixture thật cho toggle lúc bận vẫn giữ document cũ, tự tạo cấu hình, giữ tham số/seed, idempotence, body validation; UI một lần bấm không mở modal/không đổi DOM sơ đồ, trạng thái và nâng cao đồng bộ, hồi quy đăng nhập/sơ đồ/gỡ. Không có tài khoản dịch vụ thật; chưa chạy trình cài Windows. EXE kiểm tra payload và checksum.
