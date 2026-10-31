# Veo v44 — dùng chung phiên Flow, gửi và theo dõi clip trong workflow hiện có

Bản cập nhật 2026.11.01.44 thay cơ chế điều phối trong chính node Video Veo. Giữ ID node, cổng, dây nối, dữ liệu cảnh/clip và liên kết với Ảnh khung, Sang Dựng, Giọng đọc, Phụ đề. Không thêm node hay workflow thứ hai.

## Cài đặt

1. Đóng SceneForge. Chạy **SceneForge-Update-20261101-v44.exe**.
2. Chọn đúng thư mục chứa SceneForge.exe và install-settings.json. Theo shortcut đã cung cấp trước đây: `D:\4\releases\2026.10.28.2`, không chỉ `D:\4`.
3. Updater kiểm baseline v2, yêu cầu tối thiểu patch v14, sao lưu các file thay thế trong thư mục `updates` của bản cài. Không cài lại Python, model, runtime; không hạ Playwright. Dự án, ảnh, video và profile vẫn giữ.
4. Mở lại; node phải hiện **Veo v44**. Không cần cài lần lượt v42/v43 nếu baseline đang hợp lệ.

## Sử dụng

- Lần đầu sau cập nhật, vào **Tài khoản → Flow** hoặc **Quản lý phiên Flow** trong node. Hai nơi dùng chung một phiên. Chọn Edge/Chrome, đăng nhập và xác nhận đúng dự án. Với quy trình đăng nhập hiện có, đóng cửa sổ đăng nhập khi được yêu cầu rồi xác nhận dự án trong cửa sổ app mở lại.
- Trình duyệt, URL dự án, email nếu đọc được và mã lựa chọn được lưu trong vault trên máy. Lần sau tạo clip tự mở lại profile và dự án đó; không bắt tạo dự án mới. Nếu không đọc được email, xác nhận tài khoản một lần khi mở lại phiên. Đổi tài khoản/dự án dùng **Đăng nhập lại / đổi dự án**. Không xuất hoặc sao chép cookie.
- Chọn cảnh/phần clip, ảnh đầu đã duyệt và prompt rồi bấm **Tạo clip cảnh này**. Một xác nhận trong app cho phép gửi một lượt Lite 8s, 9:16, x1 có thể tốn credit.
- Worker thử chọn chế độ/cài đặt qua các điều khiển được nhận diện, tải ảnh, xác minh có preview mới trong vùng nhập, điền prompt và bấm Tạo duy nhất một lần. Hỗ trợ nút Tạo có chữ và biểu tượng arrow_forward trong vùng nhập.
- Khi không xác minh được một số đầu vào, app gộp thành **một bước kiểm tra**, liệt kê đúng phần cần bạn xem. Không còn mặc định hỏi riêng dự án → ảnh → prompt → gửi ở mỗi clip. Giao diện không nhận diện được nút Tạo vẫn yêu cầu bạn bấm một lần trên Flow.
- Worker tìm thẻ kết quả mới khớp prompt, loại thẻ cũ/đã có trước khi gửi và không tự chọn khi có nhiều thẻ khớp. Thẻ không có ID máy chủ được gắn ID cục bộ dựa trên vùng chứa prompt và một trạng thái/video. Không gọi RPC riêng hay lấy token CAPTCHA.
- Node hiển thị trạng thái cùng phần trăm chỉ khi đọc được từ chính thẻ Flow đang theo dõi. Nếu không có phần trăm hoặc không đọc được đúng thẻ, hiển thị chờ không xác định; không dựng tiến độ giả.
- Khi xác định duy nhất video của lượt đó và nút tải thuộc thẻ, worker tự tải, kiểm MP4/WebM, 8 giây, 9:16, dung lượng và hash, rồi nhập đúng phòng/cảnh/phần clip. Menu tải chỉ chọn bản gốc/720p rõ ràng, không bấm upscale. Nếu chưa tự tải được, tải đúng clip trên Flow rồi xác nhận trong app; không tạo lại.
- Xem video và bấm **Dùng clip này cho workflow** để duyệt clip cho các node sau như v43. Không tự ghi đè timeline đã chỉnh tay.

## Trạng thái và chống gửi trùng

Giữ schema job v43 để tiếp tục đọc lịch sử/lượt đang có, dù giao diện là v44. Chỉ một lượt chạy; ID cũ đọc lại không gửi lại. Đổi phòng, ảnh, prompt hoặc mốc chặn nhập sai dữ liệu. Lỗi sau khi có thể đã bấm Tạo giữ trạng thái chưa rõ, cần đối soát; không tự retry, đổi tài khoản hoặc tạo lượt bù. Ngắt phiên giữ cấu hình dự án để dùng lần sau, không xóa profile.

Trong đường Flow đơn giản, tab Tài khoản hiển thị phiên thật dùng chung thay cho bảng chọn tài khoản engine cũ, bộ chia 1–16 clip và bảng kết nối Google cũ. Đường engine cũ còn trong mục mở rộng, không chạy mặc định.

## Kiểm tra và giới hạn

Đã kiểm bằng Chromium với các trang/endpoint bị chặn và thay bằng fixture, dùng MP4 8 giây thực để xác minh tệp: một lần gửi, tiến độ 37%, nhận video đúng cảnh/phần; loại thẻ cũ, ID xuất hiện muộn, nhiều kết quả, phần trăm không có; chọn giá trị cài đặt thực và popover; một bước kiểm tra khi chưa xác minh; lưu/mở lại phiên và chặn đổi email. Kiểm thêm API, đăng nhập/lifecycle bằng mock, UI thực đã rebuild, liên kết workflow, duyệt clip, idempotency và mặc định không khởi động engine cũ.

**Chưa chạy updater trên Windows và chưa đăng nhập/tạo video Google thật từ môi trường này.** Các selector của Flow thật có thể khác fixture: không tuyên bố tự động hóa 100% hay sửa được Google từ chối đăng nhập. Khi không nhận diện được thẻ, cài đặt hoặc nút tải, bản này chuyển sang bước thủ công tương ứng. Người dùng vẫn thực hiện đăng nhập/xác minh Google khi được yêu cầu. Không đưa mã Phoma hoặc dữ liệu tài khoản vào bản cập nhật/source công khai.

## Mã nguồn và kiểm tra

Mã cần đọc trước: `local_engine/simple_flow.py`, `simple_flow_dom.py`, `scripts/workflow/veo-node.js`, `scripts/shared/simple-flow-panel.js`, `scripts/app-shell/account-dispatch.js`.

Các bài áp dụng: `python -m local_engine.check_simple_flow_v44`, `check_veo_node_v44`, `check_simple_flow`, `check_simple_flow_api`, `check_simple_flow_ui`, `check_simple_flow_login`, `check_lightweight_start`. Các bài UI lịch sử v41/v43 dùng selector bản cũ, không coi tất cả bài lịch sử là kiểm tra UI v44.
