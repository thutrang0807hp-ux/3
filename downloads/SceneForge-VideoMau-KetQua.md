# Kết quả kiểm và chỗ chưa chắc

## Đã kiểm

- CPU thực: file binary 200 MiB → proxy → mốc/ảnh; SHA nguồn không đổi, file tạm được dọn. Video kiểm tổng hợp 0,5 giây được padding hợp chuẩn MP4, chỉ chứng minh đường nhận dung lượng, không phải benchmark video dài HD.
- Whisper thực qua API local, có lời và mốc từ. VieNeu thực tạo WAV rồi Whisper nghe WAV qua endpoint mới; có sai từ nên vẫn cần rà.
- PySceneDetect/OpenCV/RapidOCR thực trên dữ liệu kiểm tổng hợp; FFmpeg timeline xuất MP4 thực, kiểm khung và âm thanh.
- Chromium fixture xuyên UI: prompt ảnh → duyệt frame → prompt video; nhận file vào đúng cảnh; giọng/caption không đổi lời nguồn; mute/voice payload sang Dựng; CPU binary và không dò cảnh hai lượt.
- Tài khoản: fixture kiểm Cài đặt điều khiển dispatch, ID Flow ghim ở wrapper, review cũ bị chặn, mỗi job có ID riêng, cùng một tài khoản có slot đồng thời và hàng đợi, không gửi lại unknown.
- Endpoint thật của app + provider transport giả: phân tích/dịch/viết và JSON/ID validation. Không chuyển ngầm sang API trả phí.

## Sửa phát hiện trong lần rà này

R1: pipeline tự động trước đây chỉ nhìn cờ file model Whisper. Đã đổi để chỉ bật transcribe khi cả thư viện Whisper và model đều có; thiếu thư viện vẫn đo cảnh được và không gửi yêu cầu chép lời chắc chắn lỗi. Chromium fixture kiểm tình huống có model nhưng thiếu thư viện: binary upload gửi transcribe=false.

## Đợt reliability tiếp theo

Đã triển khai biên nhận chưa gửi, phục hồi từng job, sửa JSON, batch 8 cảnh, evidence nguồn rõ hơn, Flow/Muse journal và đối soát, ACK thành phẩm, cache bộ cài. Xem `docs/reference-reliability-update.md` để đối chiếu từng P0/P1/P2, phép thử và phần chưa làm. Không tự nâng model/slot Gemini.

## Lưu trữ v2 — 26/10/2026

Xem `docs/storage-lifecycle-v2.md` và `review/STORAGE_LIFECYCLE_CHECKS.json`: ba thao tác dọn/xóa, lease, quarantine, release/deleted, restore, registry kết quả và giới hạn đã được bổ sung. Những giới hạn còn được nêu riêng; không chứng nhận Windows/online.

## Chưa thể kết luận hoàn toàn liên thông trên dịch vụ thật

1. Chưa có account thật cho một vòng Gemini → ảnh → Flow/Muse → clip. SDK import/fixture không chứng minh phiên/credit/captcha/quyền model thật hoạt động.
2. Muse SDK hiện trỏ muse.ai. Chưa xác nhận đúng Meta AI người dùng muốn; đây là khoảng trống cần chốt, không phải đã nối mọi Meta account.
3. Chia clip còn theo khoảng 8 giây, chưa đọc duration của mọi model. Native speech/giọng/continuity và thời lượng sinh thật cần rà.
4. Camera được đo bằng optical flow/RANSAC. Hành động tay/người chưa có model local hiểu toàn bộ chuỗi; Gemini dựa ảnh mẫu/lời, có thể thiếu hành động giữa ảnh.
5. Phụ đề là ASR có mốc, chưa forced alignment theo câu chuẩn. Nhận dạng có lỗi. Giọng riêng có thể dài hơn hình, cần chỉnh trong Dựng; hạ tiếng clip là gain cố định 15%, không tự duck theo khoảng thoại.
6. Kho Kịch bản tự rút khung nhịp từ mốc; không mặc nhiên có đủ lời quảng cáo hoặc cập nhật lại mọi nội dung khi mốc không đổi.
7. Lưu trữ v2 đã gom kết quả mới được quản lý vào kho hash và ánh xạ URL cũ; không suy thành đã dọn mọi file backend cũ. File legacy chưa đủ liên kết được giữ; preview/gốc, browser và bản xuất ngoài app vẫn có thể chiếm dung lượng riêng. Xem báo cáo storage-v2.
8. Các bài Chromium có đường dẫn Linux. Bộ cài BAT có trong gói nhưng chưa chạy thử Windows. Codec nhập còn phụ thuộc trình duyệt/FFmpeg.

Các kết quả real-model đi kèm từ môi trường phát triển với đường dẫn model đã cấu hình. Gói review không chứa các model/venv đó. Trước khi thử account thật, đọc `THU_BANG_TAI_KHOAN_THAT.md`.
