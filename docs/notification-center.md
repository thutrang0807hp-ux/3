# Bảng thông báo gọn — 27/10/2026

## Chức năng
- Rộng 360px (co lại trên điện thoại), cao tối đa 560px. Tiêu đề và bốn tab đứng yên, danh sách bên trong cuộn. Tab Tất cả / Cần bạn / Xong việc / Lỗi. Lỗi là tập con Cần bạn; badge chuông đếm một dòng cần xử lý chưa đọc, không cộng hai lần vì hai tab.
- Ảnh nhỏ của video, biểu tượng loại, tên, mô tả và giờ. Chia Hôm nay / Hôm qua / Trước đó. Gom nhiều thông báo của cùng video trong ngày thành nhóm mở được; thông báo cùng loại, video và nguồn trong ba phút gộp một bản ghi với số lần. Bản ghi nhiều phòng cũ giữ nguyên và có bước chọn đúng phòng.
- Mở/đóng bảng không đánh dấu đã xem. Bấm dòng hoặc nút hành động mới ghi read=true. Đã xem làm mờ dòng nhưng không xóa việc khỏi Cần bạn. Đã xem hết nằm góc trên. Rê/đưa focus vào dòng đã xem mới hiện × xóa; xóa chỉ bỏ notification, không xóa/hủy job hay dự án.
- Nút Duyệt khung mở đúng phòng và tập trung node Ảnh khung nếu API của workspace có sẵn; không tự duyệt. Kết nối lại mở đúng màn tài khoản khi có nguồn xác định; không tự gửi lại. Xuất xong mở Dựng. Không đoán một phòng nếu thông báo cũ gộp nhiều phòng.
- Cần bạn bỏ các mục được ghi resolved/resolvedAt, hoặc thông báo khung khi phòng đã có trạng thái pendingFrames=0 mới hơn thông báo. Lỗi cũ thiếu dữ liệu kết thúc đáng tin vẫn giữ; không suy rằng đã xử lý từ việc đã xem hoặc mở Cài đặt. Chưa có cơ chế tự xác nhận hết mọi lỗi provider cũ.
- Bấm lại chuông / × / Esc / ngoài bảng đóng. Logo S (trang chủ) cũng đóng bảng và thông báo nổi, vẫn giữ hành vi về trang chủ đã có. Hai bảng Hàng chờ/Thông báo không mở chồng. Hàng chờ và pause giữ nguyên cơ chế trước.
- Thông báo nổi góc dưới cho việc Cần bạn/xuất xong, chỉ một thẻ, tự ẩn 6 giây; gộp số lượt đến liên tiếp. Rê chuột giữ lại, rời chuột 2 giây thì ẩn. Nút × chỉ đóng toast, không đánh dấu đọc. Có checkbox Thông báo nổi trong app ở Cài đặt → Thông báo, dùng prefs.package5.floating. Không thay quyền desktop.

## Kiểm tra
8 bài đạt: browser/IndexedDB thật cho kiểu dáng, nút, đọc/xóa, chuyển tác vụ (navigation spied), trạng thái đã xem khác đã xử lý, gộp theo phòng, toast bật/tắt, logo, mobile và không gửi API trong demo; hồi quy Hàng chờ, journal SQLite, Batch, Settings, Lưu trữ. Test local đọc/xóa notification ghi vào SQLite và giữ qua profile trình duyệt mới; dự án và byte nguồn không mất. Mô phỏng HTML dùng chính renderer/CSS, hợp đồng thao tác giả trong bộ nhớ, không mạng/server/phụ thuộc ngoài.
Chưa kiểm gen tài khoản online hay Windows. Mô phỏng không tạo ảnh/video hoặc đăng nhập tài khoản thật.

## Khôi phục môi trường và đóng gói
Workspace mới chỉ còn Git metadata. Khôi phục runtime từ ZIP tại published commit 538cf9d, SHA256 1d4e94a72c488e14df5a1d732c01941aff3e72a302a778ffedd1e165cbdd445f; source liên quan từ hai gói audit cùng commit. Không có đầy đủ design assets gốc để chạy lại builder toàn bộ.
Thay đổi UI nằm trong scripts/app-shell/notification-center.js/.css. scripts/demo-web/patch_notification_center.py chèn module có marker idempotent vào bốn bundle đã khôi phục, giữ nguyên các workflow/editor bundle. build.py cũng thêm module vào thứ tự nạp để build đầy đủ sau khi có lại asset nguồn. ZIP runtime giữ nguyên tất cả entry cũ, thay bundle shell và thêm module/tài liệu/kiểm mới; backend không đổi. Hai gói code gọn đã cập nhật manifest.
