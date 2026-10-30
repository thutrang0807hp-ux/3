# Veo v41 — đường node → tab Flow

Đã sửa:

1. Sau khi đổi sang kết nối web trong cùng phòng, Đọc lại model cập nhật model I2V duy nhất của đường web, lưu lại cấu hình node. Hộp gửi cũng loại bỏ lựa chọn engine cũ nếu đường web hiện chỉ cung cấp một model I2V hợp lệ. Các engine có nhiều model giữ nguyên lựa chọn thủ công.
2. Trạng thái kết nối Google không bắt tài khoản web_ui phải có khóa/engine_instance của Flow2API.
3. Binding web_ui hiện tại được dùng để chọn worker gửi, thay vì để native_route_id cũ còn sót chuyển lệnh sang engine.

Kiểm tra:

- Tái hiện lỗi model trên frontend lấy từ gói v40 đã phát hành, với test chờ phản hồi và chờ trạng thái bất đồng bộ.
- check_video_node đạt trên frontend xây lại và chính frontend giải nén từ payload v41: model/node/hộp gửi, prompt writer, ảnh đầu, giữ lượt chưa rõ, chống gửi trùng và đổi phòng.
- check_flow_managed_browser đạt với tài khoản UI không có engine key và native_route_id cũ được cố ý chèn vào: hai lượt ảnh+prompt đến đúng worker, nhận video fixture, không gọi engine; tài khoản/project đổi dừng.
- check_flow_login_tabs và check_flow_managed_workers đạt.
- Hash từng file payload, ZIP toàn vẹn, compile toàn bộ Python và xác nhận marker Veo v41 trong HTML đạt.

Tất cả là kiểm tra local/intercepted fixture. Chưa chạy updater trên Windows; chưa xác minh video thật trên Google. Lỗi Google từ chối đăng nhập không do lựa chọn model trên node và chưa được giải quyết bởi bản này. V41 tập trung đường kết nối tab web hiện có.

Cách dùng: đóng SceneForge rồi cập nhật; mở lại phải thấy Veo v41. Dùng kết nối riêng Flow bằng mã/tiện ích trên tab dự án đã đăng nhập; giữ tab mở. Ở node bấm Đọc lại model rồi thử một clip đã duyệt ảnh và có prompt. Không tự gửi lại lượt chưa rõ kết quả.
