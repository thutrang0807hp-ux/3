# SceneForge .89 — Dữ liệu & dung lượng

Đóng ứng dụng rồi chạy cập nhật trên .88. Mở Cài đặt → Dữ liệu & dung lượng.

- Bảng số file/ảnh/video và byte thực ở kho dự án & sao lưu, bản xuất cấu hình trong app, mô hình AI, ZIP cache thư viện, tệp làm việc media/ghép/phân tích. Tổng vật lý không đếm trùng cùng inode; bản sao riêng vẫn tốn thêm dung lượng.
- Dự án: tìm kiếm, lọc, sắp theo dung lượng/cập nhật/tên, chọn nhiều mục. Số file trong mỗi dự án khử trùng theo hash và có nhãn dùng chung; không cộng các dòng thành số byte sẽ giải phóng.
- Dùng lại lifecycle hiện có: dọn bản thừa, giữ thành phẩm, xóa dự án. Có xem phạm vi, xác nhận, thời gian chờ, kiểm tra revision, bảo vệ file chung/ghim/sao lưu/tác vụ. Thống kê không tự xóa dữ liệu.
- Dọn file tạm chỉ ZIP xem trước thư viện quá một giờ, có kế hoạch và token kiểm tra lại. Không dọn model, bản xuất, tư liệu dự án hay tùy tiện xóa cache động cơ.
- Rà file hết tham chiếu dùng cơ chế Thùng rác hệ điều hành hiện có; dung lượng chưa được giải phóng ngay nếu file còn ở Thùng rác.
- Quét giới hạn 5 giây / 50.000 entry và báo chưa đầy đủ. Không quét toàn ổ, file Save As tùy ý hoặc model ở vị trí không cấu hình. Mốc cập nhật dự án là metadata lưu trong app, không giả định là lần mở gần nhất.

Kiểm tra Chromium + SQLite/file thật: số file và dung lượng, file chung giữa hai dự án, không đi theo symlink, thư mục render, tìm/lọc/chọn, đơn và hàng loạt mở đúng bước xem trước, không xóa khi chưa xác nhận; cache hủy/xác nhận, model và dự án còn nguyên; bố cục desktop/mobile. EXE kiểm tra payload và nút tải/checksum; chưa chạy trình cài Windows thực.

SHA-256: 2b80cdb752377c99788d7317d44d9470afda8617b1c4ff0f51e277c12631ed5d
