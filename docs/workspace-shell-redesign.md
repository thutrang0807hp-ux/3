# Khung tạo video chung — 27/10/2026

## Đã đổi
- Cả Video mẫu và Từ ảnh & ý tưởng dùng một hàng trên 56px trên desktop, 96px/hai hàng trên màn hình nhỏ. Chuyển chế độ mở đúng phòng đã nhớ, không đổi loại dự án hoặc mất tư liệu.
- Hiện bước theo dữ liệu hiện có; bấm bước chỉ tập trung node. Duyệt, nhận kết quả, chuẩn bị và gửi vẫn gọi luồng cũ.
- Viên nguồn mở trạng thái/tài khoản và lối vào Cài đặt. Bên ảnh lưu creative/video riêng theo phòng. Muse ảnh ghi rõ thủ công, Muse video ghi rõ muse.ai, không tự nhận là Meta. Video mẫu dùng cấu hình AI chung hiện có và Flow, chưa có ghi đè nguồn riêng cho phòng. Tài khoản/phân phối dùng Cài đặt cũ; không sửa nguồn của job đã gửi.
- Công cụ chọn/kéo nền, thêm tư liệu, zoom, căn vừa, nhạc/hướng dẫn và bản đồ nhỏ xuống dưới trái. Nhãn chữ thu sau 3 giây khi rời chuột; biểu tượng luôn còn. Bên ảnh giữ xếp như mẫu và hoàn tác. Pan chỉ đổi view, không kéo node.
- Bản đồ ảnh dựa trên vị trí node thật và bấm để di chuyển view. Bản đồ video dùng bản đồ hiện có. Nút chính/tóm tắt chuyển xuống giữa dưới, giữ các tùy chọn sản xuất cũ trong menu ba chấm.
- Chạy hỗ trợ ghi rõ phạm vi: Video mẫu chỉ phân tích CPU, dừng trước gửi Gemini; chặn khởi chạy khi có aiRequest để tránh nối lại/gửi thêm ngoài ý muốn. Bên ảnh chỉ tiếp tục một bước có sẵn, giữ các bước xác nhận. Chưa triển khai tự chạy toàn bộ như chữ Chạy tự động trong bản vẽ.
- Giữ node, lời, prompt, receipt/journal, engine và model. Không sửa backend, không thêm nguồn giả, không tự gửi lại hay phát sinh credit do mở giao diện.

## Kiểm tra và giới hạn
Chromium thật với parent/iframe: thanh 56px, năm bước, nguồn, đổi provider ảnh giữ beats/jobs, phòng riêng hai chế độ, zoom, bản đồ, xếp/hoàn tác, pan trên header không đổi node, mobile 390×844 không tràn, hộp phạm vi CPU và không POST tạo nội dung. Demo dùng IndexedDB; không chứng nhận phiên online. Kiểm hồi quy thông báo và lưu trữ, trong đó lưu trữ chạy SQLite thật qua profile mới, xóa/khôi phục và bảo toàn byte thành phẩm. Xem workspace-shell-checks.json. Chưa thử tạo AI bằng tài khoản thật hoặc Windows.

## Cách dựng và đóng gói
Runtime khôi phục từ bản phát hành 487496c. Chưa có đủ design assets gốc để dựng toàn bộ. patch_workspace_shell.py chèn module có marker vào sáu HTML, cập nhật cache key của iframe; gọi lại không nhân đôi module. build.py gọi patch cuối chuỗi cho lần dựng đầy đủ sau này. ZIP giữ nguyên từng byte của mọi entry runtime cũ trừ sáu HTML đã sửa; thêm module, test và tài liệu. Không đóng gói vault/session/tài khoản cá nhân.
