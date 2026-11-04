# SceneForge v46.63 — chuyển tab nhẹ hơn

Đóng SceneForge, chạy `SceneForge-Update-20261104-v46.63-Faster-Tabs.exe`, chọn bản đã cài .62 trở lên, rồi mở lại. Đây là updater khoảng 4 MB, không phải bộ cài đầy đủ.

- Chuyển giữa Tạo video và Dựng chỉ cập nhật thanh điều hướng; không dựng lại danh sách tất cả phòng đang bị ẩn.
- Kiểm tra trạng thái dò cảnh bằng cờ nhỏ, không sao chép toàn bộ ảnh/lịch sử dự án chỉ để về Trang chủ.
- Giữ nguyên iframe của phòng, lưu trước khi về Trang chủ, và chặn rời phòng khi đang dò cảnh/xuất hoặc lưu thất bại.
- Gói chỉ thay index.html, studio.html, workflow.html, photos.html. Engine, runtime, tài khoản, dữ liệu và cơ chế gửi/nhận video giữ nguyên.

Đo Chromium cục bộ với 200 phòng, API iframe giả lập và dự án 60 cảnh chứa 12 MB chuỗi ảnh: 8 lượt chuyển Tạo video/Dựng từ 93–133 ms xuống khoảng 3–5 ms. Đây là thời gian xử lý navigation trong fixture, không bao gồm tải tab lần đầu và không phải cam kết hiệu năng Windows.

Kiểm thử: check_tab_navigation.py (giữ iframe, không render bảng ẩn/clone toàn bộ state, guard dò cảnh/xuất/lưu lỗi, tương thích API cũ); check_veo_redesign_ui.py; 3 check JavaScript cấu hình/tạo/đối soát. Kiểm tệp trong EXE byte-for-byte với nguồn, hash và launcher không đổi. Chưa chạy updater trên Windows hoặc Flow thật.

SHA256: `8c20d9b7d5d52e3bf7ca6988630310d041c9a3660e894f8f1b4a04a02537f817`
