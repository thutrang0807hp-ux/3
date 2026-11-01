# v46.20 — giữ upload .19 và sửa liên kết setting

Tải `SceneForge-Update-20261102-v46.20-Upload19-Settings.exe`. Đóng SceneForge, chọn thư mục có SceneForge.exe và install-settings.json, bấm Cập nhật rồi mở lại. Cài trực tiếp trên v46.7 trở lên của bộ cài v2, bao gồm .19; không cần cài lại .16 hoặc .18. Updater kiểm baseline, checksum và sao lưu file như trước.

## Upload

Gói .18 setting từng kèm hàm upload cũ nên làm lùi bản .19 đã chạy được. Gói này giữ **nguyên byte** `simple_flow_upload.py` từ EXE .19 người dùng gửi và xác nhận thành công:

`342e1bde247a0ca3612efe7c363cb0d741c84a1b014a71c35a402d1e6aba5869`

Vẫn là Add media menu ở thanh trên → Upload → giao ảnh; không quay về dò dấu + cạnh prompt. Bản kết hợp không tự thêm Ingredients, prompt hoặc tạo video. Upload và setting là hai thao tác riêng. Thử nút Chỉ tải ảnh lên dự án Flow trước, sau đó thử Áp dụng lên Flow trong cùng phòng.

## Setting

Trong node Veo có mục **Cấu hình Flow · bản thử .20**. Chọn Video, Khung hình/Thành phần, tỉ lệ, model và số kết quả; bấm Áp dụng lên Flow. Chưa thêm thời lượng hoặc chất lượng tải; x2–x4 không phải số luồng.

Sửa dò nhãn có icon Material, đọc lại các mục sau khi Flow cập nhật DOM, thử các mục còn lại khi Flow không cung cấp trạng thái lựa chọn. Chỉ báo khớp khi đọc lại đủ trạng thái đúng. Nếu chỉ bấm được nhưng chưa xác minh trạng thái: báo chưa xác minh, không coi là thành công. Model không có thì dừng, không đổi Lite thành Fast. Đây là áp dụng một chiều theo yêu cầu, không theo dõi hai chiều liên tục.

Khi chưa khớp: tải **báo cáo cài đặt**, không phải báo cáo upload, và xem ảnh bảng setting. Báo cáo có phase, field_results, observed và nhãn/thuộc tính trạng thái các nút; lưu cục bộ, không tự gửi đi. Có thể một số mục đã đổi trước khi lỗi.

## Kiểm chứng và phạm vi

Đã đối chiếu nguyên byte uploader với EXE .19, checksum từng file trong ZIP nhúng, giữ nguyên launcher. Đã kiểm Chromium mô phỏng đường menu Upload/hộp chọn tệp chậm và setting trên cùng trang; giao diện SceneForge gửi đúng cấu hình; model thiếu, nhãn có icon, trạng thái không xác minh, tài khoản đổi và tác vụ đồng thời đều có kiểm tra. Kiểm hồi quy upload giao đúng byte ảnh, không chạm prompt hoặc Generate.

**Upload .19 đã được người dùng xác nhận trên Flow thật; bản kết hợp .20 và setting mới chưa được xác nhận trên Flow thật. Chưa chạy updater trên Windows.** Giữ tài khoản, profile, dữ liệu và giao diện Tài khoản. Nút tạo video vẫn khóa.

Gói thay 4 file: simple_flow.py (nền .19, chỉ thêm đăng ký route setting), simple_flow_upload.py (nguyên byte .19), flow_settings.py và workflow.html.
