# SceneForge v46.40 — bộ quan sát mạng thụ động

Đây là bản thu bằng chứng, chưa phải bản sửa hoàn tất theo dõi/nhận video.

1. Đóng SceneForge, chạy SceneForge-Update-20261102-v46.40-Network-Probe.exe và chọn thư mục có SceneForge.exe cùng install-settings.json. Yêu cầu v46.7 trở lên.
2. Giữ video cũ trên Flow. Nếu bị unknown chặn, chỉ dùng xác nhận đã giữ video khi bạn thực sự đã kiểm tra và lưu các video cũ đó. Không tạo lại chúng để lấy log.
3. Khi cần làm một video mới, chuẩn bị ảnh + prompt và bấm Tạo 1 video như hiện tại. Probe tự bật trước đúng một click Generate hiện có; không gọi API tạo hay retry.
4. Tải báo cáo theo dõi video của lượt mới đó, hoặc dùng Kiểm tra video cũ sau khi dừng. Gửi JSON trong chat. Trường network_probe ghi thời gian tương đối, endpoint đã lọc, HTTP status, ID/trạng thái/tiến độ ứng viên nếu JSON có trả. Có dữ liệu HTTP lỗi 4xx/5xx.
5. Nếu Dừng, log được đóng và giữ trong Data/flow-results/<request_id>.network.json. Probe không đổi unknown hoặc tự nhập video.

Không có log lúc gửi cho lượt tạo trước bản .40. Thiếu response ứng viên sau 15 giây chỉ cảnh báo; tiếp tục quan sát tối đa 10 phút từ lúc bật, không kết luận tạo thất bại. Dữ liệu ứng viên chưa chứng minh liên kết tác vụ; association_confirmed luôn false.

Log không xuất body thô, prompt thô, cookie, header xác thực, query string hoặc media URL. JSON không có Content-Length được kiểm tra kích thước sau khi đọc, không phải RAM cap cứng. Giới hạn 300 request, 75 tóm tắt nền, 8 tác vụ thu thập, JSON 2 MiB và facts xuất tối đa 4 MiB. Các phần bị bỏ do giới hạn có cảnh báo.

Giữ đường upload/gắn ảnh/prompt .33 và luồng gửi một lần. Đã kiểm tra Chromium + HTTP fixture + ledger, bao gồm Dừng và xuất log, không dùng Google thật hoặc credit. Chưa xác minh schema Flow thật hay chạy installer Windows.
