# SceneForge v46.44 — bản thử toàn luồng native một cảnh

Yêu cầu **v46.42 trở lên**, gồm v46.43 đang cài. Phiên bản trong
`app-build.json`: **2026.11.03.4644**. Đây là bản thử; chưa xác minh tạo video
trên Flow thật và chưa chạy giao diện updater trên Windows.

## Cài và thử

1. Đóng SceneForge. Chạy `SceneForge-Update-20261103-v46.44-Native-Pipeline-Trial.exe`.
2. Chọn đúng thư mục có `SceneForge.exe` và `install-settings.json`; theo bàn
   giao trước là `D:\4\releases\2026.10.28.2`. Updater kiểm baseline/phiên bản,
   sao lưu file thay; giữ profile, tài khoản, dữ liệu, model và runtime.
3. Mở lại app, chọn tài khoản web hiện có. Giữ lịch sử cũ; bản này không tự mở
   khóa hoặc gửi lại lượt `unknown`.
4. Chọn **một cảnh** cần làm, ảnh đã duyệt và prompt. Giữ cấu hình Ingredients
   · Lite · 9:16 · x1. Bấm **Tạo 1 video** một lần và xác nhận. Không cần bấm
   Thử ảnh + prompt hay gắn chip ảnh trên Flow. Nếu Flow chấp nhận, có thể dùng credit.
5. Chờ app tự chuẩn bị project, upload, lưu ID ảnh, gửi tạo, lưu ID video và
   theo dõi/nhận video. Nhận xong thì xem clip và chọn Dùng clip này cho workflow.

## Nếu bị lỗi

Không bấm tạo lặp lại khi chưa rõ kết quả. Bấm **Tải báo cáo theo dõi video**
và gửi file JSON cùng nguyên văn thông báo lỗi. Bản .44 cho phép tải báo cáo
của lượt lỗi upload, không yêu cầu có ID video và không mở trình duyệt để tải
báo cáo đó.

Trong báo cáo, các trường cần đối chiếu:

- `record.native_inputs.native_stage`: phiên, upload, sẵn sàng hay đã bắt đầu gửi.
- `record.native_inputs.uploaded_media_id` và `uploaded_media_project`: ID ảnh
  lưu từ phản hồi upload trước khi xác minh ảnh.
- `record.native_inputs.upload_uncertain`: upload có thể đã tới Flow nhưng
  app chưa nhận được kết quả đầy đủ; không tự upload lại.
- `record.provider_task`: ID video, trạng thái liên kết, mã RPC từ chối nếu có.

Thiếu ID ảnh ở .43 không đồng nghĩa .44 đã lấy được ID trên tài khoản thật.
Cần xem báo cáo của đúng lượt mới để xác minh từng mốc. Không gửi cookie,
token hay thông tin đăng nhập trong chat.

## Thay đổi so với .43

Thay đường chuẩn bị project và upload: dùng phiên đăng nhập hiện có, tạo/dùng
lại project, warmup, upload RPC nhận ID trực tiếp và đọc lại đúng ảnh/project.
Không dựa vào DOM composer để bắt ID, không điền prompt qua UI. Prompt và cấu
hình được ghim vào payload của cảnh. Một nút tạo gọi toàn luồng backend.

Vẫn chỉ RequestLedger cũ cấp quyền gửi. Không tự fallback sang bấm Generate,
không tự retry khi uncertain, không dùng preload/hijack hay cơ chế thay
fingerprint từ Phoma. Nếu xác minh thông thường không sẵn sàng, app dừng và báo lỗi.

## Kiểm chứng và giới hạn

Các file trích từ chính EXE đã kiểm tra hash và ZIP integrity; pipeline và UI
đã chạy Chromium + ledger + video mẫu/ffprobe, mọi HTTP dùng fixture. Các ca
upload bị từ chối, generation bị từ chối và đổi project đều được kiểm tra.
Không coi đó là chứng minh schema/site key/quota hoặc việc tạo Google thật.

Chưa có resume tự động sau restart, chưa hỗ trợ hàng đợi nhiều cảnh. Không
khẳng định đã hết `PUBLIC_ERROR_UNUSUAL_ACTIVITY`. Lượt đã gửi nhưng mất kết
quả vẫn phải đối soát trước khi tạo lượt khác.
