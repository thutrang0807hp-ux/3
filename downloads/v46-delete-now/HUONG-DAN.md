# SceneForge .120 — xóa hẳn không mặc định chờ

Đóng SceneForge, chạy **SceneForge-Update-20261112-v46.120-Delete-Now.exe**, chọn đúng thư mục app đang dùng rồi mở lại. Nhận từ .62 trở lên; gồm các cập nhật .118 và nhập link ghép tiếng .119.

- “Xóa hẳn” mặc định **Xóa ngay** (0 ngày), cho cả một hoặc nhiều dự án. Vẫn có thể chủ động chọn giữ 7/30 ngày và xem/xác nhận phạm vi như trước.
- Với các lượt cũ trong Thùng rác, nút **Xóa file đủ điều kiện ngay…** xuất hiện cả khi đã quá hạn, bị giữ hoặc cần thử lại. Không phải đợi đủ ngày.
- Ngày tạo lượt dọn đổi đúng từ giây sang mili giây, không còn hiện năm 1970. Mục đang bị giữ không bị tính như đang chờ hết hạn trong 3 ngày.
- Sau xử lý, app báo dung lượng đã giải phóng và số file vẫn được bảo vệ. Tài nguyên còn dùng ở dự án khác, ghim, tác vụ, lượt tải chưa lưu hoặc sao lưu phù hợp vẫn được giữ; nhấn xóa không cưỡng ép xóa file chung.

Đã kiểm bằng Chromium, API thư viện thật, SQLite và tệp thật: lựa chọn 0 ngày cho xóa một/nhiều, giữ 30 ngày khi chủ động chọn, xử lý một lượt quá hạn qua nút UI, tệp được xóa, không có tư liệu bị thiếu và không gọi dịch vụ tạo nội dung. Chưa chạy bộ cài trên Windows.
