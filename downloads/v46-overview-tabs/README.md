# SceneForge v46.65 — Trang chủ / Kịch bản / Hàng loạt

Đóng app, chạy `SceneForge-Update-20261104-v46.65-Overview-Tabs.exe` trên bản .64 trở lên, mở lại. Khoảng 4 MB; không phải bộ cài đầy đủ.

- Kịch bản/Hàng loạt đi thẳng vào tab, bỏ lượt dựng Trang chủ bị ẩn.
- Không flush lại workflow đang bị ẩn khi chuyển giữa các trang overview còn giữ nguyên iframe; rời workspace vẫn lưu và kiểm tra đang dò cảnh/lỗi lưu.
- Hàng loạt chỉ dựng form lần đầu; giữ prompt, tỉ lệ và lựa chọn chưa gửi khi quay lại. Danh sách sản phẩm vẫn cập nhật khi có thay đổi.
- Bỏ parse/patch markup không đổi; theo dõi thay đổi DOM để không giữ nội dung lỗi thời. Dùng lại bộ định dạng ngày trên thẻ Trang chủ.
- Bố trí thẻ ngoài vùng nhìn được trì hoãn bằng content-visibility; vẫn giữ đủ phòng/công việc, không xóa hoặc ẩn dữ liệu.

Đo Chromium fixture 200 phòng: .64 Trang chủ 136–261 ms, Kịch bản 153–193 ms, Hàng loạt 214–286 ms; .65 lượt quay lại Trang chủ 32–39 ms, Kịch bản 12–32 ms, Hàng loạt 3–7 ms. Mở lạnh lần đầu có thể cao hơn; đây không phải đo trên Windows người dùng và không cam kết hết mọi lag. Khi dữ liệu thật thay đổi vẫn cần cập nhật DOM.

Kiểm thử: check_overview_tab_performance.py (không render bảng ẩn, giữ draft/form/tỉ lệ batch, guard scanning/lưu lỗi, cập nhật tên phòng, cache invalidation với DOM mutation tức thì và sau microtask); check_tab_navigation.py; check_navigation_loading.py. Chỉ thay index.html và studio.html; giữ engine/runtime/workflow .64 và mọi tài khoản. EXE đã kiểm hash và từng HTML nhúng; chưa chạy updater trên Windows/Flow thật.

SHA256: `add0dc7a4424983e5ee7516f3762f5346ed6b4ffabe1f84d9e38e630398d6f71`
