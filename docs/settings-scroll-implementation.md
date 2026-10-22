# Cài đặt · khung cố định, cuộn nội dung

Các tab dùng chung khung tối đa 1250×750 px, thu theo màn hình (khoảng cách 20 px trên/dưới). Dialog dùng hai hàng: header 76 px và vùng nội dung co giãn; không cuộn cả dialog. Footer rỗng không chiếm thêm chiều cao.

Menu trái độc lập với nội dung. Tiêu đề Cài đặt/nút đóng và tiêu đề tab hiện tại đều cố định. Nội dung tab nằm trong `.g5SettingsScroll`, cuộn bằng con lăn, có scrollbar riêng và chặn cuộn lan ra nền. Chuyển tab không đổi kích thước/độ cao khung. Tab AI giữ cột động cơ có cuộn riêng khi cần. Màn hẹp chuyển menu thành hàng ngang cố định, nội dung vẫn cuộn riêng.

Không thay điều kiện hiển thị Thiết lập đầu tiên, dữ liệu tùy chọn hoặc hành vi lưu. Đồng bộ lời chú thích Xuất video với renderer FFmpeg trực tiếp đã có, bỏ mô tả lỗi thời rằng mọi MP4 đều phải ghi trình duyệt trước.

Đã kiểm tra trình duyệt thật với con lăn: cùng kích thước qua sáu tab; chỉ scrollTop vùng nội dung thay đổi; tọa độ header, tiêu đề tab và menu không đổi; dialog/body không cuộn. Kiểm 1366×900, 1366×768 và 390×740; title canh trái cùng nhãn nhỏ; nút đóng hoạt động; không lỗi JavaScript. Đây là thay đổi bố cục, không bổ sung dịch vụ AI hoặc dữ liệu mẫu vào tài khoản thật.
