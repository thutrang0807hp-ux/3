# Trang chủ ổn định và Lưu trữ

Lưu trữ dùng thiết kế danh sách đã duyệt, trong cùng khung trang chủ: menu sản phẩm, tiêu đề và nút quay về. Trang sản phẩm giữ bốn cột Cần bạn / Máy đang chạy / Đang chuẩn bị / Đã xuất và các tab Bộ ảnh, Bộ cảnh, Chi phí. Dùng chung màu, font nhúng, khoảng cách và kiểu nút. Hàng sản phẩm giữ chiều cao khi số việc thay đổi.

## Giảm nhảy bố cục

Bỏ lượt dựng bảng sáu cột cũ trước khi dựng bốn cột mới. Cập nhật DOM theo ID video/cột/nhóm/sản phẩm, giữ ảnh đã giải mã và nút đang focus. Nhóm video vừa thả được dựng trong cùng lượt, không gỡ thẻ rồi tạo lại sau đó. Giữ vị trí cuộn theo sản phẩm, tab, bộ lọc, kiểu xem và Lưu trữ; giữ ô đổi tên đang nhập khi có cập nhật nền. Font có preload và display optional để tránh đổi font muộn. Đây là cải thiện đã đo trên Chromium, không phải cam kết tốc độ cho mọi máy hoặc mọi kích thước dự án.

## Lưu trữ

- Danh sách/khung trống, tìm theo tên hoặc sản phẩm, lọc sản phẩm, sắp theo ngày/dung lượng.
- Đo kích thước các Blob thuộc phòng trong kho files/workflow/editor của app; không giả định dung lượng thư mục máy hoặc tính bộ dùng chung. Đo bất đồng bộ, không dựng lại cả trang. Nút Đo lại cập nhật theo yêu cầu.
- Khôi phục giữ ID/timeline/tư liệu; bản xuất cũ đã khôi phục không tự quay về Lưu trữ ngay theo quy tắc bảy ngày. Khôi phục riêng một phòng thuộc sản phẩm lưu trữ vẫn giữ các phòng còn lại trong Lưu trữ.
- Xóa vĩnh viễn cần xác nhận; xóa dữ liệu riêng trong app, không xóa bộ ảnh/bộ cảnh dùng chung hoặc tệp đã ghi ngoài app; chặn tác vụ đang chạy/chưa rõ kết quả.
- Sản phẩm lưu trữ & Thùng rác vẫn mở được từ nút riêng; không tự bật hộp thoại khi vừa vào Lưu trữ.
- Không tự dọn khi vào trang. Dọn tệp tạm chỉ nhận khóa được đánh dấu cache:preview: hoặc cache:thumbnail:, cần xác nhận. Khi app không có các khóa đó, nút ghi Chưa có tệp tạm và bị vô hiệu hóa. Không dùng chức năng dọn video mẫu cũ dưới tên dọn cache.

## Kiểm tra

check_home_archive.py: giữ cùng node thẻ/ảnh/sản phẩm và focus; tám lượt render không có thay child/src ở bảng không đổi; cập nhật nền và quay lại từ Lưu trữ giữ scroll; đổi tên không mất chữ và Escape thoát đúng; vị trí tiêu đề/menu cố định; lọc/khung trống; đo byte thật trong IndexedDB thử; dọn cache giữ nguồn; khôi phục bản xuất cũ qua tải lại; giữ các phòng anh em trong Lưu trữ; hủy/xác nhận xóa và giữ bộ cảnh dùng chung; màn 1536/1366/390 px; không gọi provider trong demo.

Các kiểm tra Gói 6, thanh trên, Tài khoản và Thiết lập đầu tiên đều qua. Gói 6 vẫn kiểm tra 5 video thật trên CPU cục bộ, tối đa hai worker, tạm dừng/tiếp tục, mở worker đang chạy, lấy công thức và khôi phục sản phẩm. Chưa kiểm chứng tài khoản Flow/Muse thật trong thay đổi giao diện này.
