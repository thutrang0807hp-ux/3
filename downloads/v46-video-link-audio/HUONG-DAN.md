# SceneForge .119 — nhập link có hình và tiếng tách riêng

Đóng SceneForge, chạy **SceneForge-Update-20261112-v46.119-Video-Link-Audio.exe**, chọn thư mục đang chạy ứng dụng, rồi mở lại và dùng **Nhập video mẫu → dán link → Tải và nhập**.

Yêu cầu đã có .62 trở lên và động cơ FFmpeg/ffprobe, yt-dlp. Bản cập nhật chỉ thay `app/local_engine/video_import.py`, không thay UI, Flow, tài khoản hoặc dự án.

Khi nguồn có luồng HTTP hình và tiếng riêng, app tự tải cả hai, ghép cục bộ bằng FFmpeg, kiểm tra video có âm thanh rồi đưa vào luồng nhập hiện có. Nguồn có tệp đầy đủ được ưu tiên giữ cách tải cũ. Tổng dữ liệu nguồn tối đa 500 MB; kết quả tối đa 500 MB, 10 phút. Cần khoảng 1,3 GB trống vì tệp nguồn và kết quả có lúc cùng tồn tại. Hủy hoặc thất bại sẽ dọn các tệp tạm của lượt đó.

Chưa hỗ trợ tải danh sách phát phân mảnh HLS/DASH khi không có URL HTTP của từng luồng hoàn chỉnh; không dùng cookie đăng nhập. Không bảo đảm mọi link YouTube đều tải được: còn phụ thuộc quyền truy cập và trình trích xuất yt-dlp.

Đã kiểm tra: FFmpeg/ffprobe thật với luồng MP4 không tiếng và M4A riêng, tải HTTP mô phỏng, kết quả có cả hình và tiếng, giữ đường tải MP4 trực tiếp, giới hạn dung lượng tổng, lỗi luồng tiếng và hủy dọn tệp. Payload EXE được đọc lại để xác minh mã nguồn/hash. Chưa chạy bộ cài Windows hoặc tải link YouTube thật trong môi trường này.
