# Đối chiếu gửi tạo: Phoma / SceneForge .34 / SceneForge .44

Phạm vi: tìm khác biệt có căn cứ trước khi sửa tiếp. **Chưa xác định nguyên
nhân Google từ chối tạo; không có bản update mới từ cuộc đối chiếu này.**

## Bằng chứng đầu vào

- .34: `7583a0b`, người dùng từng xác nhận tạo video thật.
- .44: `48e84aa`, báo cáo người dùng xác nhận upload nhận ID và resolve ảnh
  thành công, sau đó MZZa6b bị `PUBLIC_ERROR_UNUSUAL_ACTIVITY`, RPC code 7.
- Người dùng xác nhận Phoma vẫn tạo được trong khi SceneForge thất bại.
  Chưa có cặp request thành công/thất bại cùng điều kiện được đối chiếu trực tiếp.
- Code Phoma người dùng cung cấp, backend SHA-256:
  `929a8acef0f970dbf3bf7672c165119b151cfd6be7f1e8c9c18c88a4084910bd`.
  Đọc source và chạy các hàm cô lập với dữ liệu giả; không chạy backend Phoma.

Không đưa báo cáo người dùng, ID tài khoản/project/media, đường dẫn dữ liệu
máy người dùng, prompt hoặc dữ liệu phiên vào GitHub.

## Kết quả đã kiểm tra trực tiếp

### 1. Code mở profile của .34 và .44 giống hệt

Đã so byte và SHA-256 của bốn file ở hai commit:

| File | Kết quả |
|---|---|
| flow_background_session.py | Giống hoàn toàn |
| flow_account_session.py | Giống hoàn toàn |
| flow_ui_session.py | Giống hoàn toàn |
| flow_managed_driver.py | Giống hoàn toàn |

Không có căn cứ gọi đây là lỗi do một thay đổi mới sang headless hoặc thay
profile trong bốn file này. **Code không đổi không chứng minh Chrome, phiên
đăng nhập, trạng thái Google hoặc môi trường thực thi không đổi theo thời gian.**

.34 để trang Flow phát request sau click Generate; .44 tự dựng request. Vì
không có bản ghi request của lần .34 thành công, không thể suy ra mọi field
của request .34 chỉ từ source SceneForge.

### 2. Payload .44 khớp Phoma trong cấu hình đang kiểm tra

Đã lấy **chính chuỗi SUBMIT trong source .44**, chạy với fetch giả, đọc lại
payload thực sự được hàm đó gửi và so với hàm Lc cô lập của Phoma. Kết quả khớp
toàn bộ cấu trúc khi cố định UUID/context/token giả:

- Một ảnh tham chiếu, prompt chữ không có tag tham chiếu inline.
- `MZZa6b`, model `veo_3_1_r2v_lite`, portrait enum 1, một output row.
- Vị trí ID ảnh, project context và các UUID cùng cấu trúc.

Điều này **không kiểm tra tính hợp lệ của token thật**, không chứng minh
Phoma đang chạy cấu hình đó trên máy người dùng và không bao phủ prompt có tag.
Khác biệt ảnh/prompt hash trong report cũng không tự chứng minh prompt bị đổi:
tracker hash prompt sau chuẩn hóa khoảng trắng, receipt hash prompt gốc đã strip.

Code ps của Phoma chọn đường theo generationMode nếu được chỉ định, hoặc theo
việc có ảnh reference khi mode chưa được chỉ định. Nhãn giao diện “Tạo từ mô
tả” và model “Lite” riêng lẻ không đủ xác định đường RPC:

| Đầu vào/mode | Đường trong source Phoma |
|---|---|
| Text | YhhmEf, nhóm model t2v |
| Reference/Ingredients | MZZa6b, nhóm model r2v |
| Khung đầu | eb1hJf, nhóm model i2v |
| Khung đầu/cuối | nprQif, nhóm model interpolation/first-last |

Đã đọc ảnh settings người dùng cung cấp: Lite, 9:16, tải 720p, hai luồng;
PRO chọn 8s và ULTRA chọn 6s. Ảnh chưa có reference hoặc cảnh; chưa chứng minh
lần chạy thành công dùng đường nào hoặc tier nào. Không tự đổi SceneForge
sang 6s hay text chỉ dựa vào màn hình settings này.

### 3. Metadata HTTP có khác, nhưng chưa có bằng chứng gây từ chối

Đã chạy riêng transport $e của Phoma và SUBMIT .44 với cùng dữ liệu giả:

| Phần | Phoma | SceneForge .44 |
|---|---|---|
| Query `hl` | Có | Không có trên lệnh generation |
| Referrer trong fetch options | Đặt source-path rõ ràng | Dùng mặc định trình duyệt |
| Credentials | include | same-origin |
| `_reqid` | Dựa trên context request + counter | Dựa trên thời gian |
| Nguồn metadata | WIZ, có fallback dữ liệu trang/request trước | WIZ cho generation |
| Headers chính | content-type, x-same-domain | Cùng hai header đó |

Hai chế độ credentials cùng gửi cookie cho request cùng origin trong trường
hợp này. Referrer mặc định có thể tương đương referrer được đặt rõ khi trang
ở đúng project. Không được diễn giải bảng trên thành bằng chứng “thiếu cookie”.
Upload .44 dùng transport có `hl`/referrer rõ, trong khi generation dùng hàm
riêng. Đây là khác biệt triển khai thực, **chưa phải nguyên nhân được xác nhận**.
Không phát hành bản “sửa UNUSUAL_ACTIVITY” chỉ bằng cách thêm query hoặc header.

### 4. Chuẩn bị xác minh trong Phoma không tương đương hoàn toàn

Ở đường video của source Phoma: ps gọi Ot với action VIDEO_GENERATION trước
kE; Ot gọi b0, và b0 có bước chuẩn bị bổ sung trước execute. Source còn có
cơ chế can thiệp môi trường trình duyệt/xác minh. .44 chỉ gọi API Enterprise
thông thường mà trang đã nạp; các cơ chế can thiệp đó chưa được chuyển sang.

Không thể gọi hai phiên là giống hoàn toàn chỉ vì model/payload giống. Cũng
không thể kết luận một cơ chế cụ thể trong source Phoma chắc chắn là lý do
Phoma thành công ở lần chạy người dùng đang nói tới.

Upload dùng action MEDIA_GENERATION; tạo video dùng VIDEO_GENERATION. Google
chấp nhận upload **không đồng nghĩa** đã chấp nhận yêu cầu tạo video hoặc việc
xác minh riêng cho hành động đó.

### 5. Không tìm thấy bước warmup clip thường bị bỏ sót

Bốn warmup NfrxTb / ve2Lsc / DTaVef / nzlxg khớp source Phoma. Hàm refresh AE
được gọi trước upscale trong đoạn đã đọc; không phải bằng chứng phải gọi thêm
nó trước mọi lần tạo clip thường. Không thêm request hoặc delay theo phỏng đoán.

Phoma có cơ chế tuần tự hóa/cooldown theo workspace và chốt dừng sau unusual
activity. SceneForge có gate một lượt và giữ unknown sau từ chối. Cần so hành
vi thực tế trước khi quy lỗi cho tốc độ hoặc mức song song.

### 6. Theo dõi/tải chưa phải nơi gây ra lần từ chối này

Report .44 có poll_count=0 và RPC tạo bị từ chối trước khi nhận ID video. Sửa
poll, dò thumbnail hoặc download không thể khôi phục việc tạo ở lần này.

Report có trường generation_ready/message của receipt chuẩn bị còn giữ nội
dung cũ sau generation_rejected. Đó là điểm cần chỉnh báo cáo, **không phải
bằng chứng lệnh tạo chưa gửi hoặc nguyên nhân Google từ chối**. Trạng thái
provider_task/rpc_rejected và phase submit_rejected mới mô tả kết quả gửi.

## Bước tiếp theo dựa trên bằng chứng

1. Xác nhận cấu hình **đang dùng thật trong Phoma**: Ingredients/Frames,
   Lite/Fast, ratio và duration. Source có nhiều đường RPC/model; mặc định
   Lite trong source không chứng minh UI Phoma đang dùng Lite Ingredients.
2. Nếu cấu hình khác, đối chiếu đúng đường/model trước khi sửa; không so một
   lần Frames/Fast thành công với Ingredients/Lite rồi kết luận hai payload giống.
3. Nếu cùng cấu hình, cần một cặp tóm tắt request thành công/thất bại đã loại
   bỏ dữ liệu đăng nhập: method/RPC, cấu trúc payload, model/ratio/output count,
   project/source-path khớp hay không, các tên query/header và mã response.
   Không gửi HAR thô, cookie, Authorization, form at, token xác minh hoặc signed URL.
4. Kiểm tra những khác biệt đó rồi mới chọn patch. Có thể chuẩn hóa transport
   cho nhất quán, nhưng không gọi đó là fix đã chứng minh khi chưa thử thật.

Hiện chưa có quyền truy cập phiên Windows/Flow thực tế của hai ứng dụng trong
cloud. Dữ liệu còn thiếu là quan sát lần chạy, không phải thêm fixture cho
cùng một giả định. Không tự gửi thêm video, đổi tài khoản hoặc xóa lịch sử.

## Tái chạy phép đối chiếu offline

```sh
python3 scripts/analysis/compare_reference_submit.py \
  --phoma /path/to/phoma_code/browser-server-dist/index.js \
  --output /tmp/flow-submit-audit.json
```

Script từ chối source Phoma khác hash đã đọc; không thực hiện mạng, không mở
profile, không đọc credential. Kết quả đã chạy lưu ở
[flow-submit-audit-20261103.json](flow-submit-audit-20261103.json).
