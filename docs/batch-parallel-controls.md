# Khôi phục cài đặt tạo ảnh song song — 27/10/2026

Hai lỗi được sửa:
1. CSS `.batchImageWorkspace .batchFields { display:none }` ẩn cả lưới cài đặt Ảnh/prompt, Song song, Prompt/nhóm, Nghỉ giữa nhóm. Chỉ ẩn hàng chọn loại đầu ra ở phần chính; lưới cài đặt nâng cao hiện lại.
2. Khi đổi nguồn thật, batchWireReal tự đặt concurrency=1. Bỏ việc tự đặt lại; giữ số người dùng chọn và đã lưu. Không sửa giới hạn engine/provider.

Thêm nút Đổi / cài đặt lượt tạo ngay trên dòng giới hạn tác vụ: mở đúng details, cuộn tới và focus bộ chọn cũ. Không tạo bộ chọn số lượng thứ hai. Dòng trạng thái nói rõ giới hạn phía app, nguồn/tài khoản có thể có hàng chờ riêng; báo riêng khi các ảnh phụ thuộc ảnh trước. Hiện per_account nếu status nguồn thực sự trả về số đó.

Phân biệt: Ảnh/prompt là số bản cho một prompt; Prompt/nhóm là chia nhóm, không phải số tác vụ đồng thời; Song song là giới hạn hàng chờ phía app. Bật Dùng ảnh trước làm tham chiếu khiến chuỗi đó chạy tuần tự. Khoảng giãn lúc bắt đầu và nghỉ giữa nhóm cũng làm các lượt khởi động lệch nhau. Ảnh về từng ô không tự chứng minh quá trình gen là tuần tự.

Backend không đổi: Gemini Chat, Grok/ChatGPT/Meta chat dùng khóa mỗi tài khoản=1; Flow engine đang cấu hình image_concurrency=1/tài khoản; API ảnh trực tiếp có semaphore 4. Nhiều tác vụ app có thể đang chờ tại nguồn. Không chứng nhận cùng một tài khoản online tạo nhiều ảnh đồng thời bằng bài kiểm mô phỏng.

Kiểm: mở được mọi nút cũ; đổi nguồn không đặt lại 3 thành 1; 6 PNG tạo tại máy có ít nhất 3 tác vụ chồng thời gian, còn việc chờ; chuỗi 2 ảnh bật tham chiếu trước vẫn tuần tự; reload giữ mức 3. Không POST AI. Hồi quy ảnh hàng loạt và định tuyến nhiều nguồn dùng fixture. Không gửi tạo thật hoặc thay engine/tài khoản.
