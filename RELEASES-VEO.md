# Các bản Veo đã giao: v42–v45

Danh sách này chỉ gom các bản trước công cụ thử chạy nền. Gói v45 không chứa thử nghiệm đó.

| Bản | Nội dung | Mã chính | Gói cập nhật | Source ZIP |
| --- | --- | --- | --- | --- |
| v42 | Đường Flow một phiên, engine cũ không khởi động mặc định | [Nguồn](simple-flow-v42) | [EXE](downloads/v42/SceneForge-Update-20261031-v42.exe) | Xem hướng dẫn trong thư mục v42 |
| v43 | Thay cơ chế ngay trong node Veo hiện có, giữ cổng và dây | [Nguồn](veo-node-v43) | [EXE](downloads/v43/SceneForge-Update-20261031-v43.exe) | [ZIP](downloads/v43/SceneForge-Veo-v43-Source.zip) |
| v44 | Theo dõi thẻ kết quả, tự tải khi nhận diện được, lưu phiên riêng | [Nguồn](veo-node-v44) | [EXE](downloads/v44/SceneForge-Update-20261101-v44.exe) | [ZIP](downloads/v44/SceneForge-Veo-v44-Source.zip) |
| v45 | Trả lại giao diện Tài khoản cũ, node dùng tài khoản web đang chọn, bỏ kết nối riêng | [Nguồn](veo-node-v45) | [EXE](downloads/v45/SceneForge-Update-20261101-v45.exe) | [ZIP](downloads/v45/SceneForge-Veo-v45-Source.zip) |

Trang xem thử và trang tải chính hiện đồng bộ đúng frontend v45 lấy từ payload đã giao. Xem thử chỉ là giao diện, không có backend Google để đăng nhập/tạo video trên GitHub Pages.

**Vấn đề còn tồn tại ở v45:** tài khoản đã lưu không đồng nghĩa cửa sổ Flow đang kết nối. Nếu endpoint trình duyệt không phản hồi, node báo FLOW_BROWSER_ENDPOINT_UNAVAILABLE và không gửi tạo video. Chưa có chạy nền trong v45. Các lần kiểm tra Chromium/fixture không chứng nhận tạo video Google thật hoặc updater trên Windows.

Đọc [hướng dẫn v45](downloads/v45/HUONG-DAN.md) về phạm vi, cách dùng và kiểm thử. Không cần cài tuần tự từng bản; updater kiểm baseline và tối thiểu v14 theo hướng dẫn.
