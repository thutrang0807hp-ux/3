# Chi phí & Cài đặt — 27/10/2026

## Phạm vi
- Bỏ tab Bộ cảnh ở trang chủ sản phẩm. Giữ sceneBank và file cũ; không xóa node Bộ cảnh video trong dự án.
- Chi phí & theo dõi là trang riêng ở cột trái. Lọc 7 ngày / 30 ngày / tháng, sản phẩm, nguồn và kết quả; biểu đồ ngày hoặc bảng, xếp hạng sản phẩm/video, lần tạo lại rõ nguồn gốc, lỗi có mã, lịch sử phân trang và CSV.
- Chỉ cộng chi phí đã ghi nhận, giữ riêng credit/VND/USD. Không biết phí hoặc số dư thì ghi chưa xác minh; không suy phí từ số job hoặc giá niêm yết. Chỉ nhãn tạo lại rõ ràng mới được phân loại tạo lại, không suy nguyên nhân chất lượng từ việc gen nhiều lần. Lịch sử tối đa 20.000 dòng có cảnh báo cắt ngắn.
- Demo dùng số minh họa được đánh dấu, không ghi vào tài khoản thật. Luồng thật đọc SQLite/library, không gọi nhà cung cấp để đo chi phí.
- Cài đặt mở Tổng quan; chấm màu thể hiện trạng thái, nguồn Gemini Chat và API riêng biệt, cài đặt ít dùng nằm trong Nâng cao. Bỏ banner xem thử lặp toàn trang, giữ nhãn nhỏ.
- Kiểm tra & lưu API key chỉ thay key khi truy vấn danh sách model thành công. Key/model/kết quả kiểm lưu một giao dịch; phát hiện key bị đổi đồng thời. Key sai giữ cấu hình cũ. Không tạo ảnh/video trong bước kiểm.
- Thư mục lưu đo byte vật lý theo bốn nhóm, chống đếm trùng hard link, bỏ symlink và giới hạn thời gian/số file; có nhãn chưa đầy đủ nếu dừng sớm. Quét thư viện, thư mục đầu ra và hai vị trí model đã biết; không đại diện toàn ổ đĩa. Ngưỡng trống dùng đúng admission minimum_free_mb; không tự đổi mặc định.
- Dọn cache/dự án dùng lại quy trình xem trước/xác nhận. Không bật tự dọn mới. Nút engine mở hướng dẫn/chi tiết thật, không giả có API tự cài hoặc khởi động lại.

## Kiểm tra
Backend HTTP/SQLite thật, Playwright Chromium desktop/mobile và vault mã hóa thật. Kiểm candidate key dùng fixture truy vấn model, không dùng key/provider online. Đã kiểm key sai giữ key cũ, CSV an toàn công thức, phí chưa rõ không thành 0, không lộ key/cookie/prompt, đo file chỉ đọc, hủy dọn giữ file, xuất thư viện không kèm vault và bỏ tab vẫn giữ 8 clip cũ.
Kết quả từng bài: monitor-settings-checks.json. Không có bằng chứng tạo thật bằng tài khoản online hoặc chạy Windows. Không bổ sung TTL 24 giờ cho lô Batch trong thay đổi này.

## Code
- scripts/app-shell/cost-monitor.js; settings-redesign.js; monitor-settings.css
- local_engine/monitoring.py; ai_providers.py (verify-save); vault.py (giao dịch secrets); library_api.py (mở thư mục đang cấu hình)
- batch-studio.js ghi regeneratedFrom cho thao tác tạo lại mới; không đổi gửi job.
