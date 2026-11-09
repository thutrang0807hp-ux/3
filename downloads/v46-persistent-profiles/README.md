# SceneForge .93 — Profile riêng và nhận diện trình duyệt ổn định

Đóng SceneForge và cửa sổ đăng nhập do app mở, rồi cập nhật trên .92. Không cần đóng trình duyệt cá nhân.

## Cách dùng

Cài đặt → Tài khoản → Mở phiên ở dòng đã lưu. Thêm tài khoản mới vẫn dùng Đăng nhập trên web. Tài khoản cũ có thể cần đăng nhập một lần nếu cookie không còn hiệu lực. Bấm Lưu phiên sau đăng nhập. Chi tiết hiển thị mã profile ngắn; sơ đồ, nút Gỡ và kiểm tra phiên được giữ.

## Phạm vi

- Gemini Chat/Muse: profile đăng nhập riêng được giữ trên ổ, mở lại theo tài khoản; thử khôi phục cookie từ vault khi mở tài khoản cũ. SDK vẫn kiểm và làm mới phiên qua luồng cũ, không giả định SDK dùng toàn bộ fingerprint của trình duyệt.
- Grok/ChatGPT/Meta: đăng nhập, kiểm phiên và công việc dùng cùng profile riêng. Khôi phục cookie phiên còn thiếu từ snapshot mã hóa; không đè cookie mới trong trình duyệt bằng snapshot cũ. localStorage được giữ. Các lượt của cùng profile dùng lần lượt để tránh mở một profile hai lần; tài khoản khác vẫn độc lập.
- Flow: giữ profile hiện có, lưu lựa chọn trình duyệt và cỡ cửa sổ; Mở phiên mở đúng binding tài khoản, không tự đổi tài khoản đang chọn.
- Ổn định nhận diện bằng trình duyệt thực đã chọn, profile và viewport/cửa sổ 1280×800. ID profile là mã quản lý cục bộ. Không thay Canvas/WebGL, không random User-Agent, không giả thiết bị hoặc né xác minh. Bản cập nhật trình duyệt/OS vẫn có thể đổi fingerprint thực.
- Đóng Chrome/Edge qua Browser.close để cookie được ghi xuống đĩa trước khi dừng tiến trình. Đóng/hủy phiên không xóa profile đã gắn tài khoản; profile mới chưa lưu được bỏ. Gỡ tài khoản dùng các guard backend cũ và dọn profile mới do tính năng quản lý; profile Flow cũ tiếp tục theo lifecycle Flow hiện có.
- Profile tự chứa dữ liệu web nhạy cảm theo cơ chế của trình duyệt; mapping và snapshot đăng nhập dùng vault mã hóa. Không sao chép profile trình duyệt cá nhân. Không đưa profile/cookie vào gói cập nhật hay ZIP dự án.
- Gợi ý cache Chromium 64 MB disk + 32 MB media mỗi profile; không phải giới hạn cứng cho toàn bộ profile. Có thể tốn vài chục/vài trăm MB hoặc hơn. Dung lượng profile được thống kê riêng, không bị nút dọn ZIP cache xóa.
- Không làm phiên sống mãi, không bảo đảm tránh đăng xuất/OTP của dịch vụ. Không tự tạo nội dung khi mở phiên.

## Kiểm tra

Chromium thật, origin thử nghiệm cục bộ, chạy headless trong CI: cookie/localStorage sống qua đóng và khởi động lại vault/manager/browser; UA/platform/ngôn ngữ/viewport giữ nguyên; profile hai tài khoản không lẫn; cookie mới không bị snapshot cũ ghi đè; cookie phiên được khôi phục; khóa profile có thể hủy khi chờ; gỡ một tài khoản không xóa tài khoản khác; path/service guards và registry mã hóa. Thử thêm launcher native thật + CDP với URL cục bộ được thay riêng trong test để xác nhận cookie flush qua đóng/mở subprocess. Backend Muse save/reopen/cancel/remove chạy với vault thật, thay cửa sổ ngoài bằng fixture. Regression UI đăng nhập/sơ đồ/gỡ và thống kê dung lượng đã qua. EXE kiểm tra nguồn đóng gói và checksum.

Chưa chạy cửa sổ headed trên Windows, đăng nhập tài khoản dịch vụ thật hoặc trình cài Windows. Gói chỉ chứa code/giao diện, không có model hay dữ liệu tài khoản.

SHA-256: 65133d054c5728b21707a250fc3734efb7315cf26564b061f4abfadc80ad5cbf
