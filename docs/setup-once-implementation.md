# Thiết lập đầu tiên · chỉ mở một lần

Khung Thiết lập chỉ tự mở khi companion trên máy trả `connected: true`, dữ liệu trình duyệt còn mới (chưa có thư mục/phòng/phòng từng mở), chưa xem và chưa hoàn tất thiết lập. Không lấy `localhost` đơn thuần làm bằng chứng đã cài app: bản web tĩnh không có companion và `?demo=1` không mở wizard. Không gọi AI hoặc đăng nhập để xác định điều kiện này.

Lưu cờ `package5WelcomeSeen` vào kho prefs trước khi hiển thị. Đóng bằng X/Esc hoặc hoàn tất thì không tự bật lại khi reload/mở app. Nếu người dùng đã bắt đầu thao tác lúc khởi động, không thay menu đang mở bằng wizard; ghi nhận đã qua màn chào. Giữ cờ hoàn tất cũ `package5WelcomeDone`, thư mục và dữ liệu cũ. Cờ theo hồ sơ trình duyệt của app; xóa toàn bộ dữ liệu trình duyệt được coi là lần dùng mới.

Bỏ nút “Thiết lập ban đầu” khỏi Cài đặt; các trang Thư mục lưu, AI, Tài khoản, Động cơ và sản phẩm vẫn có lối riêng. API welcome cũ giữ để tương thích nhưng không mở lại sau khi đã xem, và không mở trên web/demo.

Thiết kế thu từ 1100 xuống tối đa 960 px; sidebar 285 px, nội dung co giãn. Rút gọn lời chào, bước đánh số cùng hàng với tên; header/body/footer tách rõ. Footer có padding 16×24 px, nút luôn bên trong khung. Nội dung cuộn trong chiều cao màn hình; mobile chuyển một cột. Không hỗ trợ chọn thư mục thì vô hiệu hóa nút và hướng dẫn Chrome/Edge, không để một nút bấm không chạy.

Kiểm tra: `python scripts/app-shell/check_setup_once.py` kiểm static preview/demo không hiện; fixture companion-connected mở đúng một lần; đóng/reload/gọi lại không hiện; đủ 5 bước và lưu hoàn tất; Cài đặt không còn nút mở lại; nút/footer trong dialog ở 1366×768 và 390×740. Fixture chỉ giả metadata loopback để kiểm vòng đời, không chứng nhận bộ cài Windows hoặc kết nối nhà cung cấp. `python scripts/app-shell/check_topbar.py` giữ kiểm thanh hai dòng và điều hướng.
