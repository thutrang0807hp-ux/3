# SceneForge v46.57 — theo dõi Flow trong lúc CLI chạy

Cập nhật trên bản .52 trở lên. Đóng SceneForge, chạy `SceneForge-Update-20261103-v46.57-Live-Flow-Progress.exe`, rồi mở lại ứng dụng.

- Đọc trực tiếp log JSON từ CLI gốc, không sửa SDK/session hoặc thêm lệnh tạo.
- Ghi và hiển thị ID video khi CLI quan sát được phản hồi tạo trong đúng dự án; giữ workflow ID nếu có.
- Hiển thị các bước thật: chuẩn bị, gửi tạo, chờ/xử lý, tải và kiểm tra tệp; có thời gian chờ.
- CLI hiện không cung cấp phần trăm: thanh chờ không xác định, không dựng phần trăm giả.
- Giữ cấu hình đã chọn, một ảnh tham chiếu, x1 video và phục hồi tải xuống mà không gửi tạo lại.

Kiểm tra trên đúng 7 tệp nhúng trong EXE: 14 kiểm thử CLI, 4 kiểm thử log tiến độ, tuyến submit/lookup ghi ID trước khi CLI thoát, tải phục hồi và giao diện nhận ID. Dùng CLI giả lập cục bộ; chưa xác minh trực tiếp Flow hoặc chạy bộ cài trên Windows. Thời điểm nhận ID phụ thuộc log CLI/Flow; không bảo đảm mọi giao diện Flow trả ID sớm.

SHA256: `72ed73e0b595c47ca58963318efbdbded235f0c6fb6bbc9275af6fec4469fbcf`
