# SceneForge .168 — ảnh sản phẩm chính và dữ kiện từ Kịch bản

Đóng app → chạy cập nhật → mở lại cảnh cần làm → kiểm tra ảnh chính → chủ động tạo lại nếu cần. Không tự gửi lại hoặc xóa ảnh cũ. Không cần cài lại tiện ích hay đăng nhập lại Gemini.

## Dữ kiện sản phẩm

Luồng tạo khung trực tiếp giờ tự lấy các dòng thông số vật lý từ Thông tin có căn cứ trong node Kịch bản: khối lượng, dung tích, số đo, chất liệu, màu và mô tả nắp/hình dáng. Các dòng chỉ chứa giá/ưu đãi không đưa vào chỉ dẫn ảnh. Có mục thu gọn trong từng cảnh để xem các thông số được lấy. Tên sản phẩm trong kịch bản không được dùng để viết đè nhãn thật của ảnh tham chiếu.

Ảnh chính quyết định hình dáng, tỉ lệ, thiết kế nắp, màu, chất liệu và nhãn. Số đo cao/rộng/đường kính được người dùng cung cấp dùng cho kích thước thực tế. Khối lượng 200 g hoặc dung tích 200 ml không xác định chiều cao/đường kính; prompt không được đổi chúng thành số cm bịa ra. Thông số không tự in thành chữ mới trên sản phẩm. Số đo nhập riêng ở Chỉnh chung có ưu tiên khi mâu thuẫn với số đo trong phần Kịch bản.

Đây là bổ sung dữ kiện vào yêu cầu gửi Gemini; chất lượng tái tạo hình dáng/chữ nhỏ vẫn phải kiểm bằng mắt. Không có đảm bảo sao chép chính xác tuyệt đối hay giữ nguyên pixel sản phẩm bằng prompt.

## Ảnh chính

Đã sửa đường chọn ảnh: khi bộ lọc riêng từ bản cũ không chứa ảnh chính chung đã chọn, app lấy đúng ảnh chính trong kho tham chiếu chung, không âm thầm đổi sang ảnh khác. Nếu ảnh chính đã mất, chặn tạo và yêu cầu chọn lại. Ảnh riêng được chọn rõ trong từng cảnh vẫn ưu tiên hơn ảnh chung. Mặc định chỉ một ảnh sản phẩm chính; góc bổ sung vẫn là lựa chọn chủ động của bạn.

Hiển thị tên ảnh chính và lỗi lựa chọn trong cảnh. Lượt mới lưu danh sách tên/ID ảnh tham chiếu và bản ảnh kết quả để đối soát. Lượt cũ đang chờ giữ nguyên lựa chọn/chữ ký lúc gửi; cập nhật không thay đổi yêu cầu đã gửi hoặc tự gửi lại.

## Kiểm tra

Node thật trên Chromium + backend/account/ledger thật với Gemini/tiện ích mô phỏng: dữ kiện 200 g, cao 9 cm, đường kính 7 cm đến câu gửi gốc; ưu đãi không thành chi tiết ảnh; cảnh có bộ lọc đỏ cũ vẫn gửi ảnh chính xanh đã chọn; ảnh chính thiếu bị chặn; ảnh riêng vẫn giữ; metadata tham chiếu gắn với kết quả; nhận lượt chờ cũ không đổi chữ ký. Các chức năng kích thước/chỉnh chung/xem ảnh lớn từ .166/.167 tiếp tục qua kiểm thử.

Không chạy tạo ảnh trên tài khoản Google thật hoặc bộ cập nhật Windows của bạn. Bản này sửa chọn ảnh và truyền thông số, chưa chứng minh lỗi hình dáng/màu/chữ của Gemini đã hết. Backend, tài khoản, tiện ích và hàm gửi/nhận không thay đổi so với .167. Gói gộp từ .62 trở lên.
