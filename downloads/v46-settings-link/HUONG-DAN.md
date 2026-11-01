# v46.24 — gắn ảnh của cảnh, điền prompt và gửi một lượt

Đóng SceneForge, chạy `SceneForge-Update-20261102-v46.24-Thumbnail-Crop.exe`, chọn thư mục có SceneForge.exe và install-settings.json, bấm Cập nhật rồi mở lại. Cài trên v46.7 trở lên của bộ cài v2. Giữ nguyên hàm upload .19, tài khoản, profile và dữ liệu.

## Thử một cảnh

1. Duyệt đúng ảnh đầu của cảnh và rà prompt chuyển động ở node Video Veo.
2. Giữ cấu hình **Video · Thành phần (Ingredients) · Veo 3.1 Lite · 9:16 · x1** cho bước thử tạo một clip. Chưa thêm cài đặt thời lượng; luồng nhận clip hiện vẫn kiểm 8 giây và dọc 9:16 như trước.
3. Bấm **Chỉ tải ảnh lên dự án Flow**, chờ hoàn tất bằng đường upload .19 đã chạy được.
4. Bấm **Gắn ảnh + điền prompt**. Phần mềm đối chiếu thumbnail với ảnh gốc của lượt upload trong cùng phòng/tài khoản, mở menu ⋮ của ảnh khớp duy nhất, chọn Add to prompt (Image nếu có submenu), rồi điền và đọc lại prompt của đúng cảnh. Bước này chưa gửi tạo video.
5. Xem **ảnh kiểm tra trên Flow**. Nếu đúng ảnh/prompt/cấu hình, bấm **Tạo 1 video trên Flow** và xác nhận cho phép gửi; có thể tốn credit. Backend kiểm lại ảnh, prompt, tài khoản, phòng và setting trước khi gửi một lần.
6. Lượt tạo dùng bộ theo dõi và nhận video hiện có. Nếu chưa rõ kết quả, giữ để kiểm tra, không tự gửi lại. Chưa có hàng đợi nhiều cảnh hoặc chạy đồng thời.

## Khi chưa gắn được

Bấm **Tải báo cáo ảnh/prompt**, gửi JSON và ảnh kiểm tra trong chat. Báo cáo có phase, hash ảnh/prompt, các thumbnail ứng viên và kết quả đối chiếu; không lưu URL media có chữ ký. Không tự gửi báo cáo đi.

Nếu có nhiều ảnh khớp: hiện thumbnail và nút Dùng ảnh 1/2/... để người dùng chọn. Sau lựa chọn, đối chiếu lại đúng media ID cùng ảnh nguồn rồi tiếp tục; không chọn ảnh đầu danh sách. Nếu thư viện quá lớn, không khớp thumbnail, menu khác, hoặc ô tạo đang chứa ảnh/prompt khác: dừng để kiểm tra, không ghi đè. Không dùng Animate. Nếu đổi ảnh, prompt, cảnh, phòng hoặc setting sau chuẩn bị, cần chuẩn bị lại. Nhãn sẵn sàng thuộc lần kiểm tra đó; backend đọc lại ngay trước lúc gửi.

Đối chiếu thumbnail hỗ trợ ảnh đổi kích thước/nén nhẹ và đòi duy nhất một ứng viên; đây không phải bằng chứng media ID từ API. Người dùng cần xem ảnh kiểm tra trước khi xác nhận gửi ở lượt thử trên Flow thật.

## Kiểm chứng

Người dùng đã xác nhận upload .19 và setting .20 hoạt động trên máy của mình. Phần mới của .21 **chưa được xác nhận trên Flow thật**, chưa chạy updater trên Windows. Đã kiểm Chromium với ảnh và trang mô phỏng: đúng ảnh, Add to prompt, prompt nguyên nội dung, không chọn ảnh trùng, không ghi đè prompt khác, chặn ảnh/prompt/cảnh đổi; route chuẩn bị có ảnh kiểm tra; ledger thật gửi đúng một lần và không gửi lại khi kết quả chưa rõ. Giao diện khóa tạo trước khi có receipt và khi prompt đổi. Bộ hồi quy upload .19 đạt.

Hàm upload giữ nguyên SHA-256 `342e1bde247a0ca3612efe7c363cb0d741c84a1b014a71c35a402d1e6aba5869`. Gói có 5 file: simple_flow.py, simple_flow_upload.py, flow_settings.py, flow_prepare.py và workflow.html; kiểm SHA-256 từng file và giữ nguyên mã launcher.

## Sửa theo báo cáo Flow thật

Báo cáo .21 dừng ở match_library_reference vì có hai thumbnail khớp cùng sai số 0.756 nhưng media ID khác nhau. Setting đã đọc lại đúng Video / Ingredients / 9:16 / Lite / x1; chưa tới bước mở menu ảnh hoặc điền prompt. .22 thêm trạng thái chờ chọn thumbnail, kiểm tra lựa chọn còn thuộc đúng cảnh/prompt/tài khoản và media ID vẫn khớp ảnh nguồn. Ghi nhớ binding ảnh trong phiên hiện tại để lần chuẩn bị tiếp theo không hỏi lại nếu còn đúng. Không cần upload thêm vì gặp ảnh trùng trong cùng phiên. Khi khởi động lại app sau cập nhật, vẫn thực hiện bước upload như quy trình bên trên.

Đã kiểm Chromium tái hiện hai media ID, chọn ID thứ hai sau khi danh sách đổi thứ tự, thumbnail PNG, chặn lựa chọn giả/cũ và không chạm menu, prompt hoặc Generate trước khi người dùng chọn. Phần mới chưa được thử trên Flow thật.

## .23 — nhận diện ảnh trong ô tạo và phản hồi thao tác

Ảnh chụp từ máy người dùng cho thấy đã bấm Add to prompt nhưng kiểm tra ảnh đính kèm chưa đạt, nên nút Tạo bị khóa. .23 hỗ trợ thumbnail nhỏ/cắt giữa ảnh, chip nằm phía trên hàng nhập prompt và chip CSS có media ID trùng ảnh nguồn đã đối chiếu. Khi chip tồn tại từ phiên trước, ID phải đối chiếu được với thumbnail thư viện khớp ảnh gốc. Không coi riêng ảnh trong thư viện là ảnh đã gắn.

Ngay khi bấm Gắn ảnh + điền prompt, trạng thái hiện trong node; khi lỗi API, thông báo được giữ lại. Dưới nút Tạo luôn có lý do nếu chưa sẵn sàng: chờ chọn thumbnail, chuẩn bị lỗi, prompt đổi, setting chưa đúng hoặc còn lượt chưa rõ kết quả. Chỉ mở khi đủ bước. Báo cáo ảnh/prompt có attachment_probe ghi kích thước ảnh, vùng composer, ID và cách kiểm chứng; không ghi URL media.

Đã kiểm Chromium với thumbnail 24px bị crop, chip phía trên form nhập, chip CSS, ảnh sai và trường hợp chỉ có ảnh thư viện; kiểm phản hồi lỗi API vẫn hiện trong node và lý do khóa nút. Đây là kiểm thử mô phỏng, chưa xác nhận phần mới trên Flow thật hoặc updater Windows.

Nếu ảnh là thành phần inline trong editor, .23 chèn chữ mà không Select All hoặc phát phím Enter, để giữ ảnh đã gắn và tránh gửi sớm. Đã kiểm ảnh inline còn nguyên, prompt đúng và Generate chưa được bấm.

## .24 — so thumbnail theo cách Flow hiển thị

Báo cáo .23 ghi nhận scope composer 600×160 có đúng một img đã tải, natural 670×1200 hiển thị 50×50, sai số đối chiếu 18.272. Setting vẫn đúng. Mã cũ dùng crop giữa mặc định khi đối chiếu thumbnail nhỏ; báo cáo chưa ghi cách lấy pixel hoặc CSS nên chưa thể khẳng định ảnh sai hay phép so sánh sai.

.24 giữ cách đọc canvas ảnh gốc nếu được phép. Nếu CORS chặn canvas và phải chụp img hiển thị, bộ so sánh dựng đúng object-fit, object-position, padding/viền và chỉ loại pixel góc bo/viền không chứa ảnh. Ngưỡng xác minh vẫn là 4, ảnh sai tiếp tục bị chặn. Báo cáo ghi capture_method (canvas/screenshot), object_fit, object_position, border_radius và kích thước ảnh để xác định chính xác nếu vẫn chưa khớp. Không lưu URL ảnh.

Đã tái hiện Chromium với ảnh 670×1200 hiển thị 50×50 khác origin, canvas bị chặn: cách crop giữa cũ báo sai lớn; đối chiếu theo CSS nhận đúng cover/top, cover/center, fill và contain. Ảnh màu khác bị từ chối; prompt chỉ điền khi ảnh được xác nhận, không bấm Generate trong chuẩn bị. Phần mới chưa xác nhận trên Flow thật và chưa chạy updater Windows.
