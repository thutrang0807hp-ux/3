# SceneForge .143 — đối soát đồng bộ kho

Sửa các trường hợp lệch revision thông thường khiến kho tạm dừng ghi và node không gửi AI:

- Nếu checkpoint mất phản hồi nhưng đọc lại kho xác nhận đúng library_id và đúng toàn bộ nội dung đã gửi, app tự nhận biên nhận đó. Sửa đổi mới phát sinh trong lúc chờ không bị hydrate đè; giữ dirty/fullScan để lưu tiếp.
- Khi khởi động, biên nhận checkpoint của chính app cùng digest bản kho đã lưu cho phép tiếp tục giữ bản trình duyệt sửa mới hơn rồi checkpoint, thay vì coi mọi khác biệt digest là xung đột.
- Lưu mốc đồng bộ đã xác nhận trong IndexedDB riêng sceneforge-sync-baseline, theo library_id và revision. Chỉ gồm metadata/định danh media, không sao chép blob, không đưa baseline vào dữ liệu dự án. Lỗi ghi cache baseline không biến lần lưu kho đã xác nhận thành lỗi.
- Nếu có baseline đúng, gộp ba phía theo bản ghi và thuộc tính object: thay đổi riêng một phía, dự án mới độc lập, thay đổi thuộc tính độc lập được giữ cả hai. Array, blob marker, xóa/sửa và cùng trường khác nhau không bị gộp bừa. Mất baseline/không khớp định danh không tự chọn bản thắng.
- Trước gộp, lưu browser-bundle bảo vệ bản trình duyệt. Commit dùng revision hiện tại để chống ghi đè đồng thời. Kiểm tra digest kết quả và epoch trước hydrate để không đè sửa đổi mới. Giữ cơ chế một cửa sổ ghi.

Xung đột thật và lỗi cũ chưa có baseline vẫn cần lựa chọn một lần. Ngay node có Giữ bản đang sửa · đồng bộ: xác nhận dùng bản trình duyệt hiện tại, tự browser-bundle và backup kho máy trước commit; từ chối ghi khi sao lưu thất bại/có cửa sổ khác giữ quyền/có sửa đổi mới trong lúc lưu. Bản chỉ có trong kho máy cũ nằm trong backup, không tự gộp vào bản đã chọn. Sau khi thành công mở lại quyền ghi, không yêu cầu nạp kho máy hoặc tải lại trang. Có thể Tạo lại toàn bộ ngay.

Cách dùng: đóng app cập nhật. Các trường hợp đủ bằng chứng được đối soát lúc mở. Với lỗi cũ vẫn hiện trên node và muốn giữ nội dung đang sửa, bấm Giữ bản đang sửa · đồng bộ, đọc xác nhận rồi tiếp tục tạo ảnh. Không phải quy trình xuất ZIP/nạp lại cho mỗi dự án mới. Dự án vẫn có bản ghi riêng, media kho chung chống trùng; bản này không chuyển thành thư mục độc lập từng dự án.

Đã kiểm thử storage thật trong Chromium với API kho giả lập: mất phản hồi commit kèm sửa mới, mở lại với biên nhận của chính app, dự án mới độc lập được gộp, cùng trường xung đột giữ cả hai, từ chối ghi khi backup thất bại, sao lưu cả hai trước lựa chọn giữ bản đang sửa, cửa sổ thứ hai không được chiếm quyền ghi. Kiểm thử node nút giữ bản: hủy xác nhận không ghi. Kiểm thử tích hợp SQLite/kho file thật và giao diện dọn/lưu trữ đã qua, không gọi dịch vụ AI. Hồi quy dừng/tạo lại/tiến độ; cú pháp shell/workflow và nội dung nhúng gói. Chưa thử trình cài Windows hoặc môi trường dữ liệu thực của người dùng.

Không hứa không bao giờ có xung đột: sửa cùng một nội dung từ hai bản hoặc mất kết nối có thể vẫn cần bảo vệ/lựa chọn. Mục tiêu là không khóa kho cho lệch revision đã chứng minh an toàn, và không làm mất sửa đổi để bật AI. Cộng dồn từ .62 trở lên.

SHA-256: 0075d90b1a96ffffc9622e9b3846e1a131254840698f0f27536e7e53b3d9ea48
