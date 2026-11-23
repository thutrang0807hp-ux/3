# Gemini qua trình duyệt — SceneForge .161 + tiện ích 1.7.0

1. Đóng SceneForge, chạy cập nhật .161 vào đúng thư mục app đang dùng, mở lại.
2. Giải nén ZIP tiện ích mới đè vào thư mục tiện ích SceneForge cũ. Vào chrome://extensions hoặc edge://extensions → Tải lại ⟳. Chấp nhận quyền mới nếu trình duyệt hỏi. Nếu chưa cài, bật Chế độ nhà phát triển → Tải tiện ích đã giải nén → chọn thư mục chứa manifest.json.
3. Mở Gemini Chat trên Chrome/Edge đã đăng nhập, giữ tab đó mở.
4. App → Cài đặt → Tài khoản → Gemini Chat → Kết nối bằng mã tiện ích → Tạo mã. Chọn tab Gemini, bấm biểu tượng tiện ích, nhập mã và đúng cổng app rồi Kết nối. App tự chọn kết nối trình duyệt mới sau khi đọc được ô chat. Không cần cài Gemini SDK hoặc chuyển cookie cho kết nối này.
5. Dùng node Ảnh khung như trước. SceneForge chuẩn bị prompt, ảnh nguồn và ảnh tham khảo; tiện ích chỉ gửi lên Gemini và lấy ảnh về đúng cảnh. AI tối ưu prompt vẫn tùy chọn.

Cảnh còn kẹt lượt SDK cũ: mở cảnh → Chỉnh thêm → Bỏ chờ lượt cũ và tạo mới. Đọc xác nhận vì lượt mới có thể dùng thêm hạn mức. Lượt cũ và ảnh cũ vẫn được giữ; không tự thay thế hoặc gửi lại lượt cũ. Kết nối trình duyệt mới không thể tự lấy lại ảnh của một hội thoại SDK cũ chưa được mở trong tab.

Không đổi nick trên tab kết nối; nếu đổi nick hoặc đóng trình duyệt, kết nối lại rõ ràng. Mỗi lượt mới mở tab nền riêng; tab thành công được đóng sau khi app nhận kết quả. Tab lỗi được giữ để kiểm tra/nhận lại. Không đóng tab đang tạo nếu muốn nhận lại kết quả.

Nguồn tham khảo cơ chế: https://github.com/thutrang0807hp-ux/test-gemoni-chat — tiện ích 0.2.2. Chỉ tích hợp cơ chế kết nối/gửi/nhận, không thay node, quy tắc prompt hay quy trình duyệt SceneForge. Không có model hoặc tài khoản cá nhân trong gói tải.

Đã kiểm thử broker, worker tiện ích và DOM giả lập; ảnh PNG thật được lưu bằng luồng job hiện có. Chưa chạy Google thật/Windows thật của bạn. Cơ chế thao tác DOM phụ thuộc giao diện Gemini hiện hành và quyền tạo ảnh của tài khoản. Không tự nâng chất lượng ảnh lên 4K.
