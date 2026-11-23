# SceneForge .165 — chỉnh riêng ảnh khung

Đóng SceneForge, chạy bản cập nhật và chọn đúng thư mục đang cài. Mở lại node Ảnh khung → bấm một cảnh.

- Tham chiếu: mỗi mục dùng chung, giữ nguyên hoặc chọn ảnh riêng (tối đa 3 ảnh/mục, tổng lượt vẫn tối đa 8 ảnh kể cả nguồn).
- Prompt: giữ khung prompt hiện tại; có thể sửa và lưu, AI tối ưu là tùy chọn.
- Lịch sử: chọn lại phiên bản ảnh đã có.
- So sánh gốc/kết quả bằng thanh kéo. Nhãn kích thước hiển thị rộng × cao và tỉ lệ; khung nguồn xem trước được ghi rõ, kết quả dùng kích thước tệp gốc.
- Thanh tiến độ đếm cảnh hoàn tất và báo bước đang chạy; không đoán phần trăm phía Gemini.
- Chỉ tạo lại cảnh đang mở; nút tạo phần thiếu trên node chỉ xử lý cảnh chưa có ảnh.

Ảnh chung tiếp tục quản lý ở node Ảnh tham chiếu. Không thêm nhóm tay cố định. Chỉ thay các vai trò được nối, giữ bố cục/cách cầm theo khung gốc. Các lựa chọn riêng được lưu theo cảnh; về thiết lập chung không xóa ảnh/lịch sử. Sửa tham chiếu không tự gửi yêu cầu tạo ảnh. Ảnh mới cần duyệt trước khi tạo video.

Giữ nguyên tiện ích 1.8.0, kết nối tài khoản, hàm Gemini gốc và backend của .164. Không cần cài lại tiện ích cho bản này. Gói gộp nhận từ .62 trở lên, giữ dự án và model.

Đã kiểm tra node thật + backend/ledger với Gemini DOM và kết nối tiện ích mô phỏng; kiểm tra bộ ảnh gửi đi, prompt cũ, không lẫn cảnh, không gửi lại khi sửa, kích thước và thanh so sánh. Chưa chạy trên Gemini thật/Windows của bạn; chất lượng thay thế và chữ nhỏ vẫn cần duyệt bằng mắt.

Implementation: scene.frameReferenceChoices holds keep/custom choices; shared defaults reuse existing reference selection. sceneReference/refsFor resolve these before the unchanged imageBindings/generationRefs packing and unchanged direct prompt recipe. Custom uploads retain original assets. Product keep removes product context and bindings; custom takes precedence over legacy product-off flags. Existing manual prompt ownership checks still require review after changed inputs. No browser/account/worker/backend file changes. The cumulative builder pins all non-workflow payload files to .164. Existing receipts remain schema164, so this UI update resumes the same job owner without migration.
