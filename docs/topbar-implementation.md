# Thanh trên tab Tạo video · 22/10/2026

Đối chiếu `SceneForge_ThanhTren.zip` (SHA-256 `e085c2c354b61a1d5e93606af9eca7243050ccdff4250725e7ffbe1cd5575179`). Giữ ZIP gốc, Markdown và ảnh trong `design/topbar-received/`. Tên/số trong ảnh là ví dụ, không nạp thành số thật.

## Đã triển khai

- Phòng video mẫu trong app chỉ còn hai dòng: dòng 1 quay lại/chọn phòng, trạng thái lưu thật, nút gạt Tạo video/Dựng, hai viên Flow/Gemini, Hàng chờ, dấu hỏi; dòng 2 Từ video mẫu, bốn chặng tiến độ, dự kiến, Chi tiết. Giữ tên phòng một lần trên thanh trên.
- Khung workflow nhúng bỏ khoảng trống đầu trang và ba thanh nội bộ lặp lại. Node, vị trí kéo, minimap và viewport còn nguyên; không làm phẳng sơ đồ thành ảnh.
- Bốn chặng lấy trạng thái từ workflow hiện tại. Ba chặng đầu bấm để tới node tương ứng; Sang Dựng mở tab editor của cùng phòng, không tự ghi đè hoặc nhập lại timeline. Nhãn Ghép video đổi thành Sang Dựng.
- Menu Chi tiết gộp tài khoản, credit, thời điểm đọc, dự kiến clip, giá ảnh khung, credit đã ghi nhận trong phòng, phí phân tích, đọc lại dữ liệu, Tài khoản và bảng chi phí. Chỉnh đơn giá tham khảo và chuyển Lưới/Danh sách được giữ bên trong menu, thay cho các nút rời.
- Không hiện nút Xem lỗi mẫu trên thanh trên. Tính năng báo lỗi thực trong node vẫn giữ nguyên; mã/dữ liệu minh họa cũ không bị xóa khỏi kho.
- Từ ảnh được ẩn trên thanh của phòng video mẫu ở MVP theo tài liệu. Các phòng từ ảnh, Bộ cảnh mới sửa, dữ liệu/clip cũ và lối mở ở Trang chủ vẫn giữ nguyên. Thanh của phòng từ ảnh không bị ép dùng tiến độ video mẫu.
- Dòng trạng thái lưu lấy trực tiếp từ việc ghi IndexedDB của workflow, gồm đang lưu/đã lưu/lỗi, không suy từ timestamp của phòng. Chuyển sang Dựng đọc trạng thái lưu editor khi có.
- Cả hai dòng giữ chiều cao 56 + 48 px ở desktop/1366 và màn hẹp. Trên màn hẹp cuộn ngang trong từng dòng; không tự xuống thêm dòng hoặc đè canvas. Popup giới hạn chiều rộng/chiều cao theo màn hình, đóng bằng Esc/bấm ngoài/nút đóng.

## Dữ liệu kết nối và chi phí

Đọc metadata từ companion cùng máy qua GET `status`, `ai/providers`, `logs`: một lần khi mở phòng, khi đóng Cài đặt/Tài khoản hoặc bấm Đọc lại. Không gọi model, không gửi yêu cầu tạo clip, không đọc cookie ra UI. Web tĩnh và demo không gửi các GET này và không dùng 860/1.240 credit minh họa của dashboard làm số thật trên thanh.

Flow chỉ xanh khi companion xác nhận động cơ tạo đã nối và có phiên active/ready đang dùng. Credit cần số hữu hạn **và thời điểm đọc**; thiếu một trong hai thì ghi cần đọc credit. Số dư có timestamp nằm trong Chi tiết, không được gọi là số cập nhật liên tục. Lỗi đọc giữ dữ liệu trước và nêu lỗi.

Gemini xanh khi có key và kết quả kiểm danh sách model thành công; tooltip nói rõ chưa kiểm quota/khả năng sinh nội dung. Có key mà chưa kiểm thì vàng; chưa có key dẫn tới Cài đặt AI. Không coi việc lưu key là xác minh thành công.

Credit đã tiêu chỉ cộng các log đúng mã phòng, đơn vị credit và trạng thái done/success; không cộng giá dự kiến của job đang chạy hoặc log phòng khác, không gộp VND với credit. Không có log xác minh thì hiển thị chưa có số đo. Dự kiến dùng đơn giá clip tự nhập và được ghi rõ trong Chi tiết, chưa gồm giá khung/lượt thử lại.

**Giới hạn còn thật:** Flow hiện chưa có adapter đọc quota/credit mới hoặc tạo clip đã kiểm chứng. Nút đọc lại chỉ đọc metadata/nhật ký mà companion đang có; UI nói rõ điều này. Giá ảnh khung và phí phân tích không tự gán 0. Chi phí đầy đủ mở dashboard hiện có. File này không chứng nhận kết nối Flow/Gemini thật đã hoạt động.

## Kiểm tra

- `python scripts/app-shell/check_topbar.py`: hai dòng và canvas sát phía dưới ở 1920/1366/760; số lưu/phòng hiện tại; popup, Esc, Lưới/Danh sách, AI settings, help, queue, editor navigation; bảo toàn cảnh và reload phòng; không gọi API trong demo.
- Fixture kiểm riêng credit có/không timestamp, trạng thái xanh/vàng và chỉ cộng log hoàn tất đúng phòng. Đây là dữ liệu kiểm thử trong bộ nhớ, không phải credit thật.
- `python scripts/app-shell/check_workflow_navigation.py`: từ Trang chủ vẫn mở phòng từ ảnh; quay lại giữ chỉnh sửa, đủ node không chồng, legacy script/frame/clip Blob còn nguyên. Bài thử cập nhật lối mở phù hợp việc ẩn shortcut B2 trong MVP.
- `python scripts/app-shell/check_showcase.py`: demo riêng, project/timeline có thể mở, dữ liệu làm việc không bị ghi đè, không gửi API.
- `PYTHONPATH=/tmp/sceneforge-cpu-deps python scripts/app-shell/check_package6.py`: kiểm hồi quy gallery, hàng phân tích và sản phẩm.

Chỉ kiểm giao diện/logic trên Chromium Linux; chưa chứng nhận phiên và credit nhà cung cấp thật.
