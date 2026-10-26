# Củng cố tài khoản và nhận ảnh chat — 27/10/2026

Sửa các lỗi đã đối chiếu từ đánh giá gói Cài đặt; không thay node hoặc cách dùng hai luồng video.

## Hành vi đã sửa

- ChatGPT/Grok/Meta có thể nhận nhóm tối đa 8 ảnh trong một lượt (mỗi ảnh 24 MB, tổng 96 MB). Đợi nhóm URL ổn định ít nhất ba khoảng kiểm 2 giây và nút/trạng thái đang gen biến mất; không nhận ngay ảnh đầu tiên. Mỗi ảnh được kiểm định dạng, giữ file gốc và lưu kho theo hash. Nhóm cùng một job, không tạo thêm yêu cầu AI.
- Trong kết quả Batch có nút Ảnh 1/2/... để xem và tải riêng. Tải nhóm/ZIP các kết quả đã chọn chứa đủ ảnh dịch vụ trả về. Mở lại và Kiểm tra kết quả không nhân bản; Tạo lại vẫn chỉ tạo số job đã yêu cầu, không nhân theo số ảnh trả về.
- Khi có bằng chứng rõ về trang đăng nhập, tài khoản thành hết phiên; có thông báo hạn mức trong vùng cảnh báo thì thành hết lượt. Thiếu/đổi giao diện mà chưa xác nhận được phiên thì cần xác minh. Tài khoản đó không nhận việc mới. Mạng lỗi không bị coi là hết quota và không tự đổi tài khoản gửi lại.
- Kiểm tra phiên không tự xóa trạng thái hết lượt. Người dùng có thể xác nhận “cho phép thử lại ở việc mới” sau kiểm phiên; không khẳng định quota đã hồi và không gửi lại job cũ.
- Chuyển Chia việc/Dự phòng không bị chặn chỉ vì tài khoản đang chọn không còn hợp lệ, miễn còn tài khoản khác sẵn sàng. Dùng riêng vẫn đòi đúng tài khoản hợp lệ; job đã nhận vẫn ghim tài khoản cũ.
- Lưu URL hội thoại khi trang có URL cụ thể; bỏ query/fragment, chỉ cho đúng miền dịch vụ. Kết quả/ô lỗi có link mở hội thoại khi đã ghi được. Không phải cơ chế tự gửi lại hoặc tự khôi phục bằng API.
- Phiên mới và phiên cũ khi khởi động adapter chỉ giữ cookie/localStorage thuộc miền chat chính. Không giữ toàn bộ cookie Google/Facebook trong cửa sổ SSO. Một số cách đăng nhập có thể cần đăng nhập lại; không mạo nhận còn dùng được nếu không kiểm được phiên.
- Bảng tài khoản phân biệt kiểm phiên với đã nhận ảnh thành công theo TỪNG tài khoản. Không suy từ tài khoản A tạo được rằng B cũng tạo được. Meta AI không còn nhãn “Muse”; Muse cũ vẫn muse.ai. Biểu tượng nguồn riêng.
- Tab Động cơ có Playwright/Chromium, nhận biết package và executable trong đường cài thông dụng; cài qua install-chat-browser.bat. Job gen mặc định chạy Chromium không hiện cửa sổ; đăng nhập và kiểm phiên vẫn có cửa sổ. Có thể dùng SCENEFORGE_CHAT_VISIBLE=1 khi cần quan sát.
- Sửa bài kiểm Cài đặt cũ: đối chiếu tên engine thay vì đếm cứng; kiểm API dùng rõ nguồn API và fixture, không yêu cầu SDK Chat ngoài phạm vi bài kiểm.

## Kiểm chứng

Xem `chat-reliability-checks.json`: trình duyệt Chromium thật trên trang bị intercept, app/HTTP/SQLite/thư viện file thật, provider giả. Có bài tái hiện 4 ảnh xuất hiện trễ, trạng thái auth/quota, Chia việc với tài khoản cũ hỏng, giữ quota khi chỉ kiểm phiên, cho phép thử mới có xác nhận, URL không chứa query/fragment, không lưu SSO, ảnh phụ được bảo vệ khi dọn và không giữ bản backend trùng. UI kiểm PNG/ZIP thực, reload và số lượt gửi.

## Giới hạn còn lại

CHƯA thử tài khoản online thật hoặc Windows. Selector/completion marker và thông báo hạn mức vẫn cần xác minh trên UI thực/ngôn ngữ dịch vụ. Chờ ổn định ảnh là cơ chế thận trọng, chưa phải tín hiệu hoàn tất chính thức của dịch vụ. Nếu dịch vụ đổi UI/không tìm được ảnh đầy đủ, job dừng, không tự gửi lại. Lượt đã bấm gửi mà lỗi vẫn có thể là unknown; link hội thoại hỗ trợ người dùng tìm lại, không đảm bảo dịch vụ luôn cấp URL trước khi mất kết nối.

Không thêm dọn lô 24h, Đóng & dọn lô hay đổi chính sách dừng hàng đợi Batch. Không gộp lowSpaceGB và storage-limits trong đợt này. Không thêm cấu hình tài khoản riêng mỗi sản phẩm, fingerprint/antidetect hay đổi hạn mức của dịch vụ. Không chuyển sang API trả phí khi chat lỗi.
