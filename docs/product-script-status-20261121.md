# SceneForge .138 — thoát lượt viết kịch bản bị kẹt

Sửa AI viết bị chặn bởi submitted/unknown chỉ mở lại bảng cũ. Nay nút này đối soát trạng thái thực trong kho trước khi hiển thị. Endpoint chỉ đọc, kiểm tra store_id và dữ liệu khớp lượt đã lưu; không gọi AI, không tạo lượt mới. Trạng thái có xếp hàng/đang xử lý/hoàn tất/thất bại/không tìm thấy/chưa rõ. Khi đang xử lý bảng tự kiểm tra lại mỗi 2 giây. Hiển thị lúc bắt đầu gửi thay vì chờ im lặng. Lỗi khi nhận lại được cập nhật vào bảng, không giữ mãi câu lỗi cũ.

Thêm Viết theo thông tin hiện tại cho lượt chưa rõ. Kiểm tra lại trạng thái trước: nếu còn xử lý thì chặn gửi thêm; nếu hoàn tất thì nhận kết quả cũ; các trạng thái khác cần người dùng xác nhận bỏ chờ và viết lượt mới. Giữ bản ghi cũ trong lịch sử, dùng payload mới từ thông tin hiện tại. Không tìm thấy trong kho không đồng nghĩa chứng minh chưa dùng hạn mức.

Đóng app trước cập nhật. Trong node Kịch bản, mở lượt viết cũ → Kiểm tra trạng thái. Nếu không còn xử lý và muốn dùng dữ liệu đã sửa, bấm Viết theo thông tin hiện tại. Bản mới vẫn yêu cầu tài khoản Gemini đã kiểm chứng để AI viết được; không bỏ qua xác thực hoặc bịa kết quả.

Kiểm thử backend endpoint thiếu lượt/đang chạy/payload sai không gọi AI; Chromium kiểm thử lượt cũ không gửi thêm, chặn khởi động khi đang chạy, viết lượt mới lấy dữ kiện hiện tại sau xác nhận; hồi quy kết hợp hai nguồn, giữ lời gốc/mốc/clip cũ. Kiểm tra cú pháp toàn bộ workflow script và nội dung nhúng gói. Chưa thử Google thật hoặc trình cài Windows. Cộng dồn từ .62 trở lên.
