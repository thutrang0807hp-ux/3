# SceneForge .56 — bảng cấu hình nối trực tiếp CLI

Cập nhật từ .52 trở lên. Mở ⚙ Flow trên thanh Workflow, chọn cấu hình rồi bấm
Tạo video. Các lựa chọn được lưu và gửi cùng lượt tạo; không gọi Settings trigger
trên trang Flow và không cần bấm Áp dụng riêng.

Hỗ trợ:
- Thành phần: Lite hoặc Fast, dùng CLI video r2v với một ảnh.
- Khung hình: Lite, Fast hoặc Quality, dùng CLI video i2v với một ảnh đầu.
- Tỉ lệ: 9:16 dọc hoặc 16:9 ngang; phần nhận clip kiểm tra đúng tỉ lệ của lượt đó.
- Một video mỗi lượt. x2–x4 không cho chọn vì chưa có luồng nhận đầy đủ nhiều kết quả.

Thời lượng dùng mặc định Flow; workflow vẫn kiểm tra clip khoảng 8 giây. Không ép
--duration 8 vì đã gây lỗi trên tài khoản người dùng. Tải bản gốc, chưa thêm
1080p/4K, giá PRO/ULTRA hay các tùy chọn chưa được xác minh.

Giao diện giữ màu tối của SceneForge, dùng nút chọn tỉ lệ/chế độ và một danh sách
model. Lựa chọn chưa gửi tạo chỉ vì người dùng đổi cấu hình. Quality không được
chọn với Thành phần. CLI gốc tự thao tác model có trên tài khoản Flow, không ghi
đè session/SDK và không tự đổi sang model khác nếu không khả dụng.

Cấu hình được chốt vào request và kết quả. Đổi bảng sau khi gửi không diễn giải
lại clip cũ. Giữ một lần upload và cơ chế tải lại clip đã tạo của bản trước.

Đã kiểm tra 11 trường hợp CLI, luồng submit/prepare/CLI/ffprobe thật với provider
giả lập, nhập video ngang, trường hợp request trùng/đổi cấu hình, nhận clip cũ và
bảng Chromium thật. Kiểm tra trên mã lấy từ EXE; chưa chạy updater Windows hoặc
tạo video Flow thật với các cấu hình mới.

SHA256 EXE: `fbe2b0ddf8e437b8db23eaf62ca6213fbb4d2151ba04e8b20278f37f605e5a3c`
