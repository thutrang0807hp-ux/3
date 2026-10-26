# Lưu trữ & Thùng rác — 27/10/2026

Một mục thanh bên, hai tab trong trang. Chung thanh dung lượng, tìm kiếm, lọc sản phẩm, lọc loại, sắp xếp và chọn nhiều. Giữ dữ liệu cũ và các quy trình kho máy, không chuyển file chỉ vì mở trang.

## Các hành vi thật
- Lưu trữ giữ tư liệu; Dọn cho nhẹ mở quy trình rà phạm vi sẵn có (bản không dùng hoặc chốt thành phẩm và bỏ tư liệu). Dự án đã thu gọn ghi rõ chỉ còn thành phẩm + kịch bản. Xóa ở Lưu trữ chuyển sang Thùng rác, không xóa file.
- Thùng rác hiển thị dự án/sản phẩm bị xóa mềm và các lượt dọn file đang chờ từ backend. Clip/ảnh của một lượt dọn được quản lý theo dự án/lượt, chưa giả thành từng dòng độc lập; chưa có thùng rác thống nhất cho từng kịch bản trong Kho.
- Khôi phục dự án/sản phẩm ghi IndexedDB một giao dịch rồi đồng bộ kho máy. Khôi phục sản phẩm không tự khôi phục video đã bị xóa riêng trước đó. Nếu sản phẩm gốc không còn, chặn và yêu cầu chọn lại sản phẩm; không tự tạo nơi chứa giả.
- Xóa hẳn dự án đi qua lifecycle plan, xác nhận phạm vi, rồi execute. Chọn xóa ngay hoặc chờ 7/30 ngày bằng hộp dọn đã có. Chỉ lượt đã xác nhận vào khu chờ mới có hạn xóa. Dự án vừa xóa mềm không bị tự xóa sau 30 ngày. Không thêm lịch tự dọn hoặc thay chính sách cũ.
- Lượt delete trong thời hạn có nút Khôi phục, gọi lifecycle/cancel và nạp lại snapshot. Lượt chờ có thể Xóa file chờ ngay, hỏi lại trước lifecycle/expedite. File chung, bản ghim, sao lưu và job chưa rõ được bảo vệ bởi backend.
- Chọn nhiều dự án mở bộ rà kế hoạch từng dự án đã có, không xóa trực tiếp từ danh sách. Dự án đang làm việc bị chặn khi khôi phục. Sản phẩm chỉ có khôi phục; xóa hẳn sản phẩm cùng mọi tài nguyên dùng chung chưa được bổ sung.
- Dung lượng thanh trên là byte vật lý từ endpoint storage-breakdown, không cộng các dòng dự án. Bốn nhóm: dự án/lưu trữ/thùng rác/sao lưu chung; bản xuất; model; cache. Không tách màu Lưu trữ/Thùng rác vì file có thể dùng chung. Chưa đo dùng thanh xám, không vẽ tỷ lệ giả.
- Dung lượng dòng là tư liệu logic trong app, có thể trùng hash với dự án khác; có dấu * và giải thích, không gọi đó là dung lượng thu hồi. Lượt dọn chưa có số byte xét dọn riêng thì hiện —. Số byte giải phóng thật chỉ báo sau backend thực hiện.
- Dọn tệp tạm chỉ xuất hiện khi có ZIP cache đủ điều kiện; có xác nhận và token kế hoạch. Nâng cao giữ lối vào công việc/đối soát, lượt dọn và sao lưu. Backend hiện trả tối đa 100 lượt dọn gần nhất; trang không đại diện toàn bộ lịch sử đã dọn.

## Kiểm thử
8 bài PASS: Chromium desktop/mobile + IndexedDB; server local + SQLite giữa hai profile trình duyệt; xóa vào khu chờ 7 ngày, reload, khôi phục từ khu chờ giữ nguyên byte file xuất; guard web không xóa file; lifecycle bảo vệ file chung, lease, sao lưu và phục hồi sau gián đoạn; Settings, Chi phí, Tài khoản và chuyển workflow.
Không gửi AI; chưa kiểm Windows hoặc dịch vụ online thật. scripts/app-shell/check_storage_hub.py và check_storage_hub_local.py là kiểm mới. storage-hub-checks.json chứa kết quả.

Code UI: scripts/app-shell/storage-hub.js, storage-hub.css. Dùng lại home-archive.js, archive-lifecycle.js, home-dashboard.js, storage-actions.js, library-runtime.js và backend storage_lifecycle.py; không tạo cơ chế xóa file song song.
