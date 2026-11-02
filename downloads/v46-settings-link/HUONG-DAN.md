# SceneForge v46.42 — bản thử theo dõi video bằng ID

1. Đóng SceneForge. Chạy `SceneForge-Update-20261102-v46.42-RPC-Response-Fix.exe`, chọn thư mục chứa SceneForge.exe và install-settings.json. Yêu cầu v46.7 trở lên. Giữ tài khoản, profile và dữ liệu đã cài.
2. Với video cũ unknown, kiểm tra và giữ video trước khi xác nhận cho phép lượt mới. Bản này chưa khôi phục được các lượt cũ thiếu ID.
3. Chuẩn bị ảnh + prompt như hiện tại. Bấm Tạo 1 video một lần cho một clip mới bạn cần làm.
4. App đọc request/response của lần bấm đó. Nếu khớp prompt, dự án và schema, app lưu mediaId/projectId/workflowId rồi đọc trạng thái mỗi 10 giây. Không gọi lại API tạo.
5. Khi Flow báo hoàn tất cho đúng ID, app thử lấy và tải đúng tệp về cảnh, kiểm tra video bằng ffprobe rồi mới ghi hoàn tất. Lỗi tạo, lỗi đọc và lỗi tải được báo riêng. Không có số % render thì chỉ hiện trạng thái, không bịa phần trăm.
6. Nếu chưa lấy được ID sau 60 giây, có ba lần lỗi đọc, hoặc hết 10 phút theo dõi, app dừng chờ, giữ lượt và không tự tạo lại. Nếu cần kiểm tra, bấm Tải báo cáo theo dõi video; xem `record.provider_task` và `network_probe`.

Bản này được kiểm thử với Chromium, ledger và tệp video mẫu; toàn bộ HTTP trong kiểm thử bị thay bằng fixture. Chưa chứng minh schema hoặc đường tải hoạt động trên Flow thật, chưa chạy installer trong Windows. Nếu Flow thay giao thức, thiếu metadata phiên hoặc chặn tải bằng CORS, app báo chưa nhận được kết quả và giữ ID nếu đã có.

Log không xuất body thô, prompt của request mạng, cookie, header xác thực, query string hoặc signed URL. Báo cáo chẩn đoán hiện có có thể chứa prompt cảnh để đối soát. Bộ đọc chỉ sử dụng phiên Flow hiện có; không thao tác CAPTCHA, không sao chép profile hoặc xuất thông tin đăng nhập.

Giữ nguyên bộ upload thư viện v46.19 và đường upload/gắn ảnh/prompt v46.33 đã được người dùng xác nhận. Chưa gộp giao diện thành một nút; thay đổi lần này tập trung vào liên kết tác vụ và nhận kết quả.

## Thay đổi riêng của .42

Sửa lỗi đọc phản hồi RPC ghi nhận trong báo cáo .41: có request tạo đúng prompt và HTTP200 nhưng bộ đọc báo response_framing. Bổ sung cách đọc toàn bộ dòng JSON RPC có duy nhất marker e/4 cuối cùng khi không đọc được cách chia khung byte; không chấp nhận dữ liệu dở dang hoặc bỏ qua đoạn hỏng. Không còn coi marker e/4 là lỗi tạo.

Nếu đúng RPC tạo trả payload rỗng kèm lỗi, app hiện mã số hoặc PUBLIC_ERROR_* được trả về; không xuất thông điệp thô có thể chứa dữ liệu phiên. HTTP200 không được coi là tạo thành công. App không tự gửi lại khi phản hồi lỗi hoặc chưa có ID.

Đã qua 17 kiểm thử bộ đọc/tracker, cùng hai ca Chromium bổ sung dùng HTTP fixture: phản hồi theo dòng -> tải video mẫu đúng ID; RPC lỗi trong HTTP200 -> báo lỗi, không poll hoặc tải. Body thật trong báo cáo .41 không được lưu, nên chưa chứng minh bản sửa đã giải mã được chính response đó hoặc đã giải quyết việc Flow chưa tạo video.
