# Khung giao diện · menu & điểm dừng · 28/10/2026

Cập nhật: runner tự động mới đã thay đường dừng ở từng gate được mô tả dưới đây. Đọc [prompt-pipeline.md](prompt-pipeline.md) cho hành vi hiện tại: lần Chạy ban đầu cho phép tiến tới điểm dừng, chỉ dừng ở lỗi/thiếu dữ liệu/sửa tay, vẫn xem bản ghép trước khi xuất. Đường gate cũ còn là fallback khi module tự động không có; kiểm shell cũ chủ động tắt module mới để kiểm riêng đường đó.

Thuộc thanh khung dùng chung của Video mẫu và Ảnh tĩnh, không thêm node. Menu … có đúng ba mục: tiến độ/các lượt đã gửi (số clip xong, đang xử lý, lỗi/chưa rõ và thanh nhỏ), chi phí phòng này, hướng dẫn tab này. Nút ? cũ chuyển vào mục hướng dẫn. Tiến độ gọi bảng lịch sử thật của workflow; chi phí truyền roomId và lọc cả dòng chi phí lẫn xuất video. Số phí không có trong nhật ký không được tính là 0, không lấy số demo để báo chi phí thật trên menu.

Bảng Chạy tự động nằm dưới nút, có bốn bước theo từng chế độ. Video mẫu: đọc máy → hiểu/viết → ảnh khung → clip. Ảnh tĩnh: kịch bản → storyboard tổng → prompt → clip. Các phạm vi: chỉ phân tích/kịch bản; dừng trước clip; chạy đến clip. Dấu số là bước dự kiến, chỉ dùng ✓ nếu state thực tế đã hoàn tất. Không ghi mặc định Lite miễn phí hoặc giá 10/20/100.

Runner tiếp tục theo dữ liệu hiện có đến gate kế tiếp của workflow; chạy CPU với allowGemini:false rồi mở bảng rà AI, hoặc preflight ảnh/clip đúng phần thiếu. Không gửi cloud từ nút này, không tự duyệt, không gửi lại lỗi/unknown, không tự chuyển Dựng hoặc xuất video. Sau khi người dùng xử lý gate, bấm Chạy để tiếp tục đến điểm đã chọn. Đây không phải lời hứa chạy nền xuyên qua các lần duyệt. Luồng ảnh tĩnh giữ xem cả bản ghép và chốt một lần.

Chỉ nhớ điểm dừng theo roomId trong localStorage; lần sau vẫn mở bảng và rà kế hoạch. Chữ, nguồn, model, giá, lựa chọn khung/clip đổi khiến signature cũ bị từ chối; preflight gốc còn kiểm selection token và nội dung lúc gửi. Bấm lại nút, Esc, ×, bấm ngoài, đổi phòng đều đóng popover. Mobile giữ nút ▶ thu gọn, bảng không vượt màn hình.

Bản đồ của hai canvas cùng tô xanh chanh node đang chọn, bỏ màu node cũ, cập nhật bằng observer class/style. Sửa specificity CSS để màu selected và kéo khung vùng nhìn có tác dụng trên cả #minimap và #wsMinimap.

Kiểm Chromium: scripts/app-shell/check_workspace_automation.py và check_workspace_shell.py. Endpoint orchestration dùng fixture CPU/preflight (không gen thật), kiểm chặn stale plan/khung chưa duyệt/lượt unknown, đúng scene+part, nhớ scope không bỏ review, chi phí cách ly phòng, click node thật đổi màu map, mobile, không generation POST. Backend tạo nội dung vẫn là các adapter trước đó; chưa kiểm bằng tài khoản online.

Phân tích đã được chấp nhận được giữ nguyên: nút chạy không tự dò/chia lại video chỉ vì thiếu bản đo CPU cục bộ. Muốn phân tích lại dùng hành động riêng trong node Phân tích.
