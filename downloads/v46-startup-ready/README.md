# SceneForge v46.66 — chờ kho dữ liệu trước khi mở tab

Đóng SceneForge, chạy `SceneForge-Update-20261104-v46.66-Startup-Ready.exe` trên bản .65, mở lại. Khoảng 4 MB; không phải bộ cài đầy đủ. Giữ nguyên thư mục Data, không cần xóa cache hoặc tạo kho mới.

Tái hiện .65: API kiểm tra kho local bị chậm; bấm Kịch bản trước khi init gán db → recipeLibrary gọi io('prefs') → undefined.transaction. Bảng có thể hiện 0 khi chưa tải dữ liệu; riêng ảnh lỗi này không chứng minh dữ liệu mất.

- io chờ Promise mở DB, chỉ được tiếp tục sau khi bước chuẩn bị kho và openDB hoàn tất.
- Click điều hướng lúc khởi động được giữ lại (lựa chọn sau cùng); thực hiện khi app-ready. Hiện “Đang mở dữ liệu…”.
- Nếu khởi động thật sự thất bại, hiển thị/truyền lỗi gốc; không trả giả danh sách rỗng, không reset database.
- Promise đọc Kịch bản bị lỗi được bỏ để lần đọc sau có thể thử lại; không giữ Promise đã reject mãi.

Kiểm thử khởi động trọn vẹn, không gán trước db/products/rooms: DB mới, DB cũ có sản phẩm/phòng/media, lỗi mở DB, API kho managed; bấm Kịch bản rồi Trang chủ trước ready; đọc sớm phải chờ; dữ liệu cũ và nội dung media giữ nguyên sau reload; lỗi đọc Kịch bản nhất thời thử lại được. Bộ test điều hướng cũ đã đổi sang secure origin và chờ readiness thật trước tạo fixture. Kiểm trước đây chưa bao phủ bấm tab trong khi kho đang mở.

Gói chỉ thay index.html/studio.html, giữ toàn bộ tối ưu .65, workflow/engine/runtime/tài khoản. Chưa chạy updater Windows hoặc xác minh kho dữ liệu thực tế trên máy người dùng. Nếu sau khi mở dữ liệu xong vẫn thiếu phòng, cần kiểm tra đúng kho/đường dẫn, không tự khẳng định đã phục hồi.

SHA256: `e0a9f3842106bff8b1d25ea15226ffb353d3111711e04654d4399bdea7680a34`
