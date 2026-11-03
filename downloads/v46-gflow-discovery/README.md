# SceneForge v46.59 — tìm GFlow và báo lỗi đúng trạng thái

Đóng SceneForge, chạy `SceneForge-Update-20261104-v46.59-GFlow-Discovery-Fix.exe`, mở lại. Cập nhật trên .52 trở lên, gồm .58.

Báo cáo người dùng xác nhận lỗi xảy ra trước khi CLI chạy: không tìm thấy GFlow trong Downloads, chưa upload/gửi tạo. Không phải lỗi trả video từ Flow.

- Ưu tiên đường dẫn GFlow từ lượt thành công trước đây của đúng tài khoản.
- Nhận wrapper GFlow cập nhật theo module CLI thực tế hoặc requirements có pin CLI, thay vì chỉ chấp nhận một mã băm app.py cũ.
- Tìm sâu hơn trong Downloads, đọc cả hai vị trí registry Windows, OneDrive Downloads, thư mục đang chạy và Desktop; giới hạn 3000 thư mục, không chạy file trong lúc dò.
- Vẫn kiểm tra đúng email/profile; nhiều bản khớp mà không có lịch sử thì không tự đoán.
- Thiếu GFlow trước khởi chạy được ghi rõ submitted=false; không tự gửi lại.
- Cửa sổ clip cập nhật nhãn, lỗi và các nút khi lượt kết thúc, không giữ overlay Đang tạo sau thất bại.

Bản sửa không cài hay tải lại GFlow. Nếu thư mục/runtime gốc đã bị xóa hoặc chuyển ngoài nơi có thể tìm, cần khôi phục bản đã chạy được vào Downloads hoặc đặt SCENEFORGE_GFLOW_REPO tới thư mục thật. Dữ liệu tài khoản/session và CLI gốc được giữ nguyên.

Đã kiểm tra đúng tệp nhúng EXE: 20 kiểm thử CLI/discovery, tuyến backend submit/lookup (thiếu GFlow => không upload, không gọi CLI, submitted=false), Chromium kiểm tra failed mở lại các nút và xóa nhãn đang tạo. Các đường tạo/tải/nhập tuần tự qua fixture cục bộ vẫn đạt. Chưa kiểm tra trực tiếp ổ đĩa Windows hay tài khoản Flow của người dùng; chưa chạy bộ cài Windows.

SHA256: `e2d33bacc6616f41b2e7131bd04015cc796aebb587f1b5e9f4f8e15bdd76cb41`
