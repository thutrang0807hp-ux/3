# v43 — thay cơ chế trong node Video Veo hiện có

## Phạm vi

Thay nội dung và điều phối của chính node `node-videos` trong workflow tham khảo. Không tạo node thứ hai, không tạo workflow mới, không thay ID/cổng/dây liên kết. Các node Phân tích, Cảnh, Ảnh khung, Ảnh tham chiếu, Lời, Giọng đọc, Phụ đề và Sang Dựng tiếp tục dùng dữ liệu chung của dự án.

`veo-node.js` là module điều khiển mới của node đang có. Trình dựng video theo từng cảnh cũ chỉ tạo điểm gom tối thiểu, không dựng các video ẩn và bảng model cũ. `media-nodes.js` tiếp tục điều khiển node Ảnh khung; phần node Video được thay bởi module mới. Không ghép các file thử nghiệm trong agent-flow-fix vào bản này.

## Luồng mới

1. Chọn cảnh/phần clip ngay trong node. Ảnh đầu lấy từ khung đã duyệt; nếu bật nối khung thì lấy đúng đuôi phần trước theo clipStartImage.
2. Nhập/sửa prompt hoặc bấm Gemini viết riêng. Chạy video không tự gọi writer hoặc đi qua directDialog cũ. Khi ảnh/mốc đổi, giữ bản nháp nhưng yêu cầu rà và liên kết lại.
3. Kết nối một phiên Flow, rồi tạo đúng một clip. Node gọi thẳng `/flow/simple/jobs`, không qua bộ chọn tuyến engine/tiện ích cũ. Model mục tiêu là Lite 8 giây, 9:16, x1; người dùng kiểm tra trên Flow.
4. Các bước tiếp tục hiện trong chính node; cửa sổ kết nối dùng để đăng nhập và quản lý phiên. Nếu không tìm được nút Tạo duy nhất thì app yêu cầu người dùng bấm trực tiếp một lần, không đoán nút hay tự bấm lần nữa.
5. Người dùng chờ rồi tải đúng video trên Flow. Worker kiểm tra video, thời lượng/tỉ lệ/hash và yêu cầu xác nhận đúng clip. Node kiểm tra request/room/scene/part, khớp chữ ký ảnh+prompt rồi lưu vào `scene.clips` và assets dùng chung. Không chạy chuỗi watermark/CPU-review cũ khi nhập video mới; chỉ đọc metadata và một khung cuối để nối phần tiếp.
6. Bấm **Dùng clip này cho workflow** để ghi lựa chọn và receivedClipIds/reviewDecision dùng chung. Sang Dựng nhận được clip đã duyệt; lời, giọng đọc và phụ đề giữ liên kết theo cảnh/mốc. Không tự thay timeline đã chỉnh tay.

## Lịch sử và chống gửi trùng

Các lỗi cũ được giữ nguyên trong lịch sử, không đưa vào tổng lỗi lượt mới của node. Lượt cũ chưa rõ kết quả của phần clip đã chọn vẫn cần người dùng xác nhận đã xem lịch sử trước khi tạo thay thế; không tự biến thành chưa gửi. Lượt mới dùng ID mới, có ý định lưu trước gửi và negative receipt khi backend từ chối trước claim. Hủy sau khi có thể đã tạo giữ unknown; đối soát chỉ mở quyền tạo thủ công sau xác nhận, không tự retry.

Đọc lại video đã có không tạo clip mới; import idempotent theo request ID. Không để bộ directRecover cũ nhập cùng một kết quả lần nữa. Không nhập nếu phòng, ảnh, prompt, phần clip hay mốc đã đổi. Chặn bỏ theo dõi worker còn đang chạy tại route abandon chung. Node phòng khác không tiếp tục/dừng nhầm checkpoint của lượt đang chạy.

## Cài / sử dụng

- Đóng SceneForge, chạy `SceneForge-Update-20261031-v43.exe`. Chọn thư mục có SceneForge.exe + install-settings.json; shortcut người dùng gửi trước đó là `D:\4\releases\2026.10.28.2`, không chỉ `D:\4`.
- Updater giữ runtime/model/dữ liệu, sao lưu file thay trong thư mục updates của bản cài; baseline v2 và tối thiểu patch v14. Không cần cài v42 trước nếu đã có v40/v41 phù hợp baseline.
- Node cũ phải hiện **Veo v43**, ba phần Ảnh đầu / Prompt / Tạo và nhận, không còn dropdown model và nút Đọc lại model cũ.
- Chọn cảnh, kết nối Flow, nhập hoặc viết prompt, Tạo clip cảnh này, làm theo bước tiếp tục. Tải video trên Flow và xác nhận. Xem clip rồi bấm Dùng clip này cho workflow.
- Flow2API vẫn không chạy mặc định; Chrome/Playwright chỉ mở khi kết nối. Profile v42 của Flow đơn giản được giữ. Bản này không sao chép profile/cookie cá nhân hoặc Phoma.

## Kiểm tra đã chạy

- `check_veo_node_v43`: trình duyệt Chromium thật, mọi phản hồi Flow là fixture; một node, đúng cổng và dây trước/sau; sáu lỗi cũ không thành tổng lỗi mới; đúng ảnh đã duyệt + prompt tay đi duy nhất endpoint mới; double-click một request; video MP4 8s thật từ fixture nhận về đúng cảnh; Dùng clip → readyCount và Sang Dựng tăng; script/caption và voice giữ nguyên; nhập lại không nhân đôi; unknown cũ giữ và rà thủ công; thay ảnh buộc rà prompt; đổi phòng chặn dispatch. Đã chạy bằng frontend lấy chính từ payload phát hành.
- `check_simple_flow`: worker + thư viện thật trong fixture; xác nhận ảnh/prompt/credit, một lượt, download ffprobe/hash/đúng cảnh-phần, cancel trước/sau gửi, đối soát rõ ràng, video sai thời lượng bị từ chối; nút tạo dạng biểu tượng chuyển sang thao tác tay và app không bấm thêm.
- `check_simple_flow_api`: route mới trước frontend mount, receipt chưa gửi, không abandon worker đang chạy, stop/mode và không mở browser mặc định. Process đăng nhập giả, không Google.
- `check_simple_flow_ui`: bảng phiên có chọn browser và step token; chỉnh prompt trong node mới không tự gửi.
- `check_simple_flow_login`, `check_lightweight_start`: thứ tự xác nhận/profile và không spawn legacy engine mặc định; mock, không chứng minh đăng nhập Google.
- EXE resource ZIP, hash từng file payload, ZIP integrity, compile Python và mã backend trong payload khớp nguồn đều được kiểm tra.

Các bài UI lịch sử v41/v42 còn trong source để đối chiếu có selector của node cũ; không coi chúng là bài kiểm UI áp dụng cho v43. Không tuyên bố toàn bộ test lịch sử đều chạy đạt.

## Chưa xác minh

Chưa chạy updater trên Windows, chưa đăng nhập hay tạo video Google thật trong môi trường này, chưa benchmark RAM máy người dùng. Không khẳng định sửa được Google từ chối đăng nhập. Vẫn cần người dùng làm bước đăng nhập/xác minh và tải video; không tự phát hiện/tải kết quả. Phần thử nghiệm là cơ chế node mới cùng giao tiếp workflow, không phải chứng nhận tương thích mọi giao diện Flow.

Nguồn luồng đơn giản: rtrtr4 commit db5aa529c5203bee37cd05d4925b622419616b02. Không dùng bản đóng gói Phoma để chạy hoặc lấy fingerprint/captcha.
