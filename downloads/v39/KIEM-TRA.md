# Kiểm tra SceneForge v38 và bản sửa v39

Ngày 30/10/2026. Không có đăng nhập hoặc tạo video trên Google thật trong lần kiểm tra này.

## Lỗi tìm thấy và sửa

1. ContextVar truyền sang tác vụ con cho phép dùng phiên worker mà không qua hàng đợi. Đã tái hiện bằng test thất bại trên v38; v39 ràng buộc phiên với đúng tác vụ và đúng đối tượng driver.
2. Xóa tài khoản chưa ngắt ngay kết nối worker đang nhàn rỗi. V39 giải phóng worker khi xóa tài khoản, giữ nguyên Chrome và profile trên đĩa.

## Kiểm tra đạt

- check_flow_managed_workers: tái sử dụng kết nối, khóa hàng đợi cùng tài khoản, tách tài khoản, chặn tác vụ con/driver khác, hủy tác vụ, xóa tài khoản và shutdown.
- check_flow_managed_browser: Chromium thật, toàn bộ trang mạng được thay bằng fixture; hai request khác nhau tạo hai kết quả liên tiếp qua cùng kết nối; request ID trùng không gửi lại; ảnh + prompt, download/hash/ffprobe; đổi project/tài khoản dừng; Google rejection fixture dừng.
- check_flow_extension: pairing/relay/DOM, không cookie, gửi một lần, model không nhận diện dừng, kết quả chưa rõ chặn gửi lại, đối soát đúng request ID.
- check_flow_video_summary: chọn 9:16, x1, nhận 8 giây từ summary; từ chối 6 giây hoặc x1 không đổi.
- check_flow_activity_card: phát hiện thẻ hoạt động bất thường, không bấm Retry.
- check_flow_browser_probe: instance/cổng CDP đúng, cổng cũ/khác instance bị từ chối.
- check_flow_login_start_race, check_flow_login_connection_failure, check_flow_web_auto: chống mở trùng, báo lỗi kết nối đúng và kiểm tra nhập tài khoản bằng fixture.
- Payload: đối chiếu SHA256 từng file, ZIP toàn vẹn, compile toàn bộ Python, kiểm tra tài nguyên ZIP nhúng trong EXE khi build.

## Chưa đạt / chưa xác minh

Không có bản sửa Google từ chối đăng nhập. Không có video thật tạo từ SceneForge trên Windows được xác minh. Chưa chạy updater trên Windows. Chưa kiểm thử runtime Playwright 1.64.1 thực tế của người dùng. Vẫn dùng Playwright/DOM, chưa chuyển toàn bộ Puppeteer/API như Phoma.

V39 sửa worker; không được coi là bản sửa lỗi đăng nhập. Không cần thử đăng nhập lại chỉ vì bản này.
