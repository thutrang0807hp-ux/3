# Lối vào hai cách tạo video

Giữ nguyên trình node và cơ chế mở phòng riêng theo từng hướng. Thay hai nút chữ nhỏ bằng cụm chọn ở đầu màn hình: biểu tượng SVG, tên hướng và mô tả ngắn; nút đang chọn có nền vàng chanh, nút còn lại có trạng thái rê chuột/focus rõ. Hiện cả hai hướng trong phòng video mẫu và phòng từ ảnh. Bổ sung aria-pressed và aria-busy; trong lúc lưu/chuyển phòng, hai nút bị khóa tạm.

Thanh phòng cao 56 px, thanh chọn hướng 66 px; vùng node co giãn bên dưới, không bị che. Trên màn hẹp, thanh tiến trình có thể cuộn ngang; nút chọn hướng vẫn nằm ở đầu thanh. Giữ các chip tài khoản/hạn mức và bốn bước của hướng video mẫu, nút mở workspace ảnh cũ, dữ liệu và các vị trí node.

Đã kiểm tra trình duyệt: chuyển trực tiếp hai hướng, ghi nhớ phòng, giữ nội dung đã sửa trong video mẫu khi quay lại; node ảnh không chồng nhau; sắp xếp/hoàn tác; không hở khoảng trống giữa header và viewport ở các độ rộng; tài khoản/hạn mức/Chi tiết, hàng chờ và Sang Dựng hoạt động; tải lại giữ phòng; khung đã duyệt, clip Blob và kịch bản trong workspace ảnh cũ còn nguyên khi mở cả bản cũ và mới. Demo không gọi API.
