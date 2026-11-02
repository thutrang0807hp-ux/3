# Bản nháp theo dõi Flow bằng ID — để duyệt code

Người dùng đã duyệt code và cho phép triển khai. Đã chạy kiểm thử bộ đọc, Chromium, ledger và video mẫu; chưa chạy thử gửi tạo trên Flow thật. Bản phát hành thử .41 giữ cờ live_flow_verified=false.

## Luồng và các tệp

1. `flow_network_protocol.py`: giải mã form f.req, JSON lồng, XSSI và JSON có khung độ dài. Đây là bản nháp đã có trước, nay được dùng bởi bộ đọc schema.
2. `flow_task_protocol.py`: đọc đúng các vị trí của Ingredients request và response, không quét lấy UUID bất kỳ.
3. `flow_task_tracker.py`: liên kết request/response của đúng lần bấm, giữ ID, đọc trạng thái và thông tin asset, tải tệp đúng ID. Chỉ có hai RPC đọc trong bộ gọi; không có hàm gửi tạo RPC.
4. `flow_network_probe.py`: chuyển dữ liệu transient của request/response sang tracker. Báo cáo mạng vẫn chỉ chứa dữ liệu được lọc.
5. `simple_flow.py`: giữ nút Generate hiện có, hook tracker trước lần bấm duy nhất, ghi provider_task vào ledger, dùng đường theo dõi ID khi đã cài tracker. Khi đường này không liên kết được ID, không quay sang nhận video bằng prompt/thumbnail.
6. `check_flow_task_tracker.py`: các ca kiểm tra đề xuất để chạy sau khi duyệt.

## Điều kiện nhận ID

- Request được quan sát sau mốc bấm Generate, trong 15 giây đầu.
- Đúng endpoint batch, origin Flow và source-path dự án đang dùng.
- Đúng RPC Ingredients video MZZa6b; một request, một output.
- Prompt ở đúng trường prompt, khớp sau chuẩn hóa khoảng trắng; dự án trong payload cũng khớp.
- Có cấu trúc ảnh tham chiếu hợp lệ. Ảnh/prompt trước Generate vẫn do bước validate_prepared hiện có kiểm tra.
- Response của chính request đó, HTTP 2xx, không có lỗi RPC, một media row có mediaId/projectId/workflowId đúng kiểu. Không nhận input image ID làm output video ID.
- Nếu có hai request tương ứng, vô hiệu liên kết và dừng nhận tự động.
- Sau 15 giây cửa sổ đối chiếu mới cho phép bắt đầu polling.

## Theo dõi và kết thúc

- Đọc status theo mediaId, khoảng cách ít nhất 10 giây.
- Chỉ nhận status của cùng mediaId + projectId + workflowId.
- Theo schema Phoma 1.6.2: 3 thành công, 4/5 thất bại; 1/2 đang chờ; mã khác báo chưa hỗ trợ.
- Thành công: lấy asset detail, bắt buộc cùng ba ID, URL HTTPS flow-content.google/video/<mediaId>; URL ký chỉ ở bộ nhớ.
- Tải stream giới hạn 100 MiB, không redirect, dùng page hiện có; kiểm tra tài khoản trong lúc tải. ffprobe hiện có kiểm tra MP4/WebM, 8 giây, 9:16 trước khi ghi done.
- Chỉ lỗi tạo có ID/status xác định mới ghi failed. Lỗi đọc hoặc hết thời gian giữ unknown; không tự gửi lại.
- Không lấy được ID sau 60 giây thì dừng chờ với thông báo cần kiểm tra. Ba lần lỗi đọc, hoặc hết 10 phút theo dõi, cũng dừng chờ và giữ lượt.
- Không nhận sự kiện download bất kỳ của trình duyệt làm kết quả của đường theo dõi ID.
- Không bịa số %. Khi không có phần trăm render thì progress là null và trạng thái có chữ mô tả.

## Giới hạn cần đánh giá trước khi chạy

- Đây là schema rút ra từ mã Phoma 1.6.2, chưa có capture tạo video thực tế của SceneForge chứng minh cùng cấu trúc.
- Hiện chỉ nhận Ingredients RPC MZZa6b. Nếu Flow dùng RPC mới hoặc prompt có inline reference tags làm đổi cấu trúc, code báo chưa hỗ trợ.
- Reader chỉ dùng metadata phiên WIZ hiện có; nếu build label chưa có hoặc phiên yêu cầu xác minh, không cố lấy CAPTCHA hoặc vượt xác minh.
- Lượt unknown cũ không có ID không thể được khôi phục chỉ bằng bản nháp này. ID mới được ghi bền trong ledger, nhưng chức năng mở lại một lượt đã dừng để tự tải tiếp chưa được nối vào nút đối soát cũ.
- Signed URL có thể bị CORS chặn; trường hợp đó giữ ID và báo lỗi tải, không nhận video khác hoặc tạo lại.
- Chưa thay giao diện thành một nút; bản nháp tập trung vào vòng gửi -> ID -> trạng thái -> đúng kết quả.

## Kiểm tra đã chạy

Form/XSSI/nested JSON; prompt/dự án/output sai; HTTP200 chứa lỗi RPC; duplicate RPC; framing thiếu; UUID bất kỳ; URL/video sai ID; trước click; hai lượt gửi; status của video khác; lỗi tài khoản; lỗi ghi ledger; phân biệt lỗi đọc với tạo thất bại; không xuất session marker/prompt/signed URL trong snapshot.

Toàn luồng Chromium dùng fixture chặn toàn bộ HTTP: thành công (tải và ffprobe tệp MP4 thật), Flow báo thất bại, phản hồi thiếu ID, hai request phù hợp, status của video khác, HTTP503 khi đọc, HTTP403 khi tải và Dừng. Đã xác nhận đọc lại cùng request không gửi thêm lượt. Các ca rút ngắn thời gian đợi để chạy kiểm thử, không thay bộ giải mã hoặc đường tải tệp.
