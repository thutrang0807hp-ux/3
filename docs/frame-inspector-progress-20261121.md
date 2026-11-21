# SceneForge .144 — tiến độ trong cửa sổ từng khung

Bổ sung vùng trạng thái ngay trên ô prompt Việt trong inspector cảnh: bước viết prompt, bước tạo ảnh, trạng thái từng lượt. Khi pipeline trong app đang hoạt động ở đúng cảnh, hiện thanh chờ không phần trăm và đồng hồ tính từ lúc bắt đầu cảnh. Cảnh khác không bị gắn nhãn đang chạy do một cảnh khác đang xử lý.

Nút Kiểm tra lượt hiện tại đọc GET jobs của writer và ảnh hiện hành, không gửi yêu cầu AI mới, không tự áp kết quả hoặc duyệt ảnh. Giới hạn chờ 8 giây, không ghi đè trạng thái nếu job đã được pipeline cập nhật trong lúc kiểm tra. Lượt đã applied/imported/abandoned không bị kiểm tra lại và đổi nhầm trạng thái. Nút Dừng trong app dùng chung cơ chế .140.

Vùng tiến độ cập nhật mỗi giây, không dựng lại textarea. Khi app hết chờ, thanh chạy biến mất; trạng thái lượt cũ vẫn được hiện để kiểm tra, không giả phần trăm Gemini tính toán. Thông báo Lượt viết cũ còn xử lý nghĩa là lần bấm vừa rồi chưa gửi thêm, không chứng minh động cơ vẫn có phản hồi mới.

Cách dùng: đóng app cập nhật, mở từng khung. Nhìn vùng trạng thái phía trên ô prompt; bấm Kiểm tra lượt hiện tại nếu cần đọc lại lượt cũ. Viết prompt và tạo ảnh là hai bước khác nhau, kết nối Gemini/kho vẫn phải sẵn sàng. Dừng trong app không bảo đảm hủy tác vụ đã gửi phía dịch vụ.

Đã kiểm thử workflow thật bằng Chromium/API giả lập: thanh chờ trong lúc POST treo, đọc trạng thái khi đang chờ mà không tạo thêm POST, dừng, hiện thất bại/hoàn tất, prompt Việt được cập nhật, không vô tình gửi tạo media. Hồi quy dừng/tạo lại cả node và lớp prompt/sửa tay; kiểm tra cú pháp workflow và nội dung nhúng gói. Chưa thử Google thật hoặc trình cài Windows. Cộng dồn từ .62 trở lên, giữ .143 đối soát kho.
