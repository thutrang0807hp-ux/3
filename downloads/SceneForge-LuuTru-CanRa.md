# Điểm cần mang đi rà

1. Thu gọn xóa file trung gian nào thực sự trên ổ? Phân biệt IndexedDB, kho hash, schema/metadata backups, results Flow/Muse/Gemini và bản mirror ngoài app. Không mặc định estimated bytes = freed bytes.
2. `archiveTaskGuard` nhìn shell jobs/activeWorkers. Cần đối chiếu thêm cloudJobs, referencePromptJobs, analysis.aiRequest/batches của workflow mới, cả planned/unknown/missing/done chưa import; chưa có kiểm thử chứng minh chặn thu gọn đầy đủ cho mọi trạng thái đó. Đây là điểm rà bổ sung, không tự sửa trong gói bàn giao.
3. Shared refs theo key/hash có bảo vệ đủ assets nằm trong workflow/editor của phòng khác? Kiểm cả Thùng rác, pin và backups; dữ liệu giữ trong backup có thể khiến không dọn được dung lượng như dự tính.
4. Cross-DB journal/lease/checkpoint: thử crash/quota ở từng pha. ACK xuất hiện mới xác nhận Blob+room ghi browser; checkpoint xuống SQLite/mirror là các tầng tiếp theo, chưa có giao thức ACK end-to-end cho mọi tầng.
5. Thu gọn final-only giữ kịch bản/prompt nhưng bỏ timeline chỉnh sửa đầy đủ. Kiểm restore/new-room/các phiên bản và bản chữ nào được giữ thật, đặc biệt fields mới bổ sung.
6. Lịch chỉ xét khi app mở; mặc định tắt, hash thành phẩm phải khớp, ghim và mở lại chỉnh thì dừng. Có đồng bộ đầy đủ khi thay export/restore/đổi thư mục dữ liệu không?
7. RAM khác dung lượng đĩa: encode/hash/equalBlob và journal có thể materialize Blob/arrayBuffer/copy. Chưa có benchmark RAM với 10 dự án thật hoặc video lớn. Không dùng 200MB upload fixture làm bằng chứng mức RAM thu gọn.
8. Chưa triển khai thu hồi đồng bộ results Flow/Muse/Gemini. Đừng nối lệnh xóa chỉ dựa tuổi file; phải bảo vệ live jobs, unknown requests, các phiên bản và timeline.
9. `scripts/app-shell/check_photo_archive_lifecycle.py` hiện timeout ở bước Storyboard trước phần thu gọn (`#photoChatPrompt`); không tính phần sau đó là đã chạy. `check_archive_local` độc lập đã kiểm journal/lịch/giữ thành phẩm trên SQLite thật.
10. `scripts/app-shell/check_home_archive.py` là bài cũ đang timeout tại selector layout `#board [data-room]`; không ghi PASS. Có các bài tập trung lifecycle/backend riêng trong TEST_RESULTS.

Đây là snapshot phục vụ đánh giá. Không có tài khoản online/Windows E2E trong gói; không tự chạy AI hay tự dọn dữ liệu khi giải nén.
