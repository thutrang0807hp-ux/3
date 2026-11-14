# SceneForge .122 — gỡ ảnh đang được Kho kịch bản giữ

Đóng SceneForge, chạy **SceneForge-Update-20261112-v46.122-Recipe-Image-Detach.exe**, chọn đúng thư mục app rồi mở lại. Bản gộp nhận từ .62 trở lên, gồm .119–.121.

Vào **Lưu trữ & Thùng rác → Xem tệp còn lại**. Nếu ảnh được Kho kịch bản giữ, bảng hiện tên các kịch bản liên quan và nút **Gỡ ảnh khỏi kịch bản và xóa nếu không còn nơi dùng…**.

Sau xác nhận:
- Chỉ gỡ các tham chiếu tới đúng ảnh được chọn trong các mục Kho kịch bản đã liệt kê, kể cả mục đang trong Thùng rác của Kho.
- Giữ nguyên tên, nội dung, lời, nhịp cảnh, dữ liệu khác và ảnh khác.
- Xóa tệp nếu không còn nơi nào khác cần giữ. Nếu còn dự án khác dùng, bản ghim hoặc tác vụ giữ ảnh, tệp vẫn được bảo vệ.
- Sao lưu cũ không tự đưa ảnh đã chủ động gỡ trở lại; các phần nội dung kịch bản vẫn có thể khôi phục. Thao tác được ghi nhận và nạp lại dữ liệu kho máy trước khi app tải lại, tránh bộ nhớ trình duyệt ghi ảnh cũ trở lại.

Đã kiểm bằng tệp/SQLite thật và API/Chromium: tên kịch bản đúng, xác nhận cũ bị từ chối khi dữ liệu đổi, ảnh đích được xóa, lời/nhịp và ảnh khác giữ nguyên, ảnh dùng chung ở dự án khác không bị xóa, sao lưu khôi phục không tạo tham chiếu ảnh mất, dữ liệu sau tải lại vẫn đúng. Bộ hồi quy .120/.121 và xóa/khôi phục cũ đều qua. Chưa chạy bộ cài Windows hoặc sửa trực tiếp tệp trên máy người dùng.
