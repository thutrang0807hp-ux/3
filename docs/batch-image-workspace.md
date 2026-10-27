# Tạo ảnh hàng loạt và dọn im lặng — 27/10/2026

## Chức năng
- Tab chỉ tạo ảnh: ẩn đầu ra Video, giữ select nội bộ để engine cũ không gãy; bốn nút tỉ lệ 9:16 / 1:1 / 4:5 / 16:9. Bổ sung 4:5 vào loader, mô phỏng PNG và hai validator backend tạo ảnh. Nguồn/model/tài khoản giữ cơ chế đã có.
- Mỗi lượt riêng, chọn lại lượt cũ, lượt mới không trộn ảnh tải. Bảng lượt hiện paused/running/waiting và số ảnh cần người xử lý; chạy tiếp ảnh chờ dùng batchStart/batchConfirmReal cũ. Giới hạn đồng thời lấy cài đặt thật (không hứa một tài khoản luôn đạt mức đó). Không tự đổi nguồn.
- Phân biệt chờ/chạy, quota, từ chối nội dung, xác minh/đăng nhập, lỗi mạng xác định, lỗi khác, chưa rõ kết quả và cờ người dùng. Lý do nguồn dựa mã backend, không suy một lỗi mạng là chưa gửi. Không tự thử lại hai lần; không bịa giờ mở quota. Quota có nút Mở nguồn, không tự gửi lại.
- Có checkbox cho mọi ô, chọn tất cả/chọn nhanh Cần bạn/Đang chờ/Lỗi. Thanh nổi tính riêng số tải được và số đủ điều kiện tạo lại. Ảnh bị đánh dấu vẫn hiển thị nhưng bị loại khỏi tải ảnh đạt. Bỏ nút Dùng làm ảnh khung khỏi thanh nổi; chức năng đưa ảnh vào workflow còn trong xem chi tiết.
- Tạo lại mở bảng rà prompt và số yêu cầu phù hợp, bỏ qua mục đang chạy/quota/chưa rõ. Prompt bị từ chối phải sửa. Bản mới giữ slot, bản cũ được giữ đến dọn; request id, token và kết quả không bị copy sang job mới. Xếp lại không tự gửi, vẫn cần xác nhận tài khoản/nguồn. Thu hồi kết quả không tạo thêm yêu cầu.
- Xóa mặc định vào Thùng rác, ẩn cả slot để không lộ lại bản cũ. Prompt và ảnh còn giữ, khôi phục từ tab Lưu trữ & Thùng rác, có bộ lọc Ảnh hàng loạt. Khôi phục không tự chạy job chờ. Ảnh bỏ giữ 30 ngày; xét dọn khi mở tab tạo ảnh hoặc thư viện, chỉ lúc rảnh và không có phòng mở/thay đổi chưa lưu. File ghim, dùng chung, còn được job khác tham chiếu được bảo vệ; đến hạn nhưng chưa đủ điều kiện vẫn chờ.
- Xóa hẳn hỏi lại một lần. Gỡ file riêng bằng transaction prefs/files; giữ tài nguyên có tham chiếu từ dự án khác, ảnh ghim và ảnh đã bàn giao. Chặn job đang chạy/chưa rõ và ảnh còn được ô khác dùng. Receipt/request id vẫn giữ trong tombstone, không xóa sổ gửi provider. URL Blob đã xóa được thu hồi. Không báo số GB chưa xác minh; backup/kho máy còn áp dụng chính sách bảo vệ riêng, xóa logic không đồng nghĩa ổ đĩa giải phóng ngay.

## Bảng lỗi
- Đóng & dọn lượt không bị kẹt chỉ vì nhớ phòng trước đó: nếu phòng đang ẩn ở trang chủ, lưu/đóng đúng cách, rồi quay lại tab ảnh trước khi rà dọn. Việc đang chạy/chưa rõ vẫn chặn.
- Đưa dự án/ảnh vào Thùng rác, xóa ảnh/xóa dự án, dọn tệp tạm hoặc đóng lượt thành công: clearHomeError ẩn và xóa nội dung bảng cũ, không toast thành công và không thêm notification. Đóng xác nhận bằng Hủy không được coi là đã xóa thành công. Có lỗi hoặc dọn không hoàn tất thì vẫn hiển thị lý do; bảng lỗi có nút ×. Báo cáo dọn sau reload chỉ hiện nếu thực sự còn lỗi.
- Nhật ký vận hành/receipt của engine không bị xóa; yêu cầu không tạo thông báo thành công không có nghĩa xóa lịch sử an toàn của công việc.

## Kiểm tra và giới hạn
Xem batch-image-workspace-checks.json. Chromium thật: thao tác sáu loại ô, retry đúng tập con, sửa prompt từ chối, chặn lượt chưa rõ, Blob riêng xóa thật/Blob dùng chung còn, Thùng rác + khôi phục + hạn 30 ngày + reload, đóng phòng ẩn và dọn im lặng, mobile không tràn. Kho SQLite thật: PNG và batch metadata lưu qua profile mới, ảnh bỏ/khôi phục cũng lưu qua profile mới. Các nguồn Flow/Grok/ChatGPT/Meta kiểm bằng phản hồi fixture và request bị chặn trong bài kiểm: đúng nguồn/token, đổi tài khoản chặn gửi, ảnh tham chiếu giữ nguyên 1400px, 4:5 được chuyển đúng, recovery không replay. Hồi quy storage/notification/hai workspace đạt. Chưa chứng nhận tạo ảnh online hoặc Windows.

## Dựng và xem thử
patch_batch_image_workspace.py chèn CSS/JS có marker vào bốn bundle và được build.py gọi sau workspace shell. Những sửa nhỏ trong module nguồn cũ đã đồng bộ vào bundle khôi phục. ZIP runtime dựng bằng thay đúng entry từ bản d8399ea, giữ entry khác; thêm source/test/tài liệu, không có vault/cookie. package_workspace_preview.py hỗ trợ SCENEFORGE_PREVIEW_MODE=batch: một HTML nhúng bundle thật và dữ liệu riêng; sáu prompt mẫu, chạy PNG bằng canvas, không gọi AI.
