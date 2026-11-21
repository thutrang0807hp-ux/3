# SceneForge .141 — tiến độ ảnh khung

Thanh tiến độ trên node Ảnh khung đếm cảnh đã xử lý (ảnh nhận + cảnh lỗi), ghi riêng số ảnh nhận được/cảnh lỗi, trạng thái hoạt động/dừng/lỗi/hoàn tất và thời gian thực. Đồng hồ cập nhật mỗi giây khi đang chạy, không render lại toàn node. Hiển thị bước đang gửi prompt, gửi tạo ảnh hoặc dò kết quả và số giây từ phản hồi động cơ gần nhất. Chỉ là phản hồi động cơ, không chứng nhận Gemini đang tính toán. Không bịa phần trăm trong nội bộ một yêu cầu Gemini.

Hiển thị cảnh hiện tại dùng vai trò tham chiếu nào và bao nhiêu ảnh vai trò ngoài ảnh nguồn. Vai trò/bytes vẫn dùng chính generationRefs ở .139. Chuẩn bị ảnh trong app không có nghĩa đã gửi thành công hoặc model tạo đúng sản phẩm.

Lỗi Kho máy chưa sẵn sàng/chưa gửi AI dừng toàn node ngay ở cảnh đầu, không lặp cùng lỗi qua mọi cảnh. Thông báo yêu cầu xử lý kho trong Cài đặt → Dữ liệu & dung lượng. Không tự khắc phục bằng cách bỏ kiểm tra xung đột hoặc mất quyền lưu. Lỗi mỗi cảnh khác vẫn được ghi chi tiết như .140; hiển thị lỗi gần nhất, có mục mở chi tiết để tránh chữ tràn.

Đóng app trước khi cập nhật. Node Ảnh khung → Tạo lại toàn bộ để xem tiến độ mới. Nếu báo Chưa gửi AI/kho chưa sẵn sàng, xử lý trạng thái kho trước; đồng hồ hoặc thanh tiến độ không phải bằng chứng ảnh đang sinh bên Gemini.

Đã kiểm thử Chromium: thanh tiến độ và trạng thái hoạt động khi POST treo, đếm đúng ảnh/lỗi sau lượt một cảnh thất bại, lỗi kho chỉ thử một cảnh rồi dừng; hồi quy dừng/tạo lại/giữ lịch sử/phản hồi muộn; xác nhận brief lời mới/facts và bytes ảnh sản phẩm đi vào yêu cầu tạo ảnh trong mô phỏng. Kiểm tra cú pháp toàn workflow và nội dung nhúng gói. Chưa tạo ảnh Gemini thật hoặc chạy trình cài Windows. Cộng dồn từ .62 trở lên.

SHA-256: 0e88c93a7df088c3a35347c30fa7cd7a0bd2f5a0ac6105307954e513d26d7efc
