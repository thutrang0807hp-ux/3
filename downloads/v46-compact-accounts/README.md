# SceneForge .91 — Tài khoản gọn & gỡ trực tiếp

Đóng SceneForge rồi cập nhật trên .90. Mở Cài đặt → Tài khoản.

- Thay sơ đồ nút nối bằng danh sách; tài khoản đang dùng lên đầu. Hiện tối đa năm ở tổng quan, bảng dưới vẫn đủ tài khoản.
- Email/tên dài thu gọn có dấu …; tooltip và Chi tiết cho xem nguyên tên. Không sửa metadata tên thật.
- Bảng còn sáu cột, gộp hiệu lực phiên vào trạng thái; thành công/thất bại, lần dùng và ghi chú nằm trong Chi tiết. Màn nhỏ chuyển thành thẻ, không kéo ngang bảng.
- Gỡ ngay trên mỗi dòng, một lần xác nhận. Gọi API accounts/remove cũ, giữ kiểm tra tác vụ của backend. Hủy xác nhận không gửi request; lỗi giữ nguyên dòng và cho thử lại. Không xóa tài khoản ở dịch vụ.
- Giữ chọn tài khoản, kiểm phiên, bật/tắt, sửa, kéo/mũi tên đổi ưu tiên; bỏ nút đăng nhập Flow bị trùng. Không sửa backend, session hoặc luồng đăng nhập web .90.

Kiểm tra Chromium với tên/email rất dài: không tràn sơ đồ/bảng, desktop/mobile, đủ sáu dịch vụ. Gỡ hủy/lỗi/thành công đúng id, không qua màn Sửa; chọn/kiểm/sửa vẫn chạy. Regression đăng nhập web .90 đã qua. Dịch vụ giả lập, không gỡ tài khoản thật. Kiểm tra EXE chứa đúng index.html và checksum nút tải; chưa chạy trình cài Windows thực.

SHA-256: 8757ecaf43b69796921d4c510da8b2e4228b4304ca554347ee96ca75552f3d87
