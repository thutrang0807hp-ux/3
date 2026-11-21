# SceneForge .135 — nhận phiên Gemini ở nền

Sửa điểm yếu của .134: tự nhận phiên chỉ chạy trong hộp thoại đăng nhập; đóng/thay hộp thoại hủy lượt đăng nhập. Nay bộ chạy nền theo dõi cửa sổ Chrome/Edge, khi đóng cửa sổ thì nhận và kiểm tra phiên. Quay về bảng tài khoản vẫn tiếp tục nhận. Tắt app sẽ dừng lượt đăng nhập chưa hoàn tất.

Bảng tài khoản Gemini hiển thị trạng thái chờ, kiểm tra, thành công hoặc thông báo lỗi. Lỗi giữ lượt nhận để bấm Thử nhận phiên lại, không tự lặp. Thành công chỉ ghi sau khi kiểm chứng phiên. Luồng này vẫn cần đóng cửa sổ trình duyệt đăng nhập để ghi phiên vào profile.

Đóng SceneForge và cửa sổ đăng nhập do app mở trước khi cập nhật. Sau đó Cài đặt → Tài khoản → Gemini Chat → Mở phiên hoặc Đăng nhập trên web. Đăng nhập xong vào được Gemini thì đóng cửa sổ đó. Có thể quay lại bảng tài khoản để xem tiến trình. Không xóa Data hoặc cookie.

Đã kiểm thử backend không có giao diện, chờ đóng cửa sổ, lưu đúng một lần, lỗi giữ lượt và thử lại; kiểm thử hộp thoại bằng Chromium, không hủy khi quay lại; kiểm tra cú pháp toàn bộ script, hồi quy Flow, nội dung nhúng của gói. Chưa chạy đăng nhập Google thật hoặc trình cài Windows. Ảnh người dùng chưa chứng minh đây là nguyên nhân duy nhất; thông báo lỗi mới giúp phân biệt chỗ kẹt còn lại.

Cộng dồn từ .62 trở lên, giữ cập nhật trước.
