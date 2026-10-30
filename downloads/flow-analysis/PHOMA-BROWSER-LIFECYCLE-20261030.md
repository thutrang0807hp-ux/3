# Đối chiếu khởi chạy và vòng đời trình duyệt: Phoma / SceneForge

Ngày 30/10/2026. Đọc tĩnh bộ Phoma đã được cung cấp; không chạy code hoặc bộ cài Phoma, không thử tài khoản Google. Không xuất file .env, profile, cookie, token hoặc fingerprint. Báo cáo không phải bản sửa đăng nhập đã được xác nhận.

## Những gì xác nhận được

1. **Phoma được cấu hình dùng API và Chrome ngoài.** File cấu hình kèm bộ cài có chế độ API và tắt trình duyệt nhúng cho Veo. `electron/main.js:28–55` nạp file cấu hình từ resources. Một môi trường bên ngoài vẫn có thể ghi đè cấu hình; chưa quan sát trực tiếp process trên máy người dùng.
2. **Cả hai phần mềm đều có code chọn Chrome cài trên máy.** Phoma dùng `browser-server-dist/browser/cdp.js::findChrome`; SceneForge dùng `local_engine/google_login.py::installed_browser` và bootstrap Windows. Ảnh người dùng xác nhận cửa sổ SceneForge là Chrome chính thức trong profile của app; chưa có phiên bản/process runtime tương ứng của Phoma để so sánh.
3. **Phoma tách đường mở tài khoản và worker.** `browser/account-browsers.js::openAccountBrowser` có nhiều nhánh. `browser/cdp.js` có cả hàm mở cửa sổ profile và hàm chạy process do worker quản lý. Chỉ nhìn một hàm không đủ khẳng định lượt thành công dùng nhánh đó.
4. **CDP không phải khác biệt chỉ SceneForge mới có.** Phoma có Puppeteer CDP trong `browser/browser.service.js` và `browser/veo3-worker.js`; SceneForge dùng Playwright CDP ở nhánh không tiện ích. Chưa có bằng chứng CDP hoặc lựa chọn thư viện là nguyên nhân Google từ chối. Không đề xuất che dấu điều khiển trình duyệt để thay đổi kết quả này.

## So sánh vòng đời

| Khâu | Phoma trong source | SceneForge hiện tại | Kết luận có thể rút ra |
|---|---|---|---|
| Profile | `accounts/accounts.service.js:29–36`: provider/accountId | Bản v33+ có map profile theo tài khoản, giữ tương thích profile flow-web cũ | Profile cũ không tự chứng minh là sai hoặc là nguyên nhân Google chặn |
| Sở hữu phiên | Worker lưu accountId, process, port, page và trạng thái lease | Map tài khoản/profile và ràng buộc account/project; một số nhánh cũ chỉ dựa vào file cổng | Cần xác nhận đúng instance, không chỉ có file DevToolsActivePort |
| Cổng sẵn sàng | `browser/cdp.js::isCdpReady/waitCdp` kiểm tra endpoint; `cdp-port.js` quản lý cổng worker | Trước sửa: đọc file cổng rồi nối, thiếu đối chiếu định danh instance | Có thể sửa lỗi liên kết cục bộ này độc lập với lỗi đăng nhập Google |
| Kết thúc process | `browser/process-lifecycle.js` đợi process/cổng đóng; worker quản lý chủ sở hữu | Chủ yếu ngắt Playwright và giữ cửa sổ người dùng mở; watcher quản lý trạng thái đăng nhập | Hai thiết kế khác nhau; chưa chứng minh thiết kế nào gây phản hồi Google |
| Tạo video | Nhánh API nội bộ Flow, upload ảnh đầu và theo dõi media | Nhánh web mới dùng DOM; RPC native cũ cũng từng chạy trong tab đã ghép | Đăng nhập giống về profile không làm hai backend tạo video trở nên tương đương |
| Lỗi Google | Có phân loại lỗi provider | Đã dừng theo signin/rejected và thẻ hoạt động bất thường | Giữ nguyên việc dừng, không tự Retry hoặc đổi account/proxy để tiếp tục |

## Phần code SceneForge đã sửa trong workspace

Thêm `local_engine/flow_browser_probe.py`, dùng chung cho watcher và session:
- Chỉ đọc `/json/version` của cổng loopback thuộc profile app.
- Đối chiếu đường định danh browser instance với dòng thứ hai của DevToolsActivePort.
- Từ chối port bị dùng lại, endpoint khác instance, endpoint ngoài loopback, cổng không phản hồi và metadata không hợp lệ.
- Trả nguyên nhân kết nối cục bộ riêng, không coi mở cửa sổ hoặc có file cổng là xác minh đăng nhập thành công.
- Không đổi lệnh đăng nhập, không sửa fingerprint, không trì hoãn kết nối để tránh kiểm tra, không nhập profile Phoma và không thêm private RPC.

Các thay đổi kiểm tra kết nối này đã được đóng gói trong updater v35 theo yêu cầu người dùng. Không coi phần sửa kết nối này là đã giải quyết Google's sign-in rejection. Chưa xác minh đăng nhập Google thật hoặc updater Windows.

## Kiểm tra đã chạy

- Fixture HTTP: port hợp lệ, instance khớp/không khớp, host ngoài máy, endpoint không phản hồi, file port sai. Không truy cập trang hoặc gọi đăng nhập.
- Chromium thực với các trang đều được thay bằng fixture: nhận tài khoản/profile, dùng lại cửa sổ, gửi/nhận video mô phỏng, chống gửi trùng, dừng khi đổi account/project, dừng khi trang từ chối đăng nhập xuất hiện.
- Kiểm tra tương thích watcher đăng nhập cũ với fixture.

Không thử Google thật, không chạy updater Windows thật. Kiểm tra mô phỏng không chứng minh Google sẽ chấp nhận cửa sổ trên máy người dùng.

## Điều chưa xác định

Báo cáo trước của người dùng có file cổng nhưng endpoint không phản hồi; ảnh xác nhận Chrome chính thức đang mở với profile app. Hai dữ kiện này chưa cho biết do file cũ, quyền đọc, trạng thái endpoint, cấu hình máy hay lý do khác. Cũng chưa chứng minh lỗi kết nối cục bộ là nguyên nhân Google từ chối.

Vì vậy, hiện chưa có kết luận kỹ thuật đủ chắc để phát hành một bản được gọi là khôi phục đăng nhập Flow. Không yêu cầu người dùng tạo thêm lượt hoặc đăng nhập thử liên tục trên tài khoản để xác minh phỏng đoán.
