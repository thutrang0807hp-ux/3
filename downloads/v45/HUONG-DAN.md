# v45 — trả lại giao diện Tài khoản cũ, Veo dùng tài khoản đăng nhập web đang chọn

## Thay đổi đúng phạm vi

Khôi phục bố cục tab Tài khoản trước v44: thống kê, sơ đồ tài khoản, bảng danh sách, nhật ký và credit. Bỏ khối thay thế `Flow dùng cho node Video Veo` của v44. Giữ các tab dịch vụ và kiểu giao diện cũ. Flow hiện chạy một clip/lượt nên điều khiển mức song song vẫn ở bố cục cũ nhưng chỉ đọc, không hứa chạy 16 clip.

**Đăng nhập Flow chỉ tại Cài đặt → Tài khoản → Flow → Đăng nhập Flow trên web.** Dùng lại route `/flow/web-login`, lớp FlowWebLogin, bảng accounts, AccountPool và registry flow-managed-profiles đã có; không đưa trở lại cookie/engine login riêng cho node.

Node Video Veo trong workflow phân tích lấy trực tiếp tài khoản đang chọn trong bảng đó. Không còn nút Kết nối Flow, chọn trình duyệt hoặc quản lý phiên ở node, kể cả khi node chưa có cảnh. Tên tài khoản thay đổi tự động qua thông báo cùng nguồn giữa cửa sổ/iframe; trước gửi vẫn đọc lại lựa chọn thật từ API. Khi chưa đăng nhập/chọn hoặc tài khoản hết hạn, node hướng dẫn xử lý tại tab Tài khoản.

Bộ chạy giữ phần ảnh + prompt + gửi một lần + theo dõi/nhận video của v44, nhưng bám vào chính cửa sổ/profile do đăng nhập web ở tab Tài khoản mở. Không mở một browser/profile SimpleFlow khác. Khi việc xong, chỉ ngắt client điều khiển, giữ cửa sổ đăng nhập. Cửa sổ đóng hoặc nick đổi thì dừng trước gửi thêm; không tự đăng nhập lại.

## Cài và dùng

1. Đóng SceneForge. Chạy **SceneForge-Update-20261101-v45.exe** và chọn đúng thư mục chứa SceneForge.exe cùng install-settings.json, theo shortcut đã cung cấp là `D:\4\releases\2026.10.28.2` (không chỉ D:\4).
2. Updater kiểm baseline v2, yêu cầu tối thiểu patch v14 và sao lưu các file thay trong thư mục updates của bản cài. Không cài lại runtime/model, không hạ Playwright, không xóa dự án/video/tài khoản/profile.
3. Mở lại. Trong tab Tài khoản cũ, chọn tài khoản đã đăng nhập web còn dùng được; nếu chưa có hoặc cửa sổ đã đóng, dùng Đăng nhập Flow trên web tại đây. Mở đúng dự án Flow trong cùng cửa sổ này và giữ cửa sổ mở. Đăng nhập/xác minh Google vẫn do bạn thực hiện.
4. Sang workflow: node phải hiện **Veo v45**, tên tài khoản đã chọn và **không có nút kết nối riêng**. Chọn ảnh đầu đã duyệt, prompt và tạo clip như trước. Không cần xác nhận/kết nối một phiên thứ hai trong node.
5. Nếu Flow thay giao diện hoặc đầu vào chưa xác minh, giữ bước rà thủ công tương ứng của v44. Tiến độ chỉ hiện khi đọc được từ thẻ kết quả đúng; không tạo phần trăm giả. Video nhận về đúng phòng/cảnh/phần clip, sau đó bấm Dùng clip này cho workflow để duyệt sang các node sau.

Các tài khoản đã có trong bảng cũ không bị xóa. Một dòng tài khoản engine hoặc tiện ích không tự được coi là phiên web có profile. Nếu trước đây chỉ đăng nhập bằng bảng Flow riêng của v43/v44, cấu hình/profile ấy vẫn được giữ trong Data để đối chiếu, nhưng v45 không tự sao chép nó sang tài khoản khác hoặc dùng ngầm làm phương án dự phòng. Hãy dùng đăng nhập web ở tab Tài khoản một lần để có tài khoản/profile trong hệ thống dùng chung.

## Ghim tài khoản và chống nhầm lượt

Lượt mới chấp nhận selection_token của AccountPool dùng chung, không dùng token SimpleFlow riêng. Sau khi nhận việc, ghim account_id và kiểm email/profile thật trước các thao tác. Đổi lựa chọn khi một lượt đang chạy áp dụng cho lượt sau; lượt đang chạy vẫn thuộc tài khoản ban đầu. Token cũ, tài khoản bị tắt/xóa/hết hạn, profile hoặc danh tính đổi đều không cho gửi thêm thao tác. Mở đăng nhập web trong khi Veo đang chạy bị chặn để tránh thay phiên giữa lượt.

Giữ schema job v43 và các ID/cổng/dây/data clip hiện có. Đọc lại ID đã gửi không tạo lại. Chưa rõ sau khi có thể đã bấm tạo thì cần đối soát ở phòng gửi lượt đó, không tự retry hoặc chọn tài khoản khác. Đường `/flow/simple/jobs` còn là endpoint của bộ chạy, không phải một hệ thống tài khoản riêng. `/flow/simple/connect` không mở trình duyệt trong app v45; các nút cũ còn sót nếu được gọi sẽ đưa về tab Tài khoản. Cấu hình mode cũ không được bật lại đăng nhập riêng trong node.

## Kiểm tra đã chạy

- `check_account_cdp_v45`: Chromium thật, cửa sổ mở bằng cơ chế web-login có sẵn và probe/CDP thật; đăng ký tài khoản qua FlowWebLogin, bộ chạy mới nối đúng cửa sổ đó, đọc 37%, tải và xác minh MP4 dọc 8s; không mở thêm browser/profile; sau việc cửa sổ còn sống; đóng cửa sổ thật thì lượt mới thất bại trước bấm tạo. Toàn bộ website bị thay bằng fixture và DNS ngoài bị chặn, không Google thật.
- `check_account_session_v45`: registry đăng nhập web và AccountPool thật; hai tài khoản dùng đúng profile, ghim lượt đang chạy, lựa chọn mới cho lượt sau, chặn token cũ/tài khoản hết hạn/đổi nick, đúng account/scene/video. Attach trình duyệt được mock.
- `check_account_api_v45`: API lựa chọn trong tab Tài khoản bằng API status của Veo/provider; route đăng nhập web cũ; chặn kết nối riêng, không để mode cũ tách phiên, chặn đăng nhập giữa lượt và bỏ theo dõi lượt đang chạy.
- `check_account_ui_v45`: giao diện thật sau rebuild, sơ đồ/bảng cũ hiển thị; nút đăng nhập gọi route cũ; node không có kết nối ngay cả khi trống; đổi tài khoản ở cửa sổ tab Tài khoản tự cập nhật sang node và token request mới; không gọi đăng nhập riêng. Status API thật, login và gửi job dùng fixture.
- `check_veo_node_v45`: cùng một node/cổng/dây, ảnh/prompt đúng, một lần gửi, tiến độ thực hoặc không xác định, nhập clip đúng cảnh, duyệt sang Sang Dựng, giữ lời/giọng/phụ đề, chống nhập trùng và dữ liệu đổi. Chromium và API fixture.
- `check_simple_flow_v44`, `check_simple_flow`, `check_flow_web_login`, `check_lightweight_start`: hồi quy adapter/worker, bảo vệ gửi trùng, đăng nhập và khởi động nhẹ. Các test constructor standalone của SimpleFlow không đại diện đường đăng nhập người dùng trong app v45. Các test UI v43/v44 cũ dùng selector cũ, không tuyên bố tất cả test lịch sử đều áp dụng/đạt.

Đã đối chiếu nội dung và hash từng file trong ZIP nhúng của EXE với nguồn. Kiểm tra UI bản giao dùng frontend trích từ chính payload đó.

**Chưa chạy updater trên Windows, chưa đăng nhập hay tạo video Google thật trong môi trường này.** Không tuyên bố sửa được Google từ chối đăng nhập hoặc tương thích mọi giao diện Flow. Bản này sửa nơi đăng nhập và cách node dùng phiên; các bước fallback khi Flow không nhận diện được vẫn giữ như v44.

## Mã cần đọc

`local_engine/flow_account_session.py`, `simple_flow.py`, `server.py`, `scripts/app-shell/account-dispatch.js`, `scripts/shared/simple-flow-panel.js`, `scripts/workflow/veo-node.js`. Registry/profile/browser probe và FlowWebLogin cũ được dùng lại. Source/update công khai không chứa dữ liệu tài khoản, cookie hay mã Phoma.
