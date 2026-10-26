# Thanh công cụ Từ ảnh & ý tưởng — 26/10/2026

Thanh chính được thu gọn thành nguồn Ảnh/ý tưởng, nguồn Video, tiến độ, **một nút
bước tiếp theo** và menu **⋯**. Các node và dữ liệu dự án giữ nguyên.

## Sử dụng

- Chọn Gemini Chat hoặc Muse ở nguồn ảnh/ý tưởng, Flow hoặc Muse ở nguồn video.
  Muse storyboard vẫn là đường thao tác tay; video Muse hiện vẫn là muse.ai,
  chưa xác minh Meta AI. Lựa chọn dùng lại cấu hình dự án và pool tài khoản hiện có.
- Nút chính theo dữ liệu dự án: Thêm ảnh → Chuẩn bị kịch bản → Tạo storyboard →
  Viết prompt video → Tạo clip còn thiếu → Rà & duyệt clip → Mở trong Dựng.
  Có tác vụ chờ thì chuyển sang Xem tiến độ/Nhận kết quả, không tự gửi lại.
- Tạo storyboard, viết prompt và tạo clip vẫn mở bảng rà trước khi người dùng
  bấm gửi. Không gộp thành một lượt tự chạy có thể tính phí. Nếu có nhiều phương
  án kịch bản chưa chọn, nút chính dẫn về chọn phương án trước.
- **Tiến độ** gom storyboard, prompt và clip trong một bảng. Kiểm tra kết quả chỉ
  đọc/đối soát các lượt đã có. Kết quả chữ Gemini vẫn cần rà rồi Áp dụng. Các lượt
  chưa rõ không tự được coi là thất bại hoặc tự tạo lại.
- **⋯** chứa Storyboard tổng, Viết/sửa prompt, Chia clip, tạo clip còn thiếu,
  quản lý tài khoản/kết nối, tiến độ và chi tiết lượt gửi. Các chức năng cũ vẫn có
  đường mở; không đặt toàn bộ nút cấu hình/kết quả trên thanh thường trực.
- Nút kết nối chỉ dẫn theo ngữ cảnh khi đọc thấy nguồn chưa sẵn sàng. Tài khoản
  đầy đủ vẫn mở được từ menu. Đóng bảng cấu hình hoặc đổi nguồn sẽ đọc lại trạng
  thái. Cache UI không được dùng thay cho kiểm token/tài khoản ở bước gửi thật.
- Nút “Tạo phần thiếu & ghép” cũ ở chân trang được ẩn để tránh hai hành động chính
  gây nhầm. Các nút ghép/sửa trong node vẫn giữ; không xóa chức năng hay dữ liệu.

## Bố cục và mã

`scripts/photo-studio/toolbar.js` là lớp cuối sau `clip-flow.js` trong
`scripts/demo-web/build.py`. Nó thay `photoRenderProviders` bằng giao diện gọn;
không sửa backend tạo ảnh/video, bảo vệ credit, duyệt/dọn hoặc giới hạn đồng thời.

Thanh không dựng lại toàn DOM mỗi lần render nên giữ focus chọn nguồn. Chiều cao
cố định theo breakpoint, chừa chỗ biểu tượng kết nối; không đổi khi đọc trạng thái.
Menu cạnh nút ⋯, hỗ trợ Escape/click ngoài. Cửa sổ hẹp dùng hai hàng cố định và
không kéo ngang thanh. Node placement/zoom không bị tự căn lại khi cập nhật toolbar.

## Kiểm chứng

`python -m local_engine.check_photo_toolbar` dùng Chromium, app/backend/kho thật
và fixture GET trạng thái dịch vụ: các bước mở đúng bảng rà; không có POST tạo AI;
đối soát read-only; nguồn đổi vẫn giữ nội dung; route sang Dựng; menu chức năng;
kết nối theo ngữ cảnh; focus/vị trí/chiều cao; kiểm khung 1600, 800 và 390 px.
Entry point cũ `scripts/app-shell/check_photo_provider_toolbar.py` gọi bài kiểm mới.

Hồi quy `check_photo_clip_flow` và `check_photo_review_fixes` vẫn kiểm file/editor,
chia lời, duyệt và kết quả lỗi thời. Chưa xác minh generation bằng tài khoản thật
hoặc Windows. Xem `review/PHOTO_TOOLBAR_CHECKS.json` trong gói code đánh giá.
