# SceneForge v46.47 — sửa điểm gọi engine Flow

Chạy `SceneForge-Update-20261103-v46.47-Flow-UI-Engine.exe` để cập nhật bản .42
trở lên. Không cần cài tuần tự .46. Giữ tài khoản Flow đã chọn trong SceneForge.
Lần đầu tạo video, phần mềm tự tải runtime riêng khoảng 80 MB.

Bản .46 đã nối nhầm engine mới vào thử upload, khiến nút Tạo video vẫn chạy RPC
cũ. Bản .47 sửa nhánh trong chính SimpleFlow.run; thử upload không gọi tạo video.
Không tự gửi lại các lượt cũ hoặc coi lỗi cũ là kết quả của engine mới.

Đã kiểm tra tệp nhúng/checksum, 9 kiểm tra adapter/worker, và 4 kịch bản chạy
submit/run/RequestLedger thật với engine giả lập. Kiểm tra mới bắt được lỗi
của mã .46. Chưa chạy Windows hoặc tạo video Flow thật trong môi trường này.

SHA256: `8746413f128709e9834d46e347191a5c10bf9fe7b13d8ee0fb83f9ebd4dd4ded`
