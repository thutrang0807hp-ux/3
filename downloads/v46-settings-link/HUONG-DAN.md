# v46.17 — thử liên kết cài đặt SceneForge → Flow

Cài trên **v46.16**: đóng SceneForge, chạy `SceneForge-Update-20261101-v46.17-Settings-Link.exe`, chọn thư mục có SceneForge.exe và install-settings.json, bấm Cập nhật rồi mở lại. Updater dùng cơ chế sao lưu của bản cũ; không thay tài khoản, profile hoặc dữ liệu.

Trong node Veo, chọn **Cấu hình Flow**: Video, Khung hình/Thành phần, 16:9/9:16, Veo 3.1 Lite/Fast/Quality và x1–x4. Bấm **Áp dụng lên Flow**. Đây là đồng bộ theo yêu cầu từ phần mềm sang dự án Flow của phòng hiện tại, không phải theo dõi hai chiều liên tục. Chưa thêm thời lượng hoặc chất lượng tải.

Chỉ báo khớp khi đọc được trạng thái được chọn trên các nút Flow và model đang hiển thị. Nếu model không có, trạng thái không đọc được, hoặc tài khoản đổi: báo chưa đồng bộ, không tự thay model. Một số mục có thể đã đổi trước khi dừng; xem ảnh và tải báo cáo cài đặt để kiểm tra. Nhãn khớp là kết quả lần kiểm tra gần nhất, không bảo đảm cấu hình không bị thay ở ngoài phần mềm sau đó.

Giữ nguyên nút **Chỉ tải ảnh lên dự án Flow**. Bản này không gắn ảnh, điền prompt hoặc tạo video; nút tạo vẫn khóa. x2–x4 là số kết quả của mỗi lượt trên Flow, không phải hàng đợi hay số luồng.

**Kiểm chứng:** đã chạy Chromium với trang Flow mô phỏng và giao diện SceneForge thật, kiểm tra payload, đọc lại lựa chọn, tài khoản đổi, thao tác lặp, model thiếu và trạng thái không xác minh được. Đã kiểm checksum, ZIP nhúng và đối chiếu từng file EXE với nguồn. **Chưa chạy updater trên Windows và chưa chứng minh setting hoạt động trên Flow thật.**

Để xác minh trên máy người dùng: áp dụng một cấu hình, xem ảnh Flow sau thao tác và đối chiếu từng mục. Nếu báo lỗi, gửi báo cáo cài đặt cùng ảnh bảng setting; chưa thử tạo video để kiểm tra setting.

Gói thay đúng 3 file: `app/local_engine/simple_flow.py`, `app/local_engine/flow_settings.py`, `app/dist/web-demo/workflow.html`. Hàm upload và giao diện Tài khoản không bị thay.
