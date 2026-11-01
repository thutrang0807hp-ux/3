# SceneForge v46.19 — tách các bước upload dự án

Bản cập nhật nhỏ cho máy đã có v46.7 trở lên. Phiên bản cài: `2026.11.02.4619`.

Đóng SceneForge, chạy `SceneForge-Update-20261102-v46.19-Project-Upload.exe` và chọn đúng thư mục đang chạy (máy đã kiểm tra: `D:\4\releases\2026.10.28.2`). Mở lại app và dùng nút **Chỉ tải ảnh lên dự án Flow** với một ảnh.

Luồng mới mở **Add media menu** trên thanh trên, chọn **Upload** và giao tệp. Không gọi lại hàm dò nút thêm ảnh cạnh prompt. Nếu lỗi, báo cáo giữ `failed_phase`, `upload_error`, danh sách bước và điều khiển đang thấy. `upload_implementation` phải là `project_upload_v46_19`.

Bản này chỉ sửa upload; không tự điền prompt, chọn Ingredients hay tạo video. `file_delivered` chỉ xác nhận trình duyệt nhận tệp, chưa xác nhận Flow lưu thành công. Không thay đổi Data, tài khoản hoặc mô hình.

Kiểm tra: bốn tình huống Chromium mô phỏng đã qua; payload trong EXE khớp mã nguồn và checksum. Chưa kiểm thử trên Flow thật hoặc trình cài Windows của người dùng.
