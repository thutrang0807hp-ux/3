# SceneForge v46.49 — lấy lỗi khởi chạy Flow

Đây là bản bổ sung chẩn đoán, **chưa phải bản xác nhận sửa xong lỗi Windows**.
Báo cáo .48 chỉ còn câu “Engine Flow dừng” vì bộ nối đã bỏ mất loại lỗi gốc.

Chạy EXE cập nhật bản .42 trở lên, rồi thực hiện lại một lượt bằng nút Tạo video
hiện có. Nếu vẫn dừng, tải báo cáo của lượt mới. Trường `engine_diagnostics`
ghi bước lỗi, loại lỗi, chi tiết đã che dữ liệu nhạy cảm và vị trí mã nguồn.
Báo cáo cũ không thể bổ sung chi tiết đã bị bỏ mất.

Không thay luồng chuẩn bị hoặc cơ chế tạo của .48. Không tự gửi lại lượt cũ.
Đã kiểm tra SDK thật/Chromium với HTTP giả lập, hủy trước khi cấp quyền tạo;
10 kiểm tra protocol và 4 kịch bản dispatch qua mã lấy từ EXE cũng qua.
Chưa chạy Windows/Flow thật, chưa xác định nguyên nhân lỗi máy người dùng.

SHA256 EXE: `a23425c0cd2bf7f77f477a706b99bad612b8c70573092af9bdefaada80becbf4`
