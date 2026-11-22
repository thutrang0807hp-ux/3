# Kết nối Gemini bằng tiện ích

1. Giải nén SceneForge-Browser-Connect.zip vào một thư mục cố định.
2. Mở chrome://extensions hoặc edge://extensions. Bật Chế độ nhà phát triển → Tải tiện ích đã giải nén → chọn thư mục chứa manifest.json. Nếu đã có tiện ích SceneForge cùng ID, thay file trong thư mục cũ rồi bấm Tải lại ⟳.
3. Đăng nhập Gemini trên chính trình duyệt đó.
4. SceneForge → Cài đặt → Tài khoản → Gemini Chat → Kết nối bằng mã tiện ích → Tạo mã kết nối. Mặc định chỉ nối Gemini, giữ cấu hình Flow.
5. Bấm biểu tượng tiện ích, nhập mã 8 số và đúng cổng app hiển thị, bấm Kết nối. Về app đợi kiểm tra phiên rồi chọn tài khoản vừa nối.

App cũ: Đăng nhập trên web → Cách kết nối khác → Dùng tiện ích & mã kết nối. Bỏ chọn nối cả Gemini và Flow.

Bản tiện ích 1.6.9 được lấy nguyên mã từ gói nguồn .46 đã phát hành, giữ ID để tương thích kiểm tra Origin. Có cả chức năng Flow hiện có. Không chứa tài khoản/cookie cá nhân. Mã một lần hết hạn sau 3 phút. Đây là cách chuyển phiên vào app, chưa phải bộ tải ảnh trong trình duyệt và chưa xác minh khắc phục HTTP403 tài khoản thật.
