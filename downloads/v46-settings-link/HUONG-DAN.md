# SceneForge v46.36 — tự tìm lượt video cần kiểm tra

1. Đóng SceneForge, chạy SceneForge-Update-20261102-v46.36-Auto-Tracking.exe, chọn thư mục có SceneForge.exe và install-settings.json. Yêu cầu v46.7 trở lên.
2. Mở lại đúng phòng và chọn đúng tài khoản đã tạo video. Không cần tìm mã hoặc chọn lại cảnh.
3. Trong node Veo, phần **Video đã gửi chưa nhận được kết quả** nằm phía trên chọn cảnh. Bấm **Tự kiểm tra video đã gửi và tải báo cáo**.
4. Gửi file SceneForge-theo-doi-video.json trong chat. Nhiều lượt unknown được gộp vào một file; dùng prompt gốc trong toàn bộ lịch sử Flow của phòng, kể cả schema cũ. Nếu thiếu prompt hoặc không mở được Flow, file ghi lỗi cùng dữ liệu gần nhất.

Không tạo lại video, không đổi unknown, không mở retry. Giữ đường upload .33 và nút tạo .34. Bản .36 bổ sung chẩn đoán và tự chọn lượt đúng; chưa sửa dứt điểm theo dõi hoặc khôi phục video trên Flow thật. Đã kiểm tra Chromium/ledger/API mô phỏng; chưa xác minh trên Flow thật hoặc chạy installer Windows.
