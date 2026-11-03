# SceneForge v46.58 — node Video Veo

Đóng SceneForge, chạy `SceneForge-Update-20261104-v46.58-Veo-Node-Redesign.exe`, rồi mở lại. Cần bản .52 trở lên, gồm .56/.57.

- Lưới clip theo cảnh, nhóm a/b, nhãn trạng thái, lọc Tất cả / Cần xem. Nhiều clip dùng ô nhỏ và cuộn trong node.
- Bấm clip: video bên trái, prompt sửa trực tiếp bên phải; xem các phiên bản/video mẫu, phát chậm 0.5×, lặp và chuyển cảnh. Giữ các phiên bản clip.
- Video tải và kiểm tra hợp lệ sẽ tự gắn đúng cảnh; không cần bấm Dùng clip để phần mềm nhận. Duyệt là xác nhận chất lượng trước khi sang Dựng.
- Tiến độ từng bước ghi rõ ước tính; chỉ 100% khi clip được nhập/lưu. Trạng thái chưa rõ không hiện phần trăm giả hoặc chữ `missing`.
- Tạo nhiều clip sẵn sàng chạy tuần tự sau một lần xác nhận. Dừng gửi thêm khi lỗi/chưa rõ kết quả hoặc đầu vào đổi. Không tự tạo lại và không tự khôi phục hàng đợi sau khi khởi động lại.
- Dùng chung cấu hình trên thanh workflow. Không đưa giá credit chưa xác minh hoặc công tắc xóa logo chưa có chức năng vào giao diện.
- Cảnh báo có mốc thời gian chỉ hiện khi dữ liệu kiểm tra cục bộ thực sự có sẵn, không tự tuyên bố phát hiện mặt đổi.

Giữ nguyên sáu module engine của .57: CLI gốc, session/tài khoản, ledger, một lần upload ảnh, cách tải và phục hồi tải. Dùng cách chia phần clip hiện có, không tự thay quy tắc chia cảnh.

Kiểm tra đúng tệp lấy từ EXE bằng Chromium và video MP4 8 giây cục bộ: sửa prompt không gửi tạo; nhận đúng cảnh, không nhập trùng khi đọc lại; duyệt riêng; hai clip gửi đúng hai lệnh; kết quả chưa rõ dừng hàng đợi. Các kiểm tra cấu hình, dock trong iframe và tải phục hồi vẫn qua. API được giả lập trong kiểm tra, không tạo trên Google. Chưa chạy bộ cài Windows hoặc xác minh Flow thật.

SHA256: `cf4da0ee2ec5ae515e5b3af321dacb3180ccc9cf7fe8cf8886ed2c9c118574b3`
