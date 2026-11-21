# SceneForge .133 — đăng nhập Flow

Sửa nút mở tài khoản Flow cũ: trước đây cổng Chrome còn hoạt động đã được coi là mở phiên thành công, kể cả tab Google đang từ chối đăng nhập. Nay app theo dõi và kiểm tra phiên, giữ đúng profile tài khoản vừa chọn; trang từ chối không được nhận là đăng nhập thành công.

Khi chưa có cửa sổ điều khiển đang mở, Flow đăng nhập bằng Chrome/Edge thường trên profile riêng đã có, chưa bật điều khiển tự động lúc nhập tài khoản. Sau khi vào được Flow, đóng cửa sổ đó; app mở lại cùng profile để kiểm tra. Nếu cửa sổ cũ đang ở trang từ chối, đóng cửa sổ do app mở rồi thử lại. Không xóa cookie, Data hay tài khoản. Không cần đóng Chrome cá nhân.

Cách dùng: đóng SceneForge và cửa sổ đăng nhập cũ do app mở, chạy cập nhật .133, mở lại Cài đặt → tài khoản Flow → mở phiên. Đăng nhập xong và vào được Flow thì đóng cửa sổ đăng nhập, chờ app kiểm tra phiên.

Bản .132 áp dụng cách đăng nhập thường cho Gemini; .133 bổ sung Flow. Chưa có bằng chứng CAPTCHA/cache gây ra Google từ chối. Thay đổi này sửa đường đăng nhập và xác minh trong app, không bảo đảm Google luôn chấp nhận.

Đã kiểm thử logic profile/tài khoản, thứ tự đăng nhập trước điều khiển sau, không nhận trang từ chối, giao diện Flow và hồi quy Gemini bằng mô phỏng/Chromium. Gói đã kiểm tra nội dung nhúng và hash. Chưa thử tài khoản Google thật hoặc trình cài Windows.

Cập nhật cộng dồn từ .62 trở lên, giữ thay đổi đến .132. Không chứa dữ liệu tài khoản hoặc model.
