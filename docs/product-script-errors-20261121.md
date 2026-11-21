# SceneForge .137 — trạng thái viết lời sản phẩm

Tách lỗi kiểm tra trước gửi Gemini: chưa có tài khoản đã kiểm chứng/được chọn, tệp vượt 24 MB, hàng chờ đủ 30 việc. Các kiểm tra này nằm trước claim và gửi AI. Thông báo cũ gộp ba nguyên nhân và khiến người dùng không biết đã viết chưa.

Node viết theo sản phẩm nhận biên nhận chưa gửi từ backend khi request_id và store_id khớp thì ghi rejected, hiển thị Chưa gửi AI · chưa viết lại, bỏ nút nhận lại và cho viết lượt mới sau khi xử lý nguyên nhân. Lỗi mạng hoặc biên nhận không khớp vẫn giữ chưa rõ, không tự gửi lại. Lượt cũ chưa rõ không tự bị đổi thành chưa gửi chỉ dựa vào câu báo lỗi.

Hai nguồn vẫn là reference_lines/reference_scenes cung cấp cấu trúc mẫu và product cung cấp dữ kiện sản phẩm mới. Lời gốc, bản dịch, thời gian giữ nguyên. Kết quả nhận thành công cần rà và bấm Áp dụng vào cột Lời mới.

Đóng app trước cập nhật. Nếu bản mới báo chưa có tài khoản: Cài đặt → Tài khoản → Gemini Chat → nhận/kiểm tra phiên → chọn Dùng. Sửa lỗi báo trạng thái không tự sửa được việc Google/SDK từ chối phiên.

Đã kiểm thử tách lỗi trước gửi, payload hai nguồn, kết quả/mốc/ID, biên nhận chưa gửi và nút viết lại bằng Chromium, phục hồi chỉ đọc và giữ lời gốc. Kiểm tra nội dung nhúng gói; chưa chạy Google thật hoặc trình cài Windows. Cộng dồn từ .62 trở lên, giữ các cập nhật trước.
