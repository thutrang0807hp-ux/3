# SceneForge .132 — tách đăng nhập Gemini khỏi bước đọc phiên

Đóng SceneForge và các cửa sổ đăng nhập Gemini cũ do app mở, chạy **SceneForge-Update-20261121-v46.132-Manual-Google-Login.exe**, chọn đúng thư mục ứng dụng, rồi mở lại. Bản gộp nhận từ .62 trở lên, giữ các cập nhật đến .131. Không cần đóng Chrome cá nhân hoặc xóa Data.

Trong **Cài đặt → Tài khoản → Gemini Chat → Đăng nhập trên web**:

1. Đăng nhập và hoàn tất xác minh trực tiếp trên cửa sổ Chrome/Edge vừa mở.
2. Khi đã vào được Gemini, **đóng cửa sổ đăng nhập đó** để trình duyệt ghi phiên vào profile riêng.
3. Quay lại SceneForge, bấm **Lưu phiên**. Nếu trình duyệt đang đóng, đợi vài giây rồi bấm lại cùng nút.

Trong lúc nhập tài khoản, app không mở CDP/Playwright, không chèn cấu hình thiết bị tùy chỉnh hoặc cookie từ bản lưu. Sau bước đóng và Lưu phiên, app mới mở cùng profile ở trang trống để đọc phiên, sau đó dùng bộ kiểm tra phiên Gemini hiện có. Một cửa sổ trống có thể xuất hiện trong bước đọc; không nhập mật khẩu vào đó. Profile, tài khoản và cấu hình đã lưu không bị xóa. Những tích hợp khác giữ luồng hiện có.

Nếu profile còn cửa sổ điều khiển từ lượt trước, app yêu cầu đóng cửa sổ đăng nhập đó thay vì mở nhầm vào phiên cũ. Chỉ đóng cửa sổ do SceneForge mở, không cần đóng các cửa sổ cá nhân.

Lịch sử cho thấy các thay đổi .125–.131 không sửa các mô-đun đăng nhập Gemini. Việc từng đăng nhập được không xác định được nguyên nhân Google từ chối hiện tại. Bản này loại các can thiệp của app trong pha nhập tài khoản; không bảo đảm Google luôn chấp nhận phiên hoặc xác minh SDK thành công.

Đã kiểm launch arguments, thứ tự đăng nhập/đóng/đọc, không nạp cookie trước, giữ profile và lease, chặn cửa sổ điều khiển cũ, cùng hộp Cài đặt thật trong Chromium với API mô phỏng. Chưa thử Google thật hoặc chạy bộ cài/đóng cửa sổ trên Windows. Không có mật khẩu/cookie người dùng trong gói hoặc kiểm thử.
