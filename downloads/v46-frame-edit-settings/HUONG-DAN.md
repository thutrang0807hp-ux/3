# SceneForge .166 — kích thước ảnh yêu cầu và chỉnh chung nhiều cảnh

Đóng SceneForge, chạy cập nhật và chọn đúng thư mục đang dùng. Không cần tải lại tiện ích hoặc kết nối lại Gemini.

## Kích thước ngay trên node Ảnh khung

Mặc định 1080 × 1920, dọc 9:16. Chọn 1920 × 1080 ngang, 1080 × 1080 vuông, 2160 × 3840 / 3840 × 2160 hoặc nhập rộng × cao tùy chỉnh. Bấm Áp dụng kích thước chung. Các cảnh đang dùng chung cập nhật; cảnh có kích thước riêng vẫn giữ riêng. Đổi chung cũng bỏ kích thước theo nhóm trước đó để các cảnh kế thừa đúng lựa chọn mới.

Trong từng cảnh cũng có ô chọn kích thước; thay lựa chọn sẽ cập nhật đầu vào prompt. Chọn Dùng kích thước chung để bỏ kích thước riêng. Rộng/cao 256–8192 px, tối đa 32 triệu điểm ảnh.

Kích thước và tỉ lệ được ghi vào prompt và chuyển qua backend tới đúng hàm gửi Gemini; không còn gửi tỉ lệ mặc định 9:16 khi bạn chọn ngang/vuông. Đây là yêu cầu tạo ảnh; Gemini có thể trả kích thước khác. App hiển thị kích thước tệp thật và thông báo chênh lệch, không giả số hoặc tự phóng ảnh. Tỉ lệ gần 9:16 được ghi ≈ 9:16 thay cho phân số khó đọc.

## Thay đổi chung nhiều cảnh

Chỉnh chung → nhập yêu cầu một lần, chọn các cảnh cần áp dụng → Lưu. Ví dụ: đổi phần tay đang thấy thành bàn tay nữ, móng ngắn màu nude, giữ cách cầm và góc máy.

Bật Áp dụng đổi người / phần cơ thể đang xuất hiện nếu cần thay đồng loạt: các cảnh đã chọn bỏ lựa chọn Giữ nguyên người và nhận ảnh Người chung nếu có. Cảnh chỉ thấy tay vẫn chỉ có tay, không thêm cả người. Các mục giữ nguyên khác vẫn được ưu tiên. Có thể tắt Dùng yêu cầu chung trong một cảnh hoặc nhập yêu cầu riêng để ưu tiên cho cảnh đó.

Lưu chưa tạo ảnh, chưa dùng thêm lượt. Tạo lại cảnh đã chọn… có xác nhận trước khi gửi, giữ ảnh/lịch sử cũ. Cảnh đang chờ nhận kết quả phải nhận xong trước khi đổi kích thước hoặc áp dụng thiết lập chung.

## Ưu tiên đúng sản phẩm

Mặc định chỉ gửi một ảnh sản phẩm chính; chọn ảnh chính ở Chỉnh chung. Có thể bật gửi các góc bổ sung nếu chắc chắn đó là cùng mẫu sản phẩm. Không trộn các phiên bản bao bì/màu khác nhau.

Prompt chỉ lấy bố cục/góc máy/hành động từ khung nguồn; sản phẩm lấy hình dáng, tỉ lệ cao/rộng, nắp, màu, chất liệu, nhãn từ ảnh chính. Không chỉ đổi chữ/màu trên vỏ đồ cũ. Bỏ tay, nền và chữ quảng cáo xung quanh sản phẩm trong ảnh tham chiếu. Có ô kích thước thật của sản phẩm nếu bạn biết, để hướng dẫn tỉ lệ với tay/bối cảnh. Không tự đoán chính xác số cm từ một ảnh không có thước.

Giữ khung prompt hiện tại, bổ sung chỉ dẫn chất lượng ảnh rõ nét, chất liệu thật và chi tiết cao. Không thêm bước AI viết lại trước mỗi lượt. Các bản sửa tay được giữ; thiết lập ảnh được ghép vào phần yêu cầu cuối. Chất lượng thay thế, màu và chữ nhỏ vẫn cần kiểm trên ảnh thật; kiểm thử kỹ thuật không chứng minh Gemini sẽ sao chép sản phẩm chính xác tuyệt đối.

## Kiểm tra

Đã kiểm thử backend/account/ledger thật với node trên Chromium và Gemini/tiện ích mô phỏng: 1080 × 1920 mặc định; chuyển ngang tới đúng tỉ lệ trong câu gửi gốc; yêu cầu chung đúng phạm vi; ưu tiên ảnh chính và một ảnh sản phẩm; sửa riêng không lan; kết quả sai kích thước được báo; không phát sinh lượt khi chỉ lưu; lượt chờ cũ giữ chữ ký. Ô kích thước trên node đổi cảnh chung và giữ cảnh vuông riêng. Chưa chạy Gemini thật hay bộ cập nhật Windows trên máy bạn.

Cơ chế gửi/nhận và tài khoản không đổi. Backend chỉ bổ sung kiểm tra và chuyển tỉ lệ của node ảnh. Gói gộp dùng từ .62 trở lên, giữ dự án/tài khoản/model.
