# SceneForge .140 — dừng và tạo lại toàn bộ ảnh khung

Node Ảnh khung có hai nút cố định: Dừng hoạt động và Tạo lại toàn bộ N khung. Trước đây tạo lại loại running/unknown nên cảnh kẹt bị bỏ qua; dừng chỉ đặt cờ, không thoát được await mạng treo.

Dừng hủy việc chờ ở pipeline app, không gửi bước tiếp theo. Không tuyên bố đã hủy tác vụ phía Gemini: yêu cầu đã gửi có thể vẫn chạy và dùng hạn mức. Phản hồi muộn của lượt cũ bị tách khỏi pipeline hiện tại. Không đóng/xóa tài khoản, không xóa phiên bản ảnh cũ.

Tạo lại toàn bộ tự dừng pipeline đang chạy, chờ lượt cũ trong app kết thúc rồi tạo lượt mới cho TẤT CẢ cảnh, gồm cảnh unknown/đã duyệt. Không cần bấm dừng trước. Chống bấm lặp tạo hai pipeline đồng thời. Kiểm tra tài khoản trước khi thay bản ghi hiện hành. Prompt/job ảnh cũ được lưu lịch sử, media job cũ đánh dấu abandoned kèm previousState và ghi chú chưa chắc đã hủy phía dịch vụ. Giữ prompt sửa tay; đầu vào đã thay đổi vẫn cần quyết định giữ/viết lại bản sửa tay theo luồng sẵn có.

Mỗi cảnh được chuẩn bị prompt rồi tạo ảnh theo sản phẩm và kịch bản hiện tại. Lỗi một cảnh được ghi rõ và tiếp tục cảnh khác trong lượt tạo lại toàn node; không gắn trạng thái thành công cho lượt có lỗi. Lỗi mạng, đăng nhập hoặc quota vẫn có thể khiến tạo ảnh thất bại; nút mới bảo đảm bắt đầu luồng mới trong app, không bảo đảm dịch vụ sinh ảnh thành công.

Đóng SceneForge trước cập nhật. Mở node Ảnh khung → Tạo lại toàn bộ. Theo dõi tiến trình từng cảnh; bấm Dừng hoạt động khi cần. Tạo lại có thể dùng thêm hạn mức vì lượt cũ có thể còn xử lý bên Gemini.

Đã kiểm thử workflow thật với API giả lập/Chromium: dừng khi POST treo, bao gồm cảnh unknown, gửi đủ prompt và ảnh cho hai cảnh, bấm tạo lại lần nữa có ID mới, bỏ phản hồi muộn, giữ ảnh/lịch sử, một cảnh lỗi không chặn cảnh sau. Hồi quy prompt sản phẩm và lớp prompt; kiểm tra cú pháp toàn bộ script và nội dung nhúng gói. Chưa tạo ảnh Gemini thật hoặc chạy trình cài Windows. Cộng dồn từ .62 trở lên.
