# Sửa sau đánh giá độc lập — Từ ảnh & ý tưởng, 26/10/2026

## Phạm vi đã chốt

Sửa chia clip/câu, lời không dấu cách, kiểm nội dung thực sự gửi, kết quả lỗi thời,
số lượt gen dự kiến và test lưu trữ. **Giữ chính sách duyệt bản mới nhất rồi dọn
ngay bản cũ đủ điều kiện**, không chuyển sang chọn bản bất kỳ hay chờ xóa N ngày.
Vẫn bảo vệ timeline, dùng chung, ghim và ảnh còn được clip đã chọn tham chiếu.

## Thay đổi

- `shared/clip-planning.js`: phần nhiều clip có giới hạn dưới cân đối (tối đa mốc
  3 giây cho mỗi phần), không còn phạt cắt câu 1000 điểm dẫn tới phần 1 giây.
  Cảnh vốn ngắn vẫn giữ ngắn. Trần gen cơ sở vẫn 8 giây, không tự khai model hỗ trợ
  9 giây. Khi không giữ nguyên câu được, chọn điểm ngắt phù hợp và yêu cầu rà lời.
- Cùng một bảng phân đoạn/ký tự dùng cho mốc câu, bộ chia và gán lời. Có ngắt câu,
  dấu phẩy, từ và grapheme Unicode; không coi toàn bộ tiếng Trung là một từ.
  Phụ đề native lấy chính lời của từng phần. Đây vẫn là ước lượng từ chữ, không phải
  canh thời gian theo tiếng nói thực. Có thể phải sửa tay.
- Hộp **Chia clip** hiển thị số lượt gen cho toàn cách chia, chưa trừ clip đã có,
  kèm cảnh báo câu bị chia. Đây không phải báo giá credit hoặc cam kết model tạo
  thời lượng tùy ý. Đuôi tĩnh vẫn chỉ là tùy chọn nhịp không lời tối đa 1,2 giây.
- Fingerprint video mới (`version:2`) gắn với prompt thực tế, lời qua prompt,
  ảnh tham khảo thực sự dùng, ảnh khung và mốc phần; không gắn với ảnh storyboard
  chỉ dùng để viết prompt. Chỉ thay storyboard không làm mất duyệt clip. Áp dụng
  prompt mới thực sự hoặc thay ảnh/lời/mốc vẫn làm clip cần rà/tạo lại.
- Nhận kết quả kiểm lại nội dung/mốc/chuỗi nối. Kết quả lỗi thời giữ ở `staleClips`,
  có lịch sử và link tải trong **Các lượt đã gửi**, không thay ô/bản duyệt/plan.
  Các lượt mới có thứ tự generationOrder lưu từ lúc chuẩn bị, không coi thứ tự
  trả kết quả là thứ tự tạo. Lượt legacy không rõ thứ tự mà đã có ứng viên hiện tại
  được giữ riêng để kiểm tra thay vì tự thay ứng viên.
- Cách chia có clip/job cũ giữ mốc cũ. Signature dạng cũ có đường đối chiếu bảo thủ,
  bỏ khác biệt storyboard nhưng vẫn kiểm nội dung cũ, mốc, ảnh khung và lời từng
  phần. Lời thực tế của lượt cũ được giữ, không tự diễn giải lại theo bộ chia mới.
  Nếu lượt cũ đã chia lời Trung sai, cần sửa lời/tạo lại có chủ ý, không tự gửi AI.
- Kết quả lỗi thời không tự bị xóa bởi thao tác duyệt một ô đang dùng; nó vẫn là
  dữ liệu dự án để đối soát. Thu gọn/xóa dự án dùng chính sách lưu trữ hiện có.
- `check_storage_jobs`: sửa fixture kiểm bản mới nhất/chosen đều được giữ; thêm
  bản giữa đủ điều kiện dọn và latest của phần khác để kiểm đúng hai phía.

## Kiểm chứng

`check_photo_review_fixes` kiểm bằng Chromium + backend/kho file thật, chỉ giả lập
GET kết quả provider: repro nhịp 9 giây; cảnh 2 giây; Việt/Trung/Nhật/Hàn/emoji;
coverage chữ, thời lượng; storyboard-only edit và signature legacy; prompt thay
đổi thực; kết quả nội dung cũ/lượt cũ; giữ bản duyệt/plan/file qua duyệt và reload;
UI số lượt gen; không có POST generation.

Các bài hồi quy: `check_photo_clip_flow`, `check_clip_planning_ui`,
`check_photo_version_approval`, `check_version_approval`, `check_storage_lifecycle`,
`check_storage_jobs`, `check_approval_ui`, `check_library_ack_recovery_ui`.

Không cài model/repo mới, không đổi giới hạn đồng thời. Chưa kiểm generation bằng
tài khoản thật hoặc Windows. Muse vẫn muse.ai, chưa phải Meta AI. Các báo cáo cũ
vẫn mô tả lần chạy cũ; xem `review/PHOTO_REVIEW_FIXES_CHECKS.json` cho đợt này.
