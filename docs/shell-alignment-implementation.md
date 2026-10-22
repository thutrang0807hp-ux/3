# Khung tab đồng nhất và logo mới

Logo chữ nhật được thay bằng biểu tượng bảng phim/play SVG hai lớp, dùng màu vàng chanh. Logo có kích thước/điểm đặt cố định và bấm để về trang chủ. Thanh điều hướng trái dùng chung độ rộng 72/60/48 px theo màn hình, giữ nguyên giữa Trang chủ, Kịch bản, Tạo video và Dựng.

Kịch bản nằm trong vùng nội dung của Trang chủ, giữ thanh sản phẩm; tiêu đề, khoảng đệm và chiều cao header cùng chuẩn. Chỉ danh sách và phần sửa công thức cuộn riêng. Chọn sản phẩm hoặc Lưu trữ thoát đúng khỏi kho kịch bản. Chức năng kho chung, tìm/sửa/lưu/xóa công thức và ảnh chụp công thức trong phòng cũ không đổi.

Tạo video và Dựng giữ chung mốc bắt đầu vùng làm việc: thanh phòng 56 px + vùng công cụ 66 px. Phòng ảnh có hostNavigation bỏ header nhận diện lặp bên trong iframe. Editor trong host bỏ chữ SceneForge và điều hướng lặp, giữ ô tên bản dựng, trạng thái lưu, mở/lưu dự án, Bố cục và Xuất video; editor độc lập giữ header cũ.

Các iframe được giữ kích thước khi không được chọn, dùng visibility/inert/aria-hidden để ngăn tương tác và vẫn dừng phát. Khung workflow/editor được bù chiều cao thanh công cụ để không co về 0 hoặc đổi kích thước mỗi lần chuyển tab. Không ẩn rồi hiện lại iframe đích nếu đang được chọn. Dữ liệu, node, timeline và worker đang chạy không bị dựng lại bởi thay đổi khung.

Đã kiểm tra Chromium: cùng vị trí logo/rail; tọa độ tiêu đề Trang chủ và Kịch bản trùng; cuộn editor công thức không kéo tiêu đề; các nút điều hướng còn hoạt động. Ba vòng Tạo video/Dựng và qua Trang chủ/Kịch bản giữ cùng iframe, cùng chiều rộng/chiều cao, cùng mức zoom và dữ liệu cảnh. Vùng canvas ảnh và trình dựng thẳng mốc với vùng workflow. Màn 1536/1366/390 px không tràn tài liệu. Đây là kiểm tra bố cục và trạng thái trên Chromium, không phải cam kết tốc độ mọi máy.

Các kiểm tra thanh trên, hai hướng workflow/ảnh cũ, Gói 6 (5 video thật cục bộ, worker, công thức, thùng rác), Lưu trữ và thêm ảnh đều qua. Demo không gọi API/provider. Gói nguồn thiết kế và dữ liệu sản phẩm/phòng được giữ.
