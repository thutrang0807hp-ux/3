# Trang chủ Video — 27/10/2026

Triển khai theo ảnh tham khảo ba cách xem. Cùng một tập phòng/video, không tạo bản sao dự án hoặc gọi AI khi đổi cách xem.

- **Bảng:** thẻ nhỏ đồng đều, ảnh bên trái, tên/loại/các cảnh/việc tiếp theo bên phải. Cột có nhiều video rộng hơn; khi đủ chỗ, thẻ chạy hai cột con. Cột trống thu hẹp, cuộn trong cột; không dùng một thẻ rất lớn rồi các thẻ nhỏ.
- **Lưới:** bìa dọc 9:16, chữ bìa từ hook/tên đang có, nhãn trạng thái màu, tên và việc tiếp theo dưới ảnh. Không tạo nội dung bán hàng mới từ giao diện.
- **Danh sách:** một dòng/video, chọn nhiều, sắp tên/trạng thái/việc tiếp theo/credit/cập nhật; nút Mở, menu, Xóa ngay cuối dòng. Credit chỉ từ log có `cost_unit=credit`; dấu — là chưa có số liệu xác minh. Nhật ký đọc khi mở Chi phí & theo dõi, không tự tạo ước tính.
- Chip lọc trạng thái cho cùng dữ liệu. Lọc cách làm Video mẫu/Từ ảnh và tìm kiếm vẫn dùng được. Chọn nhiều giữ qua cách xem, bỏ chọn khi đổi phạm vi sản phẩm/tìm kiếm hoặc bộ lọc trạng thái, tránh thao tác nhầm video ẩn.
- Di chuột/focus hiện ô chọn và nút menu/xóa trên thẻ; màn hình nhỏ hiện sẵn. Thanh thao tác dưới danh sách: chuyển sản phẩm, lưu trữ, rà dọn, đưa vào Thùng rác.
- **Xóa ở trang chủ là đưa vào Thùng rác**, có xác nhận và khôi phục. Không xóa file nguồn, clip, kịch bản, bản dựng hoặc file xuất. Chưa có lịch tự xóa Thùng rác mới. Xóa hẳn vẫn qua quy trình dọn dữ liệu hiện có, sau khi khôi phục dự án nếu đang trong Thùng rác.
- Di chuyển/lưu trữ/xóa nhiều video cập nhật metadata trong một transaction IndexedDB; có rà lại tác vụ trước khi xác nhận. Giữ refs riêng và thư mục gốc khi chuyển sản phẩm. Chặn khi job đang chạy/chờ/chưa rõ hoặc kho máy chưa sẵn sàng.
- **Dọn cho nhẹ** dùng trình rà kế hoạch hiện có. Với nhiều video, mở danh sách để rà từng dự án; không âm thầm dọn toàn bộ chỉ bằng một nút. Không thay đổi chính sách lưu trữ hoặc lịch đã cài.
- Bỏ tab Chi phí trong hàng tab sản phẩm; thêm **Chi phí & theo dõi** ở cột trái. Giữ Lưu trữ và thêm Thùng rác Video. Trên điện thoại có menu Sản phẩm & thư viện, gồm chuyển sản phẩm, tạo sản phẩm, chi phí, lưu trữ và thùng rác.

## File chính

`scripts/app-shell/home-dashboard.js`, `.css` — UI và thao tác metadata.
`package4.js` — gọi renderer mới thay nhánh Bảng/Danh sách cũ.
`package6.js` — khôi phục sản phẩm giữ nguyên các video đã được đưa vào Thùng rác riêng trước đó.
`scripts/demo-web/build.py` — nạp module/CSS cuối shell. Không thay thứ tự/logic các engine AI.

## Kiểm chứng

Xem `home-dashboard-checks.json`. Chromium thật, IndexedDB/Blob thật, SQLite qua backend local thật. Có kiểm chọn nhiều, hủy xác nhận, ngăn cập nhật một phần khi nhóm có job đang chạy, lưu/khôi phục với phiên trình duyệt mới, giữ file xuất, chuyển sản phẩm giữ refs/thư mục, tương thích Lưu trữ, giữ DOM ảnh/focus/cuộn, hình dọc và nút trên mobile. Không gọi nhà cung cấp AI.

Bài kiểm Archive cũ bấm nút sidebar trên điện thoại; test đã đổi sang menu mobile mới. Có log lỗi ban đầu và log kiểm lại; không gọi đó là lỗi engine/lưu dữ liệu. Không chứng nhận Windows hay tài khoản AI thật vì thay đổi này chỉ ở trang chủ.
