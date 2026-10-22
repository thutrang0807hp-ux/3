# Thêm ảnh trực tiếp vào Bộ ảnh sản phẩm

Giữ trang chủ bốn cột và bố cục bốn nhóm Người / Trang phục / Sản phẩm / Bối cảnh. Mỗi nhóm có nút Thêm ảnh, chọn nhiều tệp cùng lúc, số lượng ảnh và ảnh thu nhỏ bấm để xem lớn. Giữ nút Chỉnh bộ ảnh để sửa mô tả hoặc quản lý ảnh như trước.

Ảnh được kiểm tra loại tệp, giới hạn 15 MB mỗi ảnh, đọc/thu nhỏ bằng bộ xử lý ảnh có sẵn rồi lưu vào nhóm trong IndexedDB của sản phẩm. Ghép vào bản ghi mới nhất trong một transaction, giữ ảnh và mô tả đang có. Hiển thị trạng thái lưu và chặn mở bản chỉnh sửa cũ trong lúc ảnh đang lưu. Ảnh lỗi bị bỏ qua và báo tên tệp; các ảnh hợp lệ vẫn được nhận. Không gọi API hoặc tự suy ra mô tả từ ảnh.

Không sửa room.refs hay photoDraft của phòng cũ; phòng mới tiếp tục lấy bản sao bộ ảnh sản phẩm theo cơ chế đang có. Các nút tải, xem ảnh và chọn nhiều tệp hoạt động cả trong demo (kho demo riêng) và bản chạy cục bộ.

Đã kiểm tra trình duyệt: nút chọn tệp thật; thêm hai ảnh cùng lúc, thêm vào cả bốn nhóm; giữ ảnh trước đó; cập nhật số tổng; xem tên/ảnh lớn; loại tệp không phải ảnh và tệp hỏng; tải lại vẫn giữ đủ ảnh; các snapshot bộ ảnh phòng cũ không đổi; hộp Chỉnh bộ ảnh còn hoạt động; màn 390 px không tràn; không gọi API trong demo.
