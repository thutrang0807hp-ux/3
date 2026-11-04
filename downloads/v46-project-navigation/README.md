# SceneForge v46.67 — giảm khựng khi vào/ra dự án

Đóng app, chạy `SceneForge-Update-20261104-v46.67-Project-Navigation.exe` trên .66, mở lại. Khoảng 4 MB; không phải bộ cài đầy đủ. Không xóa Data/cache.

Người dùng làm rõ: sau khi mở dự án ở Phân tích, bấm tab khác thấy cứng và rất lâu mới chuyển. Mẫu nhỏ 30 cảnh không tái hiện đứng hoàn toàn; mẫu thật cục bộ 60 cảnh nhiều ảnh cho thấy mở dự án và rời màn hình còn tốn công.

- Ảnh người gần đây dùng metadata nhỏ (ảnh tham chiếu của phòng, có cập nhật từ workflow), không get nguyên 20 workflow gồm assets/media. Đối soát công thức từ thông báo lưu dùng bản tóm tắt mốc cảnh/recipe, không đọc lại toàn bộ workflow mỗi thông báo. Các đường gọi cũ vẫn có fallback đọc bản ghi khi không có tóm tắt.
- Shell báo tiến độ trong workspace chỉ cập nhật thanh điều hướng/trạng thái, bỏ dựng dashboard Trang chủ ẩn.
- Shell yêu cầu reuseLoaded khi mở lại phòng đã roomSeeded, cùng tên và không có workflow mới: bỏ render/fit/save/clone project lặp lại. API gọi không có cờ vẫn giữ kết quả đầy đủ như trước.
- Grid không dựng các frame legacy rồi bỏ; chế độ danh sách vẫn có frame đầy đủ.
- Chuyển tab cùng dự án giữ nguyên iframe và timer autosave, không ép flush toàn bộ hay chờ editor restore. Không tháo parked worker khi chỉ rời màn hình; hidden iframe thắng inline visibility. Đổi/đóng dự án và checkpoint vẫn dùng flush nghiêm ngặt, giữ chặn dò cảnh/xuất/lưu lỗi.

Kiểm với shell, workflow, editor thật và dự án IndexedDB 60 cảnh ảnh JPEG nhiễu 384×682: .66 mở ~3.68s, về Trang chủ sau Phân tích ~262ms/sau Dựng ~224ms trong lượt đo; bản sửa mở ~2.1–2.2s, về Trang chủ sau Phân tích ~39–44ms/sau Dựng ~69ms trong các lượt kiểm. Đây là dữ liệu mẫu cục bộ, không đo trên máy người dùng và không chứng minh hết mọi long task.

check_real_project_navigation.py kiểm đủ 60 thẻ/cảnh, giữ iframe và sửa tên dự án tự lưu sau khi rời màn hình, checkpoint và đổi phòng thật vẫn chặn khi lỗi lưu, tiến độ không render dashboard ẩn, recentPeople và recipe summary không đọc nguyên workflow. Các bộ startup/nav/overview/Veo/3 JS vẫn đạt. Test guard trước đây đã đổi từ chặn việc chuyển view sang guard checkpoint/disposal thật; không vô hiệu hóa guard lưu dữ liệu.

Chỉ thay index.html, studio.html và workflow.html. Engine/runtime/tài khoản/CLI giữ nguyên. Chưa kiểm updater trên Windows, kho dữ liệu người dùng hoặc Flow thật.

SHA256: `fd33c65a167e3681e01a7e4d255d3555fc1c551def086517eedd9745e66c5cf2`
