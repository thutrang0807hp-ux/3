# Kiểm tra đăng nhập và sửa chọn tab — v40

Đã rà các điểm mở trình duyệt/đăng nhập trong SceneForge, windows_bootstrap và so sánh mã Phoma, gflow-cli, google-flow-mcp, seosona-flow đã tải trong workspace. Đây là kiểm tra mã cục bộ; không phải xác minh toàn bộ GitHub hay lần đăng nhập Google trực tiếp.

Lỗi tái hiện trên nguồn v39 đã phát hành: một tab accounts.google.com/signin/rejected cũ được quét trước tab Flow hợp lệ làm watcher kết luận Google từ chối ngay. V40 chọn duy nhất một tab Flow, theo dõi tab đó qua chuyển trang và popup Google có opener tương ứng. Tab lỗi cũ không liên quan không quyết định trạng thái lượt hiện tại. Nhiều tab Flow hoặc tab mục tiêu bị đóng thì dừng và yêu cầu chọn rõ, không tự nhận tài khoản đầu tiên.

Kiểm tra đạt: check_flow_login_tabs (gồm watcher thật với mock transport), check_flow_web_auto, check_flow_login_connection_failure, check_flow_login_start_race, check_flow_managed_browser (Chromium thật, toàn bộ URL thay bằng fixture; tab rejected cũ mở trước tab Flow, hai lượt video mô phỏng liên tiếp qua worker, không gửi trùng, đổi tài khoản/project dừng). Đã chạy test hồi quy trên mã v39 và tái hiện lỗi, sau đó bản mới đạt. Payload ZIP, SHA256 từng file và compile Python đạt.

Giới hạn: không thay đổi cơ chế Google xác thực. Nếu Google thực sự từ chối tab của lượt hiện tại thì vẫn không đăng nhập được. Không có chứng cứ lỗi tab cũ là nguyên nhân duy nhất trên máy người dùng. Không giả nhận diện trình duyệt, không đọc/copy cookie từ Phoma, không thay runtime. Không khẳng định đã sửa việc Google từ chối đăng nhập hoặc đã tạo video thật trên Windows.
