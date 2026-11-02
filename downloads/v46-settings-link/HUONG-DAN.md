# SceneForge v46.39 — history và xác nhận giữ video cũ

1. Đóng SceneForge, chạy SceneForge-Update-20261102-v46.39-History-Review.exe, chọn thư mục có SceneForge.exe và install-settings.json. Yêu cầu v46.7 trở lên.
2. Mở đúng phòng và tài khoản đã gửi video. Không cần chọn mã.
3. **Kiểm tra video cũ**: app mở thumbnail phù hợp, kiểm tra trang chi tiết trong cùng dự án bằng guard riêng, đọc flow-editor-history-step-video và thử Expand prompt. Tải báo cáo JSON để gửi trong chat. Không dùng toàn bộ text history để kết luận prompt khớp.
4. **Tôi đã giữ video cũ · cho phép lượt mới**: chỉ bấm khi bạn đã kiểm tra và giữ các video được xác nhận trên Flow. Hộp thoại nêu rõ số lượt và app chưa nhận video cũ về. Xác nhận được ghi vào metadata và giữ qua lần mở lại app.
5. Sau xác nhận, chuẩn bị ảnh + prompt mới rồi bấm tạo video mới. App không gửi lại mã cũ, không đánh dấu lượt cũ là đã nhận video.

Unknown quá 3 phút chỉ có nhãn Cần kiểm tra video cũ; không tự mở khóa. Prompt khớp không đủ chứng minh video thuộc chính lượt cũ; chưa tự tải hoặc đánh dấu hoàn tất. Giữ đường upload .33 đã chạy được và luồng gửi một lần .34.

Đã kiểm tra Chromium/ledger với dữ liệu mô phỏng: cùng dự án/trang con, Expand prompt, bảo toàn unknown/result, xác nhận đúng phòng/tài khoản, hủy không mở khóa, lần mở lại giữ xác nhận và lượt mới không tái dùng ID cũ. Chưa xác minh trên Flow thật hoặc chạy installer Windows.
