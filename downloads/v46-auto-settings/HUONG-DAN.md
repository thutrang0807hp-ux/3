# SceneForge .54 — tự đồng bộ cài đặt Flow

Cập nhật từ .52 hoặc .53. Đổi lựa chọn trong bảng Cấu hình Flow là đủ; phần mềm
chờ khoảng 0,5 giây rồi gọi đường áp dụng cài đặt hiện có. Không cần bấm Áp dụng.
Giao diện chờ Flow xác nhận và hiển thị trạng thái; nếu lỗi có nút Thử đồng bộ lại.
Không tự gửi tạo video khi thay cài đặt.

Lúc đang tạo video hoặc đang áp dụng cài đặt, điều khiển được khóa để tránh
xung đột. Tạo video chờ lượt đồng bộ hoàn tất. Không gửi cấu hình chờ sang phòng
hoặc tài khoản mới nếu người dùng đã đổi ngữ cảnh.

So với .53 chỉ frontend thay đổi. Gói kèm lại nguyên bốn tệp backend .53 để cập
nhật trực tiếp từ .52; checksum xác nhận không thay mã tạo, upload hoặc nhận video.
Giữ cơ chế một ảnh/một video và lấy lại video cũ của các bản trước.

Đã kiểm tra sáu nhóm hành vi đồng bộ tự động, UI nhận lại clip và cú pháp mười
script frontend; kiểm tra lại trên frontend trích từ EXE. Backend đồng bộ dùng
route cũ. Chưa xác minh thao tác Flow thật hoặc updater trên Windows.

SHA256 EXE: `178a04a7db423656bd99e66bea07582cb20221a36933979f9c9d4c22bb3ced36`
