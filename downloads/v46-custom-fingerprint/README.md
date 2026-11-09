# SceneForge .94 — Fingerprint thiết bị tùy chỉnh, có thể tắt

Đóng SceneForge rồi cập nhật trên .93.

Cài đặt → Tài khoản → Fingerprint → chọn thông số → Bật → Lưu. Đóng cửa sổ profile và đợi tác vụ xong trước khi lưu; mở lại bằng Mở phiên để áp dụng. Nếu chưa có profile, đăng nhập web/lưu hoặc Mở phiên trước.

- Mặc định tắt; không đổi nhận diện của tài khoản cũ khi chỉ cài cập nhật.
- Thông số hỗ trợ: navigator.hardwareConcurrency 4/8/12/16; navigator.deviceMemory 4/8/16 GB; screen/viewport 1280×800, 1366×768 hoặc 1440×900. Các giá trị là override JavaScript/browser viewport, không đổi phần cứng thật hoặc gói cài.
- Lưu cấu hình/seed vào profile, ghi nguyên tử. Mã cấu hình là mã quản lý cục bộ; không phải mã fingerprint do website cấp, không đảm bảo cấu hình của hai profile khác nhau sẽ có fingerprint web khác nhau nếu chọn cùng thông số.
- Script vào trước điều hướng trang đăng nhập khi bật; browser kiểm/chạy Grok/ChatGPT/Meta dùng cùng cấu hình. Flow native và luồng nền dùng cấu hình của profile. Gemini/Muse SDK tiếp tục cơ chế riêng; không tuyên bố SDK phát ra fingerprint trình duyệt này.
- Giữ User-Agent, client hints, hệ điều hành, timezone, ngôn ngữ, Canvas, WebGL, audio và webdriver. Không có cơ chế ẩn automation hoặc vượt CAPTCHA/xác minh. Đây không phải bộ anti-detect hoàn chỉnh.
- Bật/tắt không xóa cookie, profile hoặc phiên vault. Thay thông số có thể khiến dịch vụ yêu cầu đăng nhập/xác minh; không bảo đảm giữ đăng nhập lâu hơn.
- API chỉ cho trường/giá trị được hỗ trợ; không nhận script, đường dẫn hoặc user-agent tùy ý. Không trả seed qua API. Chặn đổi khi profile đang mở, có tác vụ hoặc endpoint native của profile còn sống. Đường đăng nhập mặc định khi tắt giữ như .93.

Kiểm tra: Chromium thật trên fixture được fulfill cục bộ; giá trị đầu document, giữ cấu hình qua restart, off không còn override, cookies còn nguyên, API validation/busy guard, native startup và Flow background áp dụng trước trang. Regression profile persistence và UI đăng nhập/fingerprint đã qua. Chưa dùng tài khoản dịch vụ thật, chưa chạy cửa sổ headed hay trình cài Windows.

SHA-256: 5bdc9f08294941457da456be6599b70bb314d64b36be0c99d604c697b4a7b15a
