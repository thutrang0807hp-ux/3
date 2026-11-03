# SceneForge v46.61 — node Veo phản hồi nhanh, tạo toàn bộ clip còn thiếu

Cần cài .60 trước. Đóng SceneForge, chạy `SceneForge-Update-20261104-v46.61-Responsive-Veo-Node.exe`, mở lại. Đây là bản vá giao diện khoảng 4 MB; giữ nguyên CLI gốc, runtime và profile của .60, không cần tải lại gói 88 MB.

- Bỏ phần nguồn/cấu hình và nút Cấu hình Flow ở chân node. Chỉ giữ một bảng cấu hình trên thanh workflow.
- Nút Tạo toàn bộ N clip còn thiếu lấy toàn bộ node, kể cả clip bị bộ lọc Cần xem ẩn. Tự viết prompt còn thiếu qua Gemini hiện có, sau đó gửi từng clip x1. Có xác nhận trước khi chạy.
- Không tạo lại clip đã có hoặc tự thử lại lượt lỗi/chưa rõ. Thiếu khung đã duyệt thì chưa tạo. Clip nối b chờ duyệt a; nút Dừng gửi thêm vẫn dùng được.
- Giữ các ô ảnh/video khi cập nhật trạng thái; chỉ sửa phần DOM thay đổi. Không lưu lại toàn bộ dự án/tài sản khi phản hồi poll không đổi. Chỉ dựng phần chẩn đoán khi mở.
- Bấm tạo có phản hồi ngay trước các bước chuẩn bị/lưu; bỏ vẽ lại toàn bộ canvas sau mỗi thao tác của node và tránh vòng poll cũ vẽ lại khi chỉ có Veo đang chạy.
- Vẫn lưu ý định gửi bền vững trước POST, xác minh ảnh/prompt/cấu hình và nhập đúng cảnh. Duyệt chất lượng và Sang Dựng được cập nhật riêng.

Không thêm repo/thư viện mới: nguyên nhân ở việc dựng lại giao diện và lưu thừa. Benchmark Chromium cục bộ với 18 ảnh JPEG khác nhau (~284 KB base64/ảnh): phản hồi click khoảng 43 ms trước, ~1 ms sau; ảnh được giữ nguyên qua các lần đọc. Thời gian thực tế phụ thuộc máy và dữ liệu, không phải cam kết tốc độ tạo của Google.

Đã kiểm tra đúng HTML trích từ EXE: lưới/ảnh giữ nguyên và không lưu trên poll giống nhau; bảng cấu hình trên shell/iframe vẫn dùng được; tạo từ bộ lọc rỗng vẫn gửi đủ hai clip thiếu, tự viết đúng một prompt thiếu và giữ clip đã có; không vẽ lại canvas khi hàng đợi chạy; dừng khi chưa rõ; chờ duyệt a trước b; tự nhận clip và duyệt riêng vẫn hoạt động. Dùng API/CLI giả lập và video cục bộ. Chưa kiểm tra Flow thật hoặc chạy bộ cài Windows.

SHA256: `bbcea3522688812f31f075268cca45c0e8e95a3cbce53523742829e927fcd2f4`
