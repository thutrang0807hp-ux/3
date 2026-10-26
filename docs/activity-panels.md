# Thông báo & Hàng chờ — 27/10/2026

## Tương tác
- Bấm chuông mở Thông báo, bấm lại đóng. Ô Hàng chờ và nút Hàng chờ trong phòng cũng bật/tắt. Bảng mở cạnh nút, cuộn trong, giới hạn chiều cao; không dùng modal che nút chuông.
- Hai bảng loại trừ nhau. Nút ×, Esc, bấm ngoài và chuyển trang đóng bảng. Nút mở có aria-expanded/aria-controls; Esc/× trả focus. Không hủy, dừng tác vụ hoặc đánh dấu đọc khi mở/đóng.
- Thông báo giữ lọc Tất cả/Cần bạn/Xong việc. Đánh dấu từng mục/tất cả và mở phòng ghi read thật vào IndexedDB; chỉ thao tác rõ ràng mới đánh dấu đọc. Bản >30 ngày bị ẩn theo quy tắc hiện có, không thêm xóa thông báo lúc mở bảng.

## Hàng chờ
- Theo nguồn / Theo video / Xong gần đây (24h, tối đa 40 mục hiển thị). Nguồn gập được, giữ trạng thái gập khi cập nhật. Nguồn chưa có công việc gộp dưới; không báo đã đăng nhập từ việc engine được cài.
- Gom jobs của shell, bản mới nhất của slot Batch chưa đóng, localRecovery CPU/FFmpeg và generation_job từ lifecycle/status. Khử trùng theo request ID đã biết. Đọc lại 12 giây khi bảng mở; bản demo không gọi API. Backend hiện giới hạn tối đa 1000 generation job còn theo dõi; không hứa lịch sử hoàn tất của mọi provider đầy đủ.
- Phần trăm chỉ dùng progress hữu hạn 0–100 đã có; Batch simulation có tiến độ riêng, job online Batch không lấy progress=1 giả làm tiến độ provider. Không tạo ETA. Vòng tiến độ chung chỉ có % nếu mọi job đang chạy đều có dữ liệu; thiếu thì vòng không xác định, không hiện số %.
- Ô trái: số việc chờ/chạy, Rảnh khi trống, chấm đỏ khi có việc cần xem. Lỗi/chưa rõ không tự gửi lại. Batch đã gửi có Kiểm tra kết quả; job provider trong kho có Đối soát; job legacy mở phòng; CPU paused mở để tiếp tục bằng luồng cũ.
- Tạm dừng chỉ đổi prefs.paused và batchState.paused cho hàng đợi app/Batch; không hủy request đã gửi, không dừng CPU/FFmpeg hoặc các workflow đang tự điều phối trong iframe. Không thêm endpoint pause toàn bộ nguồn online. Làn legacy Flow dùng chung cờ ảnh/clip, không giả có hai worker độc lập.
- Giữ node queueList cũ và listener hủy/ưu tiên/kéo thứ tự legacy, tải/mở kết quả CPU. Batch hoặc job đã gửi không bị gán cơ chế kéo thứ tự giả. Giới hạn song song hiển thị từ Batch; chưa làm dropdown thay giới hạn từng provider trong popover.
- Không thay model, tài khoản, engine gửi hoặc cơ chế ledger. Cài đặt nguồn dẫn vào màn đang có; Gemini API dẫn vào AI/key.

## Kiểm thử
7 bài đạt: toggle kép, loại trừ hai bảng, ngoài/Esc/×, không tự đọc hoặc dừng job; đánh dấu đọc lưu thật; không dựng progress; nhóm/gập giữ trạng thái; mobile không tràn. Server + SQLite thật đưa job submitted vào đúng Flow lane và đối soát được khi phòng không còn; không gửi generation POST. Hồi quy Batch ZIP/ghim/đóng, nguồn-tài khoản-token, Settings, lưu trữ-khu chờ và hai workflow.
Bài Settings từng truy cập DB trước app boot; sửa fixture chờ appBootReady, giữ log đầu. Chưa kiểm gen bằng tài khoản online hoặc Windows.

Code: scripts/app-shell/activity-panels.js/.css, nạp sau batch-redesign.js. Tái sử dụng notification store, queueList listener, recovery.js và lifecycle/status; không thêm backend xóa/chạy job.
