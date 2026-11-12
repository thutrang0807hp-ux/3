# SceneForge .121 — tệp còn lại và nơi đang giữ

Đóng SceneForge, chạy **SceneForge-Update-20261112-v46.121-File-Holders.exe**, chọn đúng thư mục ứng dụng rồi mở lại. Bản gộp nhận từ .62 trở lên, gồm .119/.120.

Trong **Lưu trữ & Thùng rác**, bấm **Xem tệp còn lại** ở lượt dọn còn file. Bảng hiển thị đường dẫn, dung lượng và lý do thực tế: dự án và tên dự án, bản ghim và ghi chú, mã/trạng thái tác vụ, hạn giữ của tệp vừa tải lên chờ lưu, hoặc tên bản sao lưu. Có nút tải báo cáo JSON để kiểm tra tiếp nếu chưa xử lý được.

- Nếu tệp **chỉ còn trong sao lưu**, bảng có nút **Xóa tệp chỉ còn trong sao lưu…**. Phải xác nhận rõ việc mất khả năng khôi phục tệp đó từ các bản sao lưu được liệt kê. App kiểm tra lại nơi giữ trước khi xóa; nếu xuất hiện người dùng/tác vụ mới, lệnh bị chặn.
- Nếu tệp đang ghim, có nút bỏ ghim riêng. Bỏ ghim chưa tự xóa; xem lại lý do rồi thử xóa nếu đủ điều kiện.
- Nếu còn dự án khác dùng, bảng có nút mở dự án đó khi dự án có trong app. Không có nút cưỡng ép xóa file chung hoặc file đang chờ tác vụ/lưu.
- Nếu bấm Xóa ngay mà vẫn còn tệp bảo vệ, app tự mở bảng chi tiết. Thông báo dung lượng tính phần xóa thêm trong lần hiện tại, không lặp lại tổng dung lượng đã xóa của các lần trước.

Không xóa toàn bộ sao lưu hay tệp ngoài app. Hành động xóa bản chỉ còn trong sao lưu dùng chính sách giải phóng theo dự án/hash hiện có để sao lưu cũ được khôi phục với dấu “tư liệu đã giải phóng”, không làm xuất hiện tham chiếu tới file mất.

Kiểm tra: SQLite, API và tệp thật; UI Chromium; chống xác nhận cũ khi có dự án dùng lại; giữ bản ghim/tệp tải chờ lưu/tác vụ; xóa bản chỉ còn trong sao lưu và khôi phục sao lưu an toàn; bộ hồi quy xóa/thùng rác trước đó. Chưa chạy bộ cài Windows hoặc kiểm tra tệp cụ thể trên máy người dùng.
