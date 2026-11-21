# SceneForge .139 — kịch bản mới và sản phẩm sang ảnh khung

Nối product_adaptation gồm dữ kiện sản phẩm và lời newText của cảnh vào brief viết prompt. Đưa nội dung này vào chữ ký prompt để đổi lời hoặc dữ kiện không dùng lại prompt cũ. Cảnh có sản phẩm (cờ hasProduct, vai trò tham chiếu hoặc mô tả sản phẩm trong phân tích) tự kết nối ảnh product trong bộ tham chiếu của phòng, đúng thứ tự R và đúng bytes; không thêm sản phẩm vào cảnh không quan sát thấy sản phẩm.

Ảnh nguồn chỉ cung cấp bố cục/tư thế/ánh sáng. Chỉ dẫn viết không khôi phục nhãn/công dụng/bao bì mẫu. Xóa phần mô tả sản phẩm mẫu khỏi observed_geometry khi có thay thế; hình dáng/nhãn lấy từ ảnh sản phẩm mới, không suy từ lời thoại. Lời mới là ngữ cảnh cho hình, không phải yêu cầu viết chữ lên ảnh. Không bảo đảm model luôn tuân thủ hoặc viết đúng nhãn.

Prompt chưa cập nhật không còn hiển thị prompt mẫu như bản đang dùng. Nếu cảnh cần thay sản phẩm mà thiếu ảnh, chặn và báo thêm ảnh ở node Ảnh tham chiếu. Áp dụng lời mới bỏ duyệt khung ở cảnh đổi lời, giữ phiên bản ảnh/clip cũ. Khung nguồn đã duyệt không khiến bỏ qua tạo ảnh khi chữ ký ảnh không khớp.

Có nút Tạo ảnh theo sản phẩm trong cửa sổ xem khung, đi qua cùng pipeline chuẩn bị prompt rồi gửi tạo ảnh. AI tối ưu chỉ viết prompt. Lượt ảnh chưa rõ vẫn chặn gửi trùng; nút viết lại prompt chỉ cho viết mới sau kiểm tra trạng thái và xác nhận riêng nếu kết quả cũ là unknown. Không biến lỗi xác thực Gemini thành thành công.

Cách dùng: đóng app cập nhật; rà/áp dụng lời mới trong node Kịch bản; thêm ảnh đúng sản phẩm trong node Ảnh tham chiếu; vào Ảnh khung để tối ưu rồi tạo ảnh hoặc dùng Tạo ảnh theo sản phẩm. Prompt sửa tay vẫn được giữ và yêu cầu rà khi đầu vào đổi. Nếu Gemini chưa xác thực hoặc lượt cũ chưa rõ, phải xử lý trạng thái đó trước khi tạo tiếp.

Đã kiểm thử Chromium với workflow thật: prompt mang lời mới/facts; đúng ảnh sản phẩm trong generationRefs và request tạo ảnh; đổi dữ kiện/lời làm prompt cũ không còn hiện hành; thiếu ảnh bị chặn; khung nguồn từng duyệt không bỏ qua nhánh gửi ảnh mới. Hồi quy lớp prompt, người/trang phục/khung chuẩn, áp dụng lời và giữ phiên bản cũ. Kiểm tra cú pháp script và nội dung nhúng gói. Chưa gọi Gemini tạo ảnh thật hoặc chạy trình cài Windows. Cộng dồn từ .62 trở lên.
