# SceneForge .134 — Gemini tự nhận phiên

Đăng nhập Gemini trên cửa sổ do app mở → đóng cửa sổ đó → SceneForge tự kiểm tra và lưu phiên. Không cần bấm Lưu phiên. Giữ hộp thoại đăng nhập trong app mở cho đến khi kiểm tra xong.

App chỉ theo dõi trạng thái đóng của cửa sổ, không đọc cookie khi người dùng đang đăng nhập. Nếu xác minh thất bại, không báo thành công, không tự lặp; giữ lượt đăng nhập và hiện nút Thử nhận phiên lại. Rời hộp thoại sẽ dừng lượt nhận phiên. Các dịch vụ khác giữ cách lưu hiện có.

Đóng SceneForge trước khi chạy cập nhật. Giữ Data, cookie, tài khoản và cập nhật trước; nhận từ .62 trở lên.

Đã kiểm thử trạng thái đóng, tự nhận đúng một lần, lỗi xác minh/thử lại, rời hộp thoại, giao diện Chromium và hồi quy Flow. Đã kiểm tra nội dung nhúng của gói. Chưa kiểm chứng Google thật hoặc trình cài Windows.

SHA-256: c1d892b60c751ee3d9ea959b2493d28b30f0e908c39fddc7cd073b23ea9c0fa5
