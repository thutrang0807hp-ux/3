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

## Sửa tiếp sau báo cáo .41 — bản thử .42

Báo cáo thật ghi nhận Ingredients RPC đúng prompt, request được tracker nhận là http-1, HTTP200, phản hồi 228 byte nhưng decode_error=framing_mismatch và chưa có ID. Báo cáo đã lọc body thô nên không khôi phục được response để biết Flow trả ID hay trả lỗi. Lỗi decoder không giải thích được nguyên nhân phía Flow chưa tạo video.

Bản sửa code hỗ trợ thêm toàn bộ các dòng JSON RPC khi cách chia khung theo byte không đọc được: yêu cầu mọi dòng hợp lệ, chỉ các tag RPC đã biết, không bỏ qua đoạn hỏng, có duy nhất marker e/4 cuối cùng. Phần độ dài không khớp được ghi rõ trong metadata, không coi là đã kiểm tra byte framing. Payload vẫn phải qua điều kiện đúng RPC, prompt/dự án/request, duy nhất media row và đúng các ID. Không lấy UUID tùy ý.

Marker e/4 không còn bị coi là lỗi tạo. Bản ghi wrb.fr của đúng RPC có payload null và trường lỗi sẽ được báo riêng; chỉ xuất mã số và PUBLIC_ERROR_* đúng dạng, không xuất nội dung lỗi thô. Phản hồi bị từ chối chưa có ID vẫn giữ unknown và không tự retry; UI báo lỗi ngay thay vì đợi hết 60 giây.

17 kiểm thử bộ đọc/tracker đã qua. Bổ sung hai ca Chromium toàn luồng: RPC JSON theo dòng có marker kết thúc -> tải đúng video mẫu; RPC lỗi trong HTTP200 -> báo mã lỗi, không poll/download/retry. Đây là fixture tổng hợp, chưa phải kiểm thử lại body của báo cáo thật vì body đó không được lưu.

Người dùng đã yêu cầu đóng gói phần sửa này thành .42. Chưa xác minh lại trên Flow thật.
