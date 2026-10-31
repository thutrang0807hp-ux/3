# Kiểm tra phiên Flow chạy nền — chưa phải bản sửa node

Công cụ thử riêng khả năng mở **profile web của tài khoản đang chọn trong SceneForge v45** bằng Chrome/Edge chạy nền, rồi kiểm tra danh tính trên trang Flow. Không mở cửa sổ Flow hiển thị. Chỉ đọc trang, không tải ảnh/prompt, không bấm tạo, không dùng credit. Không xuất cookie, email hoặc nội dung phiên ra kết quả. Không cài đè hay sửa mã ứng dụng, không đổi danh sách/lựa chọn tài khoản. Chrome vẫn đọc/ghi profile của chính tài khoản như khi khởi động bình thường.

## Dùng trên máy Windows

1. Giữ tài khoản web đã chọn trong tab Tài khoản. Đóng SceneForge và riêng cửa sổ Flow do app mở nếu có; không cần đóng Chrome/Edge cá nhân.
2. Giải nén toàn bộ ZIP. Chạy **CHAY-KIEM-TRA.bat**. Chọn SceneForge.exe của bản đang cài; theo đường dẫn đã cung cấp là `D:\4\releases\2026.10.28.2\SceneForge.exe`.
3. Chờ kết quả. Công cụ mở thông báo và `KET-QUA.json` bằng Notepad. Chỉ cần gửi lại trường **code**, không gửi dữ liệu tài khoản/profile.

Dùng Python/runtime của bản cài, không cài pip hoặc tải model. Không xóa file khóa profile, không kill trình duyệt, không sao chép cookie sang profile mới. Nếu profile còn được dùng thì dừng. Không tự đăng nhập hoặc xử lý CAPTCHA/xác minh Google.

## Đọc kết quả

- `BACKGROUND_SESSION_OK`: đã đọc được đúng danh tính trong phiên nền. Đây là điều kiện đầu tiên, **chưa chứng minh tạo video nền được**.
- `AUTH_REQUIRED`: phiên nền đến trang đăng nhập Google, chưa dùng lại được đăng nhập trong lần thử này.
- `VERIFICATION_REQUIRED`: cần người dùng xác minh; công cụ dừng.
- `IDENTITY_UNREADABLE`: chưa đọc được danh tính, không tự kết luận đăng nhập còn hay hết.
- `VISIBLE_FLOW_STILL_OPEN`: còn endpoint của cửa sổ Flow, chưa thử mở cùng profile lần nữa.
- `PROFILE_IN_USE_OR_START_FAILED`: profile có thể đang được dùng hoặc browser chưa khởi động được. Không ép đóng/xóa khóa.
- `NO_WEB_ACCOUNT` / `PROFILE_MISSING`: chưa có tài khoản web/profile được chọn hợp lệ.
- `ACCOUNT_MISMATCH`: nick trong profile không khớp; dừng.
- `FLOW_NAVIGATION_FAILED`: chưa tải/đọc được Flow, chưa xác minh phiên.
- `BROWSER_INSTANCE_MISMATCH`: thông tin endpoint lưu không khớp cửa sổ, dừng.
- `INSTALLATION_ERROR`: chưa đọc được cấu hình/runtime; chưa kiểm phiên.

## Giới hạn và kiểm tra

**Công cụ này chưa sửa lỗi trong node v45.** V45 vẫn cần cửa sổ trình duyệt theo cơ chế cũ. Chỉ sau khi có kết quả từ phiên Google thật mới quyết định cách tích hợp bộ chạy nền; không coi một kết quả thử local là đã sửa xong app.

Đã kiểm bằng Chromium headless thật với profile tồn tại và cookie fixture được lưu qua lần đóng/mở lại. Tất cả trang được chặn/thay bằng fixture, DNS ngoài bị chặn; kiểm tra sai nick, thiếu danh tính, xác minh, lỗi điều hướng, nhánh trang đăng nhập, profile đang dùng/endpoint còn sống; danh sách tài khoản không đổi và kết quả không chứa email/cookie. Một số nhánh lỗi dùng mock.

Chưa chạy launcher PowerShell/BAT trên Windows, chưa kiểm phiên Google thật và chưa tạo video thật. Cần chạy trên máy có phiên của người dùng; không yêu cầu tải profile hoặc cookie lên đây.
