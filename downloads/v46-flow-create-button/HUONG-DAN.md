# SceneForge v46.48 — chỉ thay đường gửi tạo video

Chạy `SceneForge-Update-20261103-v46.48-Flow-Create-Button.exe` để cập nhật
SceneForge .42 trở lên. Không cần cài tuần tự .46 hoặc .47.

Giữ luồng đăng nhập, tài khoản, ảnh, prompt và cấu hình hiện có. Phần chuẩn bị
workspace/upload/xác minh ảnh chạy như trước. Sau đó nút Tạo video dùng engine
UI gflow-cli 0.92.1 để chọn ảnh vừa upload trong cùng dự án, gửi tạo, chờ kết quả
và tải clip về đúng cảnh. Không tự tạo lại các mã lượt cũ. Runtime riêng tự tải
ở lần đầu nếu chưa có, không yêu cầu chạy lệnh hoặc mở GFlow Studio.

Đã kiểm tra mã lấy từ EXE: checksum 13 tệp, biên dịch Python, 10 kiểm tra
adapter/worker và 4 kịch bản submit/run/ledger. Đối chiếu AST với .45 xác nhận
phần run giữ nguyên ngoại trừ nhánh thay sender. Frontend và các module chuẩn
bị không đổi. Các kiểm tra dùng fixture, chưa xác minh Windows/Flow thật.

SHA256 EXE: `de0d353ce95007b4c7978ac99b8e2174f4a35bc80d3bf3fbe8766470c9b9c389`
