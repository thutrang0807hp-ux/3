# SceneForge .172 — bấm X ẩn thật xuống khay

## Sử dụng

Đóng hẳn bản cũ trước khi chạy cập nhật. Sau cập nhật:

- Bấm X (hoặc Alt+F4) chỉ ẩn cửa sổ xuống khay hệ thống. Backend, WebView và hàng chờ vẫn được giữ nguyên.
- Lần đầu ẩn có thông báo SceneForge vẫn đang chạy.
- Nhấp đúp biểu tượng khay hoặc chọn Mở SceneForge để quay lại đúng cửa sổ/dự án đang dùng.
- Mở shortcut SceneForge khi app đang ẩn cũng yêu cầu cửa sổ hiện lại, không mở backend thứ hai.
- Chọn Thoát hoàn toàn trong menu khay để lưu rồi dừng app. Nếu lưu lỗi và bạn chọn không thoát, app và tác vụ được giữ.
- Khi cập nhật các bản tiếp theo, phải chọn Thoát hoàn toàn trước; bấm X không còn là thoát.

Chrome/Edge và các tab Gemini/Flow đang kết nối vẫn cần được mở như trước. Giữ hàng chờ khi ẩn app không có nghĩa có thể đóng trình duyệt phục vụ tác vụ.

## Nguyên nhân và thay đổi

Host trước đó không có NotifyIcon hoặc thao tác ẩn xuống khay. FormClosing luôn gọi RequestClose, FormClosed gọi Stop, sau đó OwnedProcessJob/StopBackend dừng backend và các tiến trình thuộc app. Một biểu tượng còn nhìn thấy không chứng minh backend đang sống.

Host mới tạo biểu tượng khay thật; đường UserClosing hủy đóng Form và chỉ Hide/ShowInTaskbar=false. Không Dispose WebView, không đóng owned-process job, không gọi StopBackend và không chạy handshake thoát khi chỉ ẩn. WebView2 dùng các cờ hạn chế background timer/renderer throttling để vòng chờ JavaScript vẫn hoạt động. Không tự suspend WebView. Hàng chờ hiện tại được giữ trong cùng instance.

Đường Thoát hoàn toàn giữ nguyên handshake lưu cũ, cảnh báo lưu lỗi và cleanup process job. Cleanup bỏ biểu tượng khay. Lần khởi động thứ hai gửi thông điệp Windows theo mã định danh thư mục dữ liệu để hiện lại cửa sổ đang ẩn. Không tạo dịch vụ Windows, tác vụ khởi động hay tiến trình nền thứ hai.

## Kiểm tra và giới hạn

- Đã biên dịch host Windows x64 .NET Framework 4.8 với SDK WebView2 hiện có.
- Đã biên dịch/chạy các phương thức C# đóng/ẩn/hiện/thoát thực tế với seam mô phỏng shell và WebView: X giữ backend/job/WebView; không chạy flush/exit; khôi phục trạng thái maximize; thoát thật lưu/dừng đúng một lần và xóa icon; hủy thoát khi lưu lỗi giữ tiến trình; OS shutdown đi đường thoát.
- Đã chạy hàng chờ hai cảnh bằng node/backend/ledger thật với tiện ích/Gemini mô phỏng, document.visibilityState=hidden: cả hai job trả đúng cảnh, không gửi lại, broker vẫn sẵn sàng.
- Đã kiểm source/PE và cờ background; RequestClose, StopBackend, OpenExternal và cơ chế quản lý tiến trình giữ nguyên so với .171.
- Chưa chạy tích hợp Windows Shell/WebView2 thật trên máy Windows. Phép thử visibility-hidden không thay thế kiểm tra occlusion của WebView2 trên Windows. Cần xác nhận bấm X trên máy bạn vẫn tiếp tục nhận ảnh/video.

Không đổi prompt V5.2, model, API, tiện ích, tài khoản, dữ liệu hoặc giao diện web. Builder pin mọi tệp runtime ngoài SceneForge.exe giống .171. Không cần cài lại tiện ích. Gói gộp nhận từ .62 trở lên.
