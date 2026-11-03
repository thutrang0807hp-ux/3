# SceneForge .55 — cấu hình Flow thu gọn trên thanh Workflow

Cập nhật từ .52 trở lên. Cấu hình nằm trong mục **⚙ Flow** cạnh các tab Workflow;
bấm để mở/thu gọn. Bảng dài không còn nằm trong node Video Veo. Đổi lựa chọn
vẫn tự đồng bộ như .54, có trạng thái xác nhận hoặc lỗi.

Đã bỏ hai nút của phần cài đặt: Thử đồng bộ lại và Tải báo cáo cài đặt. Không xóa
API hoặc dữ liệu chẩn đoán backend. Nếu đồng bộ lỗi, đổi lựa chọn để thử lại.
Giữ nguyên các nút kiểm tra/tải lại video cũ vì chúng phục vụ nhận clip đã tạo.

Giới hạn hiện có: nút tạo trong SceneForge chỉ hỗ trợ Ingredients · Lite · 9:16 · x1.
Các lựa chọn khác có thể đồng bộ sang Flow, nhưng chưa được hỗ trợ khi gửi tạo
trong SceneForge. Không thay đổi CLI, upload một ảnh hoặc phần nhận video.

So với .54 chỉ frontend thay đổi; bốn tệp backend trong gói có checksum giữ nguyên.
Đã kiểm tra Chromium với shell/iframe thật và API giả lập, tự đồng bộ, đóng/mở,
trạng thái lỗi, khung hẹp và cách ly worker nền; kiểm tra UI nhận lại clip cũng qua.
Chưa chạy updater Windows hoặc xác minh thao tác Flow thật trong môi trường này.

SHA256: `bc75590f09fb6d64b45e143c19ce569feacac898e10482f96367aeb81fd04649`
