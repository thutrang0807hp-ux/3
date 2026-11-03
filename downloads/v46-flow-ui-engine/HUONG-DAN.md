# SceneForge v46.46 — Flow UI Engine

Tải và chạy `SceneForge-Update-20261103-v46.46-Flow-UI-Engine.exe`, cập nhật vào
thư mục SceneForge đang cài. Yêu cầu bản .42 trở lên; không cần cài lại toàn bộ.

Mở SceneForge, dùng tài khoản Flow đã chọn và bấm **Tạo 1 video** trong node.
Lần đầu phần mềm tự tải runtime riêng khoảng 80 MB và kiểm tra SHA256; các lần
sau dùng bản đã lưu. Không cần mở GFlow Studio, chạy lệnh hay tự upload ảnh.
Trình duyệt đã cài sẽ mở để engine thao tác Flow bằng profile hiện có.

Bản này dùng engine giao diện gflow-cli 0.92.1 thay cho đường RPC tự viết khi
bấm tạo video. Giữ RequestLedger hiện có, không tự tạo lại nếu kết quả chưa rõ.
Gói EXE chứa mã nối engine; runtime được tải tự động từ URL cố định đã kiểm
checksum, không cài pip hoặc thay thư viện Python chung của SceneForge.

Đã kiểm tra checksum, tệp nhúng và 9 kiểm tra cục bộ. Chưa chạy updater trên
Windows và chưa xác minh tạo video trên tài khoản Flow thật.

SHA256 EXE: `678687e8ba51c0369bd64801583319ad79d83dbf6a83440ba3d37294f7755b4a`
