# Nguồn phòng & bản đồ chung · 28/10/2026

Bảng nguồn dùng thẻ, tách nguồn tạo ảnh khỏi nguồn phân tích/viết. Phòng ảnh hỗ trợ chọn Gemini Chat / Muse thủ công cho storyboard và Flow / Muse cho video theo các adapter đã có. Không thêm đường tạo storyboard Flow hoặc Gemini API khi chưa có backend tương ứng. Video mẫu hiện giữ Gemini Chat cho ảnh khung, Flow mặc định cho video; lựa chọn phân tích dùng chung trong Cài đặt được ghi riêng. Không gán giá/model theo hình minh họa.

Lựa chọn ảnh/video của phòng ảnh là bản nháp trong bảng; Xong mới lưu. Đóng bằng viên nguồn, ×, Esc, bấm ngoài hoặc đổi phòng bỏ bản nháp. Việc đã gửi giữ receipt và nguồn cũ. Chặn đổi khi workflow bận theo kiểm tra hiện có. Báo lỗi lưu ngay trong bảng; không âm thầm lưu khi đóng. Trạng thái chỉ dựa trên cấu hình/lựa chọn tài khoản đã đọc; Flow còn cần account_binding. Chưa có kết quả đọc thì Chưa kiểm tra, không suy ra đăng nhập từ key API. Kết nối không có nghĩa là đã xác minh quota/tạo nội dung.

Các công cụ Tiến độ, Chi phí, phạm vi Chạy tự động, Hướng dẫn chuyển sang nút … độc lập. Chạy tự động vẫn dùng hành động có phạm vi đã được giới hạn trước; không thay preflight, không tự duyệt, không tự đổi nguồn.

Hai canvas dùng chung renderer bản đồ: nền tối, ô node theo vị trí/kích thước DOM thật và khung vùng nhìn. Bấm để định tâm, kéo khung giữ điểm bám, bàn phím mũi tên di chuyển vùng nhìn. Theo dõi resize viewport/node và bỏ theo dõi node đã bị thay để không giữ DOM cũ. Không đổi layout, prompt, clip hoặc luồng duyệt bản ghép của ảnh tĩnh.

Kiểm: `python scripts/app-shell/check_workspace_shell.py`. Chromium kiểm hủy/lưu nguồn, giữ beats/jobs, đóng/mở bảng/menu, lưới bản đồ và kéo/resize, hai phòng riêng, mobile không tràn, không có generation POST. Không đăng nhập hoặc tạo nội dung bằng tài khoản thật.
