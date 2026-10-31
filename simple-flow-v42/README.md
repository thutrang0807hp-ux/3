# SceneForge v42 — node Veo theo luồng SimpleFlow

## Thay đổi

- Đường Flow mới là mặc định, tách khỏi account pool/engine/tiện ích cũ. Một phiên, một clip mỗi lượt. Node vẫn dùng ảnh khung đã duyệt và prompt hiện có; Gemini viết lại là bước riêng.
- `Kết nối / tiếp tục Flow đơn giản` mở bảng chọn Chrome/Edge, đăng nhập bằng cửa sổ thông thường, xác nhận đã đóng, rồi mở lại cùng profile bằng Playwright theo quy trình repo rtrtr4. Không tự nhận đăng nhập thành công khi chỉ mở cửa sổ. Chọn duy nhất một tab dự án sau bước xác nhận.
- Giữ các bước xác nhận: dự án/chế độ, ảnh đã gắn, kiểm tra prompt + Lite 8s/9:16/x1 và chi phí trước khi bấm Tạo một lần. Không tự dò/chuyển model trong popup như đường cũ.
- Người dùng chờ video và bấm tải trên Flow. Worker nhận sự kiện tải từ tab của lượt đó; kiểm tra video, 8 giây và 9:16, SHA256, xác nhận đúng clip rồi lưu vào thư viện và trả đúng room/scene. Không tự phát hiện video tạo xong hoặc tự bấm tải.
- Request ID trùng không tạo thêm lượt. Chỉ một clip hoạt động; node chặn gửi clip khác khi đang chạy. Dừng trước khi bấm Tạo là failed; dừng sau đó là unknown, chặn lượt mới tới khi người dùng kiểm tra lịch sử Flow và xác nhận đối soát. Không tự retry/đổi tài khoản.
- Mở app không tự khởi động Flow2API. Playwright/Chrome chỉ được khởi chạy khi người dùng kết nối. Không thêm OpenCV hay tải runtime/model mới. Đây là giảm thành phần chạy ngầm, chưa phải phép đo RAM hay tối ưu toàn bộ media gallery.

## Cài và thử

1. Đóng SceneForge. Chạy `SceneForge-Update-20261031-v42.exe`. Chọn đúng thư mục có SceneForge.exe + install-settings.json; theo shortcut người dùng gửi trước đó là `D:\4\releases\2026.10.28.2`, không phải chỉ `D:\4`. Updater kiểm tra baseline v2/minimum v14 và sao lưu các file thay vào thư mục updates của bản cài.
2. Mở app; node phải hiện `Veo v42`. Không trộn thủ công file `agent-flow-fix` với v42; nhánh đó giữ nguyên để đối chiếu, không phải nguồn v42.
3. Trên node bấm `Kết nối / tiếp tục Flow đơn giản`, chọn Edge hoặc Chrome đã cài. Đăng nhập, kiểm tra Flow, đóng các cửa sổ của phiên vừa mở và bấm Tiếp tục. Nếu Google từ chối: Dừng, không thử tự động lặp lại.
4. Trong cửa sổ mở lại, kiểm tra đúng tài khoản, giữ một tab dự án muốn dùng và Tiếp tục. Profile riêng nằm ở Data/browser-profiles/simple-flow/<browser>; không sao chép cookie/profile cá nhân hay profile Phoma.
5. Ảnh khung phải được duyệt. Viết hoặc sửa prompt như cũ. Bấm Đọc lại model nếu cần, rồi Chạy 1 clip.
6. Mở lại bảng Flow đơn giản, làm theo các bước. Sau khi tạo, chờ trên Flow rồi tự tải đúng video; xác nhận trong bảng để clip được nhập về cảnh.
7. Dùng Ngắt phiên khi xong để đóng browser automation của phiên này. Đóng bảng chỉ đóng bảng, không hủy lượt đang chạy.

## Đường cũ / khôi phục

Cấu hình, tài khoản, dự án và lịch sử cũ không bị xóa. Bảng có lựa chọn đường cũ. Vì engine cũ không tự chạy mặc định, nếu dùng lại nhánh cần Flow2API thì mở app từ môi trường có `SCENEFORGE_LEGACY_FLOW_ENGINE=1`. Đây là lựa chọn đối chiếu; không bật thêm engine khi dùng SimpleFlow. File cũ đã có trong thư mục updates do updater tạo. Việc khôi phục toàn bộ patch trên Windows chưa được chạy kiểm thử ở đây.

## Đã kiểm tra

- `check_simple_flow_login`: thứ tự xác nhận, profile/browser đúng, chưa chạy Playwright trước bước đầu; mock browser/process, không gọi Google.
- `check_simple_flow`: Chromium thật với mọi URL bị thay bằng fixture; ảnh và prompt qua đúng checkpoint, một lượt/ID trùng, tải video 8s portrait thật từ fixture, ffprobe/hash, media-library capture/file serving, hủy trước/sau gửi, đối soát thủ công, đổi account dừng và video sai thời lượng bị từ chối.
- `check_simple_flow_ui`: giao diện thật từ chính payload v42; bảng tài khoản/step token và node chỉ chuyển một slot khi có hai cảnh.
- `check_simple_flow_api`: route thật và shutdown, browser process giả; không khởi động trình duyệt/engine thật.
- `check_lightweight_start`: có cấu trúc engine cũ nhưng không spawn mặc định.
- `check_video_node`: các hành vi đường cũ, viết prompt/per-clip/giữ lượt chưa rõ và model refresh vẫn đạt với provider fixture.
- Payload ZIP, resource nhúng trong EXE, hash từng file và compile Python đạt.

## Giới hạn phải giữ rõ

Chưa chạy updater trên Windows; chưa xác minh đăng nhập Google hay tạo video Google thật. Không khẳng định v42 sửa được Google từ chối đăng nhập. Không benchmark RAM/khởi động trên máy người dùng. Runtime Playwright người dùng báo 1.64.1 được giữ nguyên; không hạ phiên bản theo requirements nguồn. Cần người dùng thử đúng một clip thực tế để đánh giá đường mới.

Nguồn tham khảo: https://github.com/thutrang0807hp-ux/rtrtr4 commit db5aa529c5203bee37cd05d4925b622419616b02. Upload adapter được điều chỉnh từ upload_reference của repo này. Không lấy mã fingerprint/captcha hoặc chạy bộ cài Phoma.
