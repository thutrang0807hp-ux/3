# SceneForge .96 — Giảm chậm và cảnh báo giả khi thoát ứng dụng

Đóng app rồi cập nhật trên .95. Đây là sửa thao tác thoát cả phần mềm, không đổi nút gỡ tài khoản.

## Thay đổi

- Kho đã sạch không quét/mã hóa/hash/commit lại toàn thư viện khi checkpoint. Chỉ xác nhận revision hiện tại.
- SceneForgeApp.flush dùng API lưu bản nháp riêng, tách khỏi guard đổi phòng. Các guard đổi phòng khi đang dò cảnh/phân tích/xuất vẫn giữ nguyên.
- Workflow và từ ảnh theo dõi version bản nháp và write đang chạy. Host gọi flush hai lần nhưng lần sau sạch sẽ không ghi lại Blob/dự án. Bản nháp chưa lưu vẫn phải hoàn tất transaction, lỗi được trả lên.
- Editor có flushForClose, chờ bản nháp chứ không chờ công việc xuất hoàn tất. Không tuyên bố MP4 chưa xong đã xuất thành công.
- Storage.flush thử lại khi metadata vừa thay đổi trong quá trình đọc; chỉ thành công khi không còn dirty/busy. Kho không active hoặc lỗi lưu thật vẫn trả lỗi.
- Không thay host EXE hoặc vô hiệu hóa cảnh báo mất dữ liệu. Khi lưu sạch, host nhận ok:true nên không hiện hộp hỏi do lỗi guard đổi phòng; khi lưu lỗi thật vẫn cảnh báo. Không sửa tài khoản, fingerprint, model hay hành vi tạo nội dung.

## Kiểm tra

Tái hiện đúng hai lời gọi JavaScript của DesktopHost trong Chromium với IndexedDB và SQLite thật: đóng khi sạch dưới 500 ms trong fixture, 0 ghi workflow/0 commit snapshot; sửa cuối chỉ ghi workflow một lần, snapshot một lần và media 2 MB còn nguyên. Kiểm tra từ ảnh và editor marker qua save-only API; guard đổi phòng vẫn chặn lúc được báo busy. Khi giả lập canonical save conflict, host nhận ok:false và bản sửa còn trong IndexedDB. Regression thống kê/dọn dung lượng đã qua. EXE kiểm tra payload và nút tải/checksum.

Chưa chạy host Windows/WebView2 thực hoặc đo nút X trên máy người dùng; tối ưu phần lưu trước khi native host đóng cửa sổ. Cảnh báo do lỗi lưu thật không bị tắt.
