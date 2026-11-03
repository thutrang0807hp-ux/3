# SceneForge v46.62 — sửa nút tạo bị khóa bởi lịch sử cũ

Đóng app, chạy `SceneForge-Update-20261104-v46.62-Create-Button-Fix.exe`, mở lại. Cập nhật trên .60/.61, khoảng 4 MB; giữ nguyên CLI, runtime và tài khoản.

- Cửa sổ clip tự đọc trạng thái các lượt cũ bằng API chỉ đọc. Lượt đúng mã/kho/phòng/cảnh/phần được backend xác nhận submitted=false và failed/not_submitted sẽ tự mở khóa.
- Nếu lịch sử cũ là lý do duy nhất gây chặn, nút có thể bấm và ghi Kiểm tra lượt cũ rồi tạo video. Không còn cảnh báo không có đường xử lý.
- Nếu kết quả cũ vẫn chưa rõ, có nút đọc lại, xem lịch sử và xác nhận đã kiểm tra ngay trong cửa sổ. Chưa có xác nhận thì không tự gửi. Bấm hủy không tạo gì.
- Giữ lịch sử và ID cũ; khi người dùng xác nhận tạo mới thì dùng đúng một ID mới. Bản ghi kho khác/cảnh khác hoặc không tìm thấy không được tự coi là chưa gửi.
- Giữ các điều kiện khung/prompt/tài khoản/cấu hình, kiểm tra chữ ký và lưu ý định trước khi gửi. Không đổi CLI/session hay tự tạo lại.

Kiểm tra đúng HTML lấy từ EXE bằng Chromium: tái hiện clip 4.2 giây với lịch sử schema cũ; receipt chưa gửi mở khóa tự động và không POST; unknown/sai cảnh vẫn giữ; hủy xác nhận không POST; xác nhận đối soát giữ lịch sử; sau đó tạo đúng một mã mới và nhận clip. Các kiểm tra tạo toàn bộ, a/b, không vẽ lại canvas, cấu hình và tải phục hồi vẫn qua. Fixture cục bộ; chưa xác minh Flow thật/bộ cài Windows.

SHA256: `f5d7e96f7767ab2122775edff295ab6c3aeae6b669da2ecec6eaacb7001ae7a8`
