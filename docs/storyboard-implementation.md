# Kịch bản và Storyboard · B2

Đối chiếu `SceneForge_KichBan_Storyboard.md` nhận ngày 23/10/2026. Bổ sung luồng Từ ảnh, giữ nguyên trang chủ bốn cột, hai hướng tạo, editor, thư viện và các phòng cũ.

## Đã triển khai

- Storyboard là node riêng, hiện cùng lúc với Kịch bản; kéo bằng tiêu đề và lưu vị trí theo từng phòng. Nút Xem node Storyboard trong Kịch bản đưa camera tới node. Có dây từ Kịch bản/Bộ cảnh tới Storyboard, rồi tới Đạo diễn. Con lăn trong danh sách Storyboard chỉ cuộn danh sách. Các node cũ giữ vị trí đã lưu. Chung `photoDraft.beats`: lời đọc, kiểu cảnh, góc máy, chuyển động, chữ trên hình; thời lượng chỉnh qua Sửa nhịp. Storyboard lấy poster từ clip đúng kiểu trong Bộ cảnh; thiếu clip hiện khung trống có tên kiểu cảnh. Không tạo ảnh AI.
- 3 phương án: lấy công thức đầu Kho đã xếp hạng, gửi một yêu cầu Gemini cho cả ba bản và Storyboard. Mỗi bản có kiểu mở đầu riêng; nhịp đầu tối đa ba giây. Xem đủ nội dung trước khi chọn. Bản đang dùng giữ nguyên đến khi chọn; có nút giữ kịch bản trước. Không tạo clip/giọng/ghép/xuất qua các hành động này khi còn chờ chọn. Không tự gọi lại khi lỗi.
- Nút AI viết kịch bản cũ cũng nhận chỉ dẫn Storyboard trong cùng phản hồi. Kiểm tra số nhịp, kiểu cảnh, trường chữ trước khi thay bản cũ; sai phản hồi giữ bản trước.
- Ghi công thức và nguồn vào snapshot của phương án được chọn. Đánh giá sau xuất tiếp tục cộng đúng công thức.
- Kho chung và Kho trong phòng có ô lượt thích/CTR nhập tay (tùy chọn), kiểu mở đầu; để trống khác với số 0. CTR 0–100%, lượt thích số nguyên không âm. Xếp hạng: 100 × (👍−👎) + CTR/10 + log10(1+lượt thích), phần chỉ số giới hạn dưới 20 điểm. Một phiếu người dùng luôn nặng hơn chỉ số nhập tay. Không coi đây là dự đoán ra đơn.
- Kho chung có nút Từ video bạn chọn, cùng API phân tích đã có; chỉ gửi video người dùng chọn, không cào web. API trả cấu trúc/hook/góc máy/chuyển động/chữ đã viết lại; không nhận hay tự bịa chỉ số từ AI.
- Cảnh báo lời giống nguồn khi có lời gốc trong workflow nguồn (chuỗi ít nhất tám từ liên tiếp); chỉ đọc để đối chiếu trong bộ nhớ, không thêm bản chép vào recipe/draft. Video nhập trực tiếp chưa có transcript: giao diện nói rõ chưa đối chiếu được. Đây là gợi ý biên tập, không phải kiểm chứng sao chép toàn diện.
- Giữ file đặc tả gốc trong gói; dữ liệu cũ không bị di chuyển hoặc xóa. Trường mới đều tùy chọn.

## Kiểm tra

- `python local_engine/check_storyboard.py`: một lượt cho ba phương án + Storyboard, từ chối trùng hook/lời đầu, sai kiểu cảnh/thiếu bản, không tự gửi lại; tương thích nút một bản. Gemini giả lập, không gọi dịch vụ thật.
- `python scripts/app-shell/check_storyboard.py`: nhập chỉ số/lưu/validation; trọng số phiếu; sửa hai chiều khi hai node cùng hiện; kéo node bằng chuột/lưu vị trí qua reload và giữ vị trí các node cũ; cảnh báo nguồn; một lượt ba bản; chặn tạo khi chưa chọn; reload giữ bản đã chọn và Storyboard.
- `python local_engine/check_recipes.py`: API rút công thức/chặn chép nguyên lời, video/recommend contracts.
- `python scripts/app-shell/check_package6.py`, `check_workflow_navigation.py`, `check_shell_alignment.py`: dữ liệu cũ/legacy, thư viện, worker, chuyển luồng, khung ổn định và zoom được giữ.
- Bài `check_recipes.py` cũ của app-shell còn chờ class `videoMenu` trong khi Gói 6 dùng `g6NewVideo`; đây là kỳ vọng cũ, không dùng bài đó làm bằng chứng đã qua.

## Chưa kiểm chứng thực tế

Chưa thử Gemini với 10–20 quảng cáo thật hoặc đo tính ổn định/hữu ích của ba hook. Kiểm tra hiện tại xác nhận khác chuỗi và loại hook; chưa chứng minh khác ý hay hiệu quả bán hàng. Chưa kiểm tra Creative Center lọc Việt Nam. Bản web mô phỏng không gọi AI; cần bản cục bộ và key để viết thật. API miễn phí vẫn có quota/điều khoản và có thể bị giới hạn, không cam kết luôn 0đ. Không đổi trạng thái hoàn thành MVP từ video mẫu chỉ vì có tính năng B2 này.
