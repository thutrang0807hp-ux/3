# Bản nháp môđun một cảnh — chờ duyệt, chưa nối vào ứng dụng

Nền: `cfb1493` (v46.42), nhánh `gh-pages`.

Mục tiêu là viết lại môđun tạo video theo cách tổ chức luồng của Phoma,
không tiếp tục thêm nhánh xử lý vào `SimpleFlow.run`. Bản này chưa sửa hay
thay thế đường đang chạy, chưa đóng gói EXE và chưa tạo video Google thật.

## Vấn đề phải giải quyết

Theo bàn giao, .34 (`7583a0b`) đã tạo được video thật. .42 nhận phản hồi
`PUBLIC_ERROR_UNUSUAL_ACTIVITY` (RPC code 7, HTTP 200). Thiếu ID ở lượt đó
là hậu quả của việc bị từ chối. Các kiểm thử dưới đây không chứng minh đã
khắc phục nguyên nhân từ chối. Không mặc định lỗi thuộc tài khoản hay thiếu token.

## Code mới

- `flow_scene_job.py`: điều phối một cảnh và SQLite lưu trạng thái bền vững.
- `flow_scene_rpc.py`: dựng payload Ingredients Lite và adapter gửi/đọc theo ID.
- `check_flow_scene_job.py`: 19 kiểm thử offline, bao gồm phản hồi RPC giả lập.

```text
Scene(request_id, account_id, room_id, scene_id, part, prompt, image)
  → reserve + fingerprint ảnh/prompt/cảnh
  → kiểm tra tài khoản → chuẩn bị ảnh và project → kiểm tra lại
  → commit dispatching trước khi gửi
  → gửi MZZa6b đúng một lần
  → lưu media_id/project_id/workflow_id trước mọi lần poll
  → jwpduf theo ID, 10 giây/lần, tối đa 30 lần mỗi đợt theo dõi
  → as29s cho đúng ID → stream/kiểm video → lưu vào cảnh
```

### Những bảo đảm của lõi

- Request ID cũ chỉ đọc lại bản ghi, không gọi tạo lần nữa.
- Cùng ID nhưng ảnh/prompt/cảnh thay đổi bị từ chối.
- Một tài khoản chỉ có một lượt chưa giải quyết; SQLite bảo vệ giữa các instance.
- Dừng/mất kết nối sau ranh giới dispatch được giữ `unknown`; crash để lại
  `dispatching` cũng không được tự gửi lại.
- ID nhận được phải đúng project và không được là ID ảnh nguồn.
- Lỗi ghi ID sau khi gửi không mở lại quyền gửi.
- `follow(request_id)` chỉ đọc trạng thái hoặc nhận video, không thể gọi tạo.
- Hết thời gian chờ vẫn giữ ID. Lỗi tải giữ `receiving` để nhận lại, không tạo lại.
- Kết quả gắn room/scene/part từ bản ghi đã lưu, không dò thumbnail hoặc prompt.
- Không hiển thị phần trăm render ước lượng.
- Store giữ hash ảnh/prompt và mã lỗi công khai; không giữ payload, thông tin
  xác thực, signed URL hoặc thông điệp lỗi thô.

### Những phần chưa nối, cần hoàn tất sau khi duyệt thiết kế

`NativeSession` là hợp đồng cần triển khai trên phiên SceneForge hiện có:

1. `check`: xác nhận tài khoản/profile/project trước mỗi thao tác.
2. `prepare`: dùng đường ảnh đã chạy được, lấy và xác minh media ID của đúng ảnh
   trong đúng project. Không bịa ID khi UI chưa trả ID.
3. `reference_context`: lấy context yêu cầu qua cơ chế phiên Flow thông thường.
   Không dùng token cố định, không xuất cookie hoặc xử lý vượt thử thách.
4. `rpc`: gửi RPC trong trang đã đăng nhập, trả HTTP status và body trong bộ nhớ;
   không tự retry lệnh tạo. Kiểm tra đầy đủ lỗi RPC bên trong HTTP 200.
5. `receive`: chỉ nhận URL đúng ID đã kiểm tra; stream giới hạn dung lượng, kiểm
   ffprobe (container, thời lượng, tỉ lệ), lưu nguyên tử vào đường dẫn ổn định
   theo request ID. Chưa hoàn tất bước này thì không được nối vào ứng dụng.

Không có implementation phiên thật trong bản nháp này. Vì vậy code chưa phải
một bản cập nhật có thể cài để khôi phục tạo video. Không nối GUI hoặc endpoint
đang dùng vào adapter chưa hoàn tất này.

Store mới tách khỏi ledger cũ để duyệt cách điều phối. Khi tích hợp cần chọn
một nơi lưu chính hoặc viết cầu nối với RequestLedger; không để hai nơi cùng
nhận quyền gửi. Chưa nhập/chuyển/xóa các lượt `unknown` hiện có. Lượt crash
ở `preparing`/`dispatching` cần bước đối soát rõ ràng; chưa có API tự mở khóa.
Phiên đầu chỉ hỗ trợ prompt chữ và một ảnh; chưa xử lý tag ảnh trong prompt,
batch, x2–x4, upscale hoặc chuyển model tự động.

## Căn cứ Phoma đã đọc

File người dùng cung cấp: `phoma_code.rar`, 24.043.506 byte. Chỉ giải nén và
đọc tĩnh; không chạy backend, bộ cài hoặc toàn bộ package Phoma.

Backend: `phoma_code/browser-server-dist/index.js`.
SHA-256: `929a8acef0f970dbf3bf7672c165119b151cfd6be7f1e8c9c18c88a4084910bd`.

- `Lc` dựng payload reference video; `jo` dựng request context.
- `Uc`: portrait 9:16 là enum 1; landscape 16:9 là enum 2.
- `FE`/`ps`: model mặc định reference Lite là `veo_3_1_r2v_lite`.
- `kE`: MZZa6b; `Wc`: jwpduf; `ci`: as29s.
- `ps`: chuẩn bị workspace/ảnh rồi mới submit, poll 10 giây, tối đa 30 lần.
- `Dc`/`Xx`: mã 3 thành công, 4/5 thất bại.

Đã chạy riêng hàm dựng payload thuần `Lc` với dependency stub và UUID cố định,
đối chiếu cấu trúc với builder Python cho prompt chữ + một ảnh: khớp.
Không chạy Phoma để thử tài khoản, không chứng nhận schema Flow hiện hành.

## Kiểm tra đã chạy

Trong `/workspace/3/veo-node-v46`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m local_engine.check_flow_scene_job
```

19/19 đạt: chống gửi trùng, hai workflow cùng request, thay nội dung, timeout,
cancel, RPC từ chối, crash trước ghi ID, lỗi ghi trước/sau gửi, đổi ảnh khi
chuẩn bị, timeout poll rồi resume, lỗi tải rồi resume, khóa tài khoản còn lượt
chưa giải quyết, provider failure, payload và chuỗi RPC theo đúng ID.
Adapter nhận tệp trong test là test double; không phải kiểm thử video/ffprobe thật.

Sau khi duyệt: hoàn tất NativeSession, thử một cảnh trên phiên hợp lệ có xác
nhận của người dùng, chứng minh Flow chấp nhận và trả video rồi mới mở rộng.
Không đóng gói hoặc tuyên bố sửa xong chỉ dựa trên kết quả offline.
