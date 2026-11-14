# SceneForge .124 — ưu tiên nguồn phát TikTok

Đóng SceneForge, chạy **SceneForge-Update-20261112-v46.124-TikTok-Playback.exe**, chọn đúng thư mục app rồi mở lại. Nhận từ .62 trở lên, gồm .119–.123.

Dán link TikTok và bấm Tải và nhập như trước. App ưu tiên nguồn phát `play`/`play_addr` hoặc nguồn được metadata khai báo không watermark, thay vì chọn bản tải được ghi rõ có watermark chỉ vì nó có độ phân giải cao hơn. Nguồn phát tách hình/tiếng vẫn dùng đường ghép đã có. Giới hạn 1080p tính đúng cho cả video ngang 1920×1080 và dọc 1080×1920, tránh loại nhầm video TikTok dọc. Link đã nhập trước khi có tính năng này được kiểm tra nguồn lại; không sửa đè video/dự án cũ nếu byte video khác.

Nếu chỉ tìm được nguồn bị đánh dấu watermark hoặc không xác định được tình trạng, app có thông báo rõ sau khi nhập và lưu thông tin nguồn cùng phòng. Vẫn giữ đường tải bản gốc để không làm mất khả năng nhập video.

Đây là **chọn bản nguồn**, không phải dùng AI/bôi/cắt hình để xóa logo. Không khẳng định đã kiểm tra từng khung hình. Logo/tên kênh được ghép sẵn vào nội dung gốc vẫn có thể còn. Công cụ `watermark/engine.js` trong repo là Gemini watermark remover, không được áp sang TikTok.

Đã kiểm bằng metadata mô phỏng theo mã nguồn yt-dlp và MP4/FFprobe thật: nguồn phát 720p thắng bản watermark 1080p; nguồn phát thiếu codec/tách tiếng được ưu tiên; khi chỉ có bản watermark thì cảnh báo rõ; nguồn khác giữ luật cũ; byte tải nguồn hoàn chỉnh không bị thay đổi. UI Chromium xác minh thông tin nguồn và cảnh báo được lưu, link cũ được xét lại. Chưa tải thử link TikTok thật hoặc chạy bộ cài Windows.
