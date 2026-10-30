# Đối chiếu Phoma 1.6.2 và SceneForge — 30/10/2026

Đã đọc tĩnh bộ Phoma người dùng cung cấp. Không chạy bộ cài, không đăng nhập hay gửi tạo trên Google. Không chứa source Phoma, cookie, token, profile hoặc prompt cá nhân. Các đường dẫn dưới đây là bằng chứng trong bộ mã đã trích xuất, không phải xác nhận cấu hình đang chạy trên máy người dùng.

## Kết quả chính

Phoma có bộ quản lý trình duyệt theo tài khoản + workspace cho mỗi luồng công việc. Nhánh API có tạo video từ một ảnh đầu, gắn mediaId và theo dõi kết quả. Nhánh DOM trong bộ mã này dừng ở thông báo chưa hỗ trợ tạo video. Đã tìm thêm file resources/.env đi kèm bộ cài: VEO3_FLOW_EXECUTION_MODE=api, VEO3_EMBEDDED_BROWSER=false, APP_BACKGROUND_BROWSER=true. electron/main.js:28–55 nạp cấu hình từ resources và không ghi đè biến môi trường đã có. Do đó bộ cài cấu hình nhánh API và Chrome ngoài; chưa quan sát trực tiếp một lượt chạy trên máy người dùng để loại trừ override môi trường. Không xuất hoặc công bố toàn bộ file .env.

SceneForge v32 nối riêng Flow qua extension là nhánh thao tác DOM, không phải bản sao backend Phoma. Luồng native_bridge cũ của SceneForge cũng đã gửi RPC từ tab Flow được ghép, nên cách giải thích đơn giản rằng chỉ Phoma gửi từ trong browser là không đúng. Cùng tên RPC không chứng minh cùng toàn bộ ngữ cảnh, cũng không xác định nguyên nhân Google chặn.

## Bằng chứng và khác biệt

| Khâu | Phoma trong mã đã đọc | SceneForge và hệ quả |
|---|---|---|
| Tài khoản/profile | browser-server-dist/accounts/accounts.service.js:29–36 tạo profile theo provider/accountId; browser/account-browsers.js:81 mở profile của tài khoản | Luồng web cũ dùng một profile riêng; v32 dùng tab Chrome được ghép. Hai cơ chế này cần phân biệt, không coi mở cửa sổ là đã có đường tạo |
| Nối trình duyệt | browser/browser.service.js có các nhánh Puppeteer connect đến browser đang quản lý | v32 extension điều khiển tab; nhánh web cũ nối Playwright CDP. Khác công cụ chưa chứng minh nguyên nhân Google từ chối |
| Workspace/project | generation/veo3/core.service.js:85–160 và video-workspace.js chuẩn bị/reuse page + project | Trước đây extension có thể nhận tab danh sách dự án rồi mới lỗi selector. Cần giữ ràng buộc account/tab/project trước tạo |
| Ảnh đầu | core.service.js:222–281 tải ảnh đầu, lưu mediaId, chọn nhánh start-video khi không có ảnh cuối | Đúng yêu cầu một ảnh khung + prompt chuyển động; không cần đổi thành nhóm ảnh tham chiếu |
| Chế độ thực thi | Hàm mặc định dom, nhưng resources/.env của bộ cài đặt VEO3_FLOW_EXECUTION_MODE=api; electron/main.js nạp file đó. Nhánh dom ở core.service.js:167–171 chưa tạo video | Nhánh được cấu hình của bộ cài là API nội bộ Flow qua phiên web, không phải chuỗi bấm menu. Chưa quan sát process của người dùng để loại trừ override |
| Gửi tạo | core.service.js:250–307 có nhánh API tạo video; flow-batch.js định nghĩa các thao tác tương ứng | Không thể chuyển thẳng thành bằng chứng bản sửa SceneForge sẽ thành công. Chưa chuyển nhánh API sang SceneForge hoặc chứng minh được khác biệt nào gây lỗi Google |
| Hàng chờ | video-account-run-lane.js giữ chủ sở hữu theo account; video-workspace.js:86–129 tuần tự hóa gửi và chặn luồng khi gặp lỗi traffic | SceneForge đã có khóa, ledger và chặn lượt chưa rõ. Cần giữ nguyên cơ chế dừng, không đổi account/proxy để tiếp tục sau lỗi |
| Kết quả | core.service.js:359–397 theo dõi media/project/workflow và phân biệt failed/success | Driver DOM của SceneForge theo video mới so với baseline; còn thiếu bằng chứng nhận dạng kết quả trên Flow thật, không thể nói tương đương Phoma |

## Phần đã áp dụng được mà không thử tài khoản

Tiện ích 1.6.9 bổ sung ràng buộc workspace:
- Không chuyển lệnh chuẩn bị video vào tab đang ở trang danh sách dự án.
- Giữ project tại lúc ghép hoặc lần prepare đầu tiên, cùng ràng buộc account/tab đã có.
- Không tiếp tục một lượt sau khi tab chuyển project; thay đổi query không làm nhầm project.
- Báo cáo hiện có page_kind, paired_transport, paired_tab, workspace_pinned để phân biệt extension_dom và native_relay. Không đưa route key hoặc project URL/ID vào báo cáo.
- Giữ nguyên nhận diện hoạt động bất thường và không tự Retry.

Đây là sửa vòng đời phiên/workspace và độ rõ của chẩn đoán, KHÔNG phải bản đã khắc phục Google UNUSUAL_ACTIVITY. Không thêm đường RPC mới, không tự gửi tạo, không sửa cấu hình xác minh của Google, không đọc profile Phoma hay tài khoản người dùng.

## Kiểm chứng và phần còn thiếu

Đã chạy Chromium với toàn bộ trang được chặn và thay bằng fixture: home/project, đổi query, đổi project, kiểm tra hash không lộ ID, dừng lỗi hoạt động bất thường, luồng gửi/nhận fixture. Đây không phải đăng nhập Google thật, không phải kiểm tra updater Windows, không chứng minh tính tương thích với Flow đang triển khai.

Để xác định vì sao Phoma thành công còn SceneForge bị chặn, đã biết cấu hình bộ cài chọn API, nhưng vẫn thiếu metadata runtime đã loại bí mật của lượt thành công (phiên bản thực chạy, loại đầu vào, stage và định danh lượt đã băm). Không cần gửi cookie, token, fingerprint, HAR đầy đủ hoặc thử lại tài khoản đang bị từ chối. Chưa có bằng chứng để quy nguyên nhân cho riêng Flow2API, profile, selector hoặc credit.
