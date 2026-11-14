# SceneForge .123 — kiểm tra tệp khi nguồn thiếu codec

Đóng SceneForge, chạy **SceneForge-Update-20261112-v46.123-Video-Source-Metadata.exe**, chọn đúng thư mục app rồi mở lại. Bản gộp nhận từ .62 trở lên, gồm các sửa lỗi .119–.122.

Bộ lọc trước đó loại tệp HTTP nếu công cụ trích xuất không ghi đủ codec hình/tiếng hoặc protocol, dù tệp có thể là MP4 bình thường. .123 giữ các định dạng đầy đủ/luồng riêng như trước, rồi mới thử định dạng HTTP chưa đủ metadata và kiểm tra nội dung tải về bằng FFprobe. Không tự xem metadata thiếu là bằng chứng nguồn cần đăng nhập.

Thử lại **Nhập video mẫu → dán link TikTok → Tải và nhập**. Nếu vẫn lỗi, bấm **Tải báo cáo nguồn video** và gửi JSON. Báo cáo gồm tên trình trích xuất, số định dạng, protocol và codec, không chứa URL CDN, cookie hay header đăng nhập.

Không hỗ trợ thêm playlist phân mảnh HLS/DASH, video riêng tư hoặc yêu cầu đăng nhập. Nguồn không có tệp HTTP phù hợp vẫn có thể thất bại. Chưa kiểm chứng trực tiếp link TikTok trong ảnh của người dùng; bản này sửa một trường hợp loại nhầm trong mã và thêm bằng chứng để xác định các trường hợp khác.

Đã kiểm bằng FFmpeg/FFprobe thật và HTTP mô phỏng: thiếu codec hình/tiếng/cả hai hoặc protocol vẫn nhận MP4 có tiếng; audio-only/manifest/DRM và HTML giả video bị từ chối; đường tải hai luồng và giới hạn dung lượng/dọn tệp cũ giữ nguyên. UI Chromium kiểm tra lỗi và xuất báo cáo không kèm URL/cookie ngoài phạm vi. Chưa chạy bộ cài Windows.
