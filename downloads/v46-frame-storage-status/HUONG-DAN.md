# SceneForge .142 — lý do kho bị chặn ngay trên node

Node Ảnh khung hiển thị Kho lưu lượt AI khi kho managed đang tạm dừng. Lấy trực tiếp state.error/phase thay vì chỉ báo Kho máy chưa sẵn sàng. Nút Kiểm tra lại kho gọi inspector chỉ đọc GET /local-api/library/status, giới hạn chờ 10 giây; hiện kết nối máy và trạng thái ghi trong app. Đối chiếu revision khi phản hồi có revision. Hiển thị cả khi chưa có lượt frame-node trước đó, có thể bấm khi pipeline đang hoạt động.

Không gọi ready/hydrate/useDisk/checkpoint, không cập nhật active/revision, không ghi đè hoặc đổi kho, không chạy AI. Nếu kho đang active=false nhưng máy kết nối được, vẫn báo chưa sẵn sàng; không coi GET thành công là đã phục hồi quyền ghi. Giữ cơ chế chặn gửi khi chưa lưu được ý định.

Guard trước gửi ở shell và workflow bổ sung lý do gốc từ state.error vào lỗi; lỗi lặp trong node có thông tin cụ thể hơn. Chưa tự sửa nguồn xung đột/mất kết nối trên máy người dùng: cần đọc thông báo được hiện tại node để quyết định cách phục hồi an toàn.

Cách dùng: đóng app cập nhật, vào node Ảnh khung, bấm Kiểm tra lại kho trong khung lỗi. Không cần mò hai mục cài đặt thu gọn. Nếu kho báo sẵn sàng thì bấm Tạo lại toàn bộ để gửi lượt mới; nếu chưa, khung giữ lý do cụ thể. Thao tác kiểm tra không tự gửi lại lượt ảnh.

Đã kiểm thử Chromium với inspector thật: lỗi xung đột local được hiện trên node, nút chỉ gọi status, mất kết nối có thông báo, không thay active/revision và không ghi kho, lý do gốc giữ trong lỗi trước gửi; hồi quy dừng/tạo lại/tiến độ. Kiểm tra cú pháp toàn bộ shell/workflow và nội dung nhúng gói. Chưa thử máy Windows người dùng, Google thật hoặc trình cài Windows. Cộng dồn từ .62 trở lên.

SHA-256: 28831141b557b560c4d24da4ae0a61c49a48eaf5b08306cc8ed58e80e50ecbfc
