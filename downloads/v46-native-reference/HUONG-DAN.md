# SceneForge v46.43 — bản thử gửi Ingredients trực tiếp

Yêu cầu **v46.42 (2026.11.02.4642) trở lên**, đúng baseline v2 đã cài.
Không cài đè lên bản cũ hơn .42. Đây là bản thử, chưa xác minh trên Flow thật
và chưa chạy bộ cài trên Windows.

## Cài và thử một cảnh

1. Đóng SceneForge. Chạy `SceneForge-Update-20261103-v46.43-Native-Reference-Trial.exe`.
2. Chọn đúng thư mục chứa `SceneForge.exe` và `install-settings.json`; theo bàn
   giao trước là `D:\4\releases\2026.10.28.2`. Updater kiểm phiên bản, sao lưu
   bốn file thay và giữ tài khoản/profile/dự án/model/runtime.
3. Mở lại app, giữ tài khoản web đang chọn. Với lượt cũ `unknown`, đối soát như
   trước; bản này không tự mở khóa hoặc gửi lại lượt cũ.
4. Chọn một cảnh mới cần làm, chuẩn bị ảnh + prompt bằng luồng hiện tại rồi
   bấm **Tạo 1 video** đúng một lần. Giao diện và bước chuẩn bị chưa được gộp
   thành một nút trong bản thử này. Lệnh được Flow chấp nhận có thể dùng credit.
5. Xem trạng thái: nếu nhận ID, app theo dõi và thử tải video về đúng cảnh.
   Nếu dừng trước gửi, giữ nguyên thông báo lỗi để chẩn đoán; không bấm lặp lại
   khi app báo lượt đã gửi/chưa rõ kết quả.

## Thay đổi thực sự

- Lượt có receipt ảnh + prompt được gửi bằng RPC `MZZa6b` trong phiên Flow hiện
  có; không bấm Generate và không tự quay về bấm Generate khi đường mới lỗi.
- Payload giới hạn một ảnh, prompt chữ, `veo_3_1_r2v_lite`, portrait, một kết quả.
- Thu media ID của lần upload hiện tại khi đối chiếu được byte ảnh + project
  trong request và duy nhất ID trong response; hoặc đọc ID từ chip composer.
  Không xác minh được thì dừng trước gửi; không đoán ID từ thumbnail.
- Dùng API xác minh thông thường mà trang đã nạp. Nếu không tìm duy nhất public
  site key hoặc API không sẵn sàng thì dừng. Không dùng preload/hijack, solver,
  thay fingerprint, cookie export hoặc profile thứ hai từ Phoma.
- Chỉ RequestLedger cũ cấp quyền gửi. Lõi SceneStore nháp chưa được cài vào app.
- Lưu ID ngay sau phản hồi hợp lệ rồi dùng tracker .42 để kiểm tra trạng thái
  và nhận video theo ID. Không tự retry lệnh tạo, không ước lượng phần trăm render.
- HTTP 200 vẫn có thể là RPC từ chối. `PUBLIC_ERROR_UNUSUAL_ACTIVITY` chưa được
  chứng minh đã sửa. Lỗi sau khi bắt đầu gửi giữ lượt `unknown` như trước.

## Giới hạn cần biết

Đây là thử nghiệm thay đường gửi, không phải toàn bộ môđun mới đã hoàn thiện.
Chưa có tự resume theo dõi sau khi khởi động lại app; không hứa khôi phục ID
các lượt cũ. Chưa hỗ trợ tag ảnh inline, x2–x4 hoặc hàng đợi nhiều cảnh. Giữ
UI hiện có nên tiêu đề node vẫn có thể hiện v46; kiểm bản cài tại `app-build.json`.

Nếu gặp `native_sitekey_not_unique`, `native_enterprise_unavailable` hoặc chưa
đọc được mediaId, lệnh tạo chưa gửi. Cần báo nguyên văn thông báo để điều chỉnh
bộ nối theo trang thật; không coi fixture đạt là chứng minh tài khoản chạy được.

Kiểm thử Chromium dùng HTTP fixture đã đi qua: gửi một lần → ID → poll → tải
video mẫu và ffprobe/hash, RPC từ chối, lỗi đọc, lỗi tải, mất kết nối, dừng,
thiếu ID ảnh và thiếu site key. Upload composer hồi quy đạt. 40 kiểm thử Python
offline đạt. Bộ cài chỉ được kiểm tra cấu trúc PE/ZIP nhúng và hash từng file;
chưa chứng nhận giao diện updater hoặc việc tạo/tải Google thật trên Windows.

Không thay bốn file của bản .42 một cách thủ công nếu đang có lượt chạy.
Nếu cần quay lại, dùng bản sao lưu updater trong thư mục `updates` của bản cài
và giữ nguyên dữ liệu dự án/tài khoản; không xóa lịch sử để tạo lại lượt cũ.
