# SceneForge v46.64 — giảm khựng khi chuyển tab và mở cảnh

Đóng app, chạy `SceneForge-Update-20261104-v46.64-Smooth-Navigation.exe` trên bản .63 trở lên, mở lại. Gói cập nhật khoảng 4 MB; không phải bộ cài đầy đủ.

- Chặn kết quả tải chậm giành lại màn hình sau khi chọn tab mới (Kho kịch bản, Trang chủ, Tạo video, Dựng, hàng loạt, theo dõi và lưu trữ).
- Các lần bấm cùng tab dùng chung việc khởi tạo iframe. Khi chuyển sang tab đã sẵn sàng, màn chờ của tab cũ không che tab mới. Chờ một nhịp vẽ giao diện trước khi khởi tạo dữ liệu nặng.
- Khi mở Phân tích video, chỉ đọc đúng bản ghi dự án thay vì getAll tất cả dự án và media. Không đổi schema, xóa dữ liệu hoặc tạo lại video.
- Mở chi tiết cảnh chỉ dựng phần chi tiết; không thay toàn bộ DOM sơ đồ/ảnh/video.
- Giữ bước lưu và các chặn đang phân tích/xuất. Không hủy tác vụ tạo video vì đổi tab. Engine/runtime/tài khoản giữ nguyên.

Kiểm thử Chromium: tái hiện lỗi tab cũ giành màn hình trên .63, xác minh bản sửa không bị; một lần khởi tạo khi bấm liên tục; lưu đang chờ hoàn tất nhưng không đổi tab về chỗ cũ; không quét toàn bộ projects khi mở phòng; mở cảnh không render lại canvas và vẫn giữ chỉnh prompt. Các kiểm thử chuyển tab .63, giao diện Veo và ba bộ JS cấu hình/tạo/đối soát đạt. Fixture cục bộ, chưa kiểm updater trên Windows hoặc Google Flow thật. Không cam kết hết mọi nguyên nhân lag.

SHA256: `b001943fef07f3dcdd6cd74101a450fdf5f55c82d84b6f6daf28e281ad29c5dc`
