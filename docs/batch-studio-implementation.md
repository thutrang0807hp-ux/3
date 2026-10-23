# SceneForge · Tab Tạo hàng loạt · 23/10/2026

Có tab riêng ngay trong SceneForge, dùng chung thanh bên, sản phẩm, bộ ảnh, bộ cảnh và kho lưu trữ. Trang chủ bốn cột, workflow node và Dựng được giữ. Không sử dụng mã nguồn Phoma; repo được giới thiệu chỉ có README/bộ cài, không đủ cơ sở xác định hoặc tích hợp implementation của họ.

## Cách thử

Mở nút **Hàng loạt** ở thanh trái hoặc URL `?demo=1#batch`. Bấm **Thử ngay 6 cảnh mẫu**: app nạp prompt, thêm sáu việc và chạy mô phỏng tối đa ba việc cùng lúc. Có thể tự nhập mỗi prompt một dòng rồi thêm vào hàng chờ. Số lượt đồng thời chỉnh từ 1 tới 4. Tab video hiện chỉ tạo ảnh minh họa cho job video, không tạo MP4.

Giao diện tối/lime được đổi thành hai vùng: cột trái chuẩn bị lượt tạo, bên phải là gallery ảnh lớn theo prompt. Không còn cột preview hẹp và danh sách thumbnail nhỏ chiếm giữa. Header / thanh công cụ và nút thêm hàng chờ giữ cố định; form và gallery cuộn riêng. Bấm ảnh mở hộp xem chi tiết. Màn hình nhỏ xếp hai vùng theo chiều dọc. Trạng thái và kết quả mô phỏng được ghi nhãn, không hiển thị credit/quota hoặc account giả.

## Đã hoạt động

- Nhập nhiều prompt (tối đa 60 dòng/lượt, 4.000 ký tự/prompt; bản thử giữ tối đa 200 việc). Chọn sản phẩm, ảnh hoặc job video xem thử, tỉ lệ 9:16 / 16:9 / 1:1.
- Thêm tối đa tám ảnh tham chiếu PNG/JPEG/WebP, mỗi file tối đa 6 MB; kiểm tra ảnh đọc được và tạo thumbnail nhỏ. Khi không chọn ảnh riêng, dùng ảnh sản phẩm tại thời điểm thêm job. Job giữ bản tham chiếu riêng, thay form/sản phẩm sau đó không đổi job cũ.
- Scheduler mô phỏng có giới hạn đồng thời; các việc độc lập chạy song song. Khi chọn nối cảnh, mỗi việc chờ kết quả của việc trước cùng lượt; lấy poster đó làm tham chiếu cho ảnh xem thử tiếp theo. Phụ thuộc bị hủy/lỗi thì chặn các việc sau, không bỏ qua liên kết.
- Tạm dừng chỉ ngừng nhận thêm việc; việc đang chạy được hoàn tất. Hủy từng việc, lọc trạng thái, xếp lại có chủ động. Tải lại trang chuyển việc đang chạy thành bị ngắt, giữ chờ và **không tự chạy tiếp**. Không có yêu cầu provider nào để gửi lại.
- Mô phỏng tạo PNG thật bằng Canvas, có chữ nhận diện mô phỏng, dựa trên tham chiếu và prompt để minh họa bố cục. Đây không phải mô hình AI, không suy luận nội dung prompt và không bảo đảm đồng nhất nhân vật. Tiến độ là tiến độ bộ mô phỏng, không phải tiến độ Veo/GPT/Grok.
- Xem/tải ảnh PNG xem thử. Có thể nhập ảnh/video thật từ máy vào từng việc, giải mã để lấy preview, lưu file bằng key phiên bản mới; giữ các file kết quả trước. Video nhập MP4/WebM tối đa 100 MB. Đóng preview/tab dừng phát và giải phóng URL tạm.
- Chỉ tư liệu **đã nhập** có nút thêm vào Bộ ảnh/Bộ cảnh sản phẩm. Ảnh mô phỏng không tự được thêm vào các bộ dùng tạo thật. Thêm chỉ bổ sung master; các phòng đã có tiếp tục giữ bộ riêng. Không ghi đè file phiên bản cũ khi nhập bản khác.
- Lấy nội dung prompt/cảnh đã lưu từ một phòng làm bản nháp, không sửa phòng nguồn. Xuất danh sách JSON gồm metadata; đây không phải ZIP đủ media. ZIP thư viện đầy đủ đã có vẫn là cách mang cả file sang máy khác.

## Dữ liệu và giới hạn

Metadata nằm trong store `prefs`, key `batch-studio-v1`; ảnh gốc và kết quả là Blob/File trong store `files` của app. Bộ chạy cục bộ tự checkpoint qua thư viện SQLite/kho hash đang có. Khôi phục sang profile trình duyệt mới giữ metadata và byte ảnh. Bản `?demo=1` dùng namespace thử tách biệt. Dữ liệu tab không hợp lệ/phiên bản tương lai được từ chối mở mà không ghi đè bản lưu.

Đây là **mô phỏng tương tác**, không có adapter tạo ảnh/video thật. Các lựa chọn Google/Veo, Grok, ChatGPT đều khóa và ghi chưa kết nối. Không gửi prompt/ảnh ra các dịch vụ đó, không đăng nhập hoặc thay đổi tài khoản, không tạo fingerprint, không thêm retry tính phí. Chưa có đồng bộ job với hàng chờ provider hoặc tự chèn kết quả vào node/timeline. Không lấy timer mô phỏng làm bằng chứng provider hỗ trợ bốn lượt/tài khoản.

Các việc mô phỏng chạy trong trang, không chạy tiếp khi đóng trình duyệt. Quy tắc phụ thuộc/giới hạn này minh họa cơ chế điều phối cho adapter tương lai; mức đồng thời thật phải theo dịch vụ, model và hạn mức tài khoản đã xác minh. CPU/FFmpeg companion vẫn dùng ngân sách một việc nặng riêng như bản trước.

## Kiểm thử

- `check_batch_studio.py`: ba mô phỏng đồng thời, dừng nhận việc mới, sáu PNG thật, hủy cha chặn con, tham chiếu và nhập ảnh/video thật, giữ phiên bản, thêm vào master giữ snapshot phòng cũ, tải lại không tự chạy, quay về board bốn cột, responsive và không gọi API trong demo. Kiểm tra từ chối metadata có ID chèn HTML và giữ nguyên bản lưu.
- `check_batch_local.py`: companion + Chromium, checkpoint metadata/PNG xuống SQLite, mở profile mới khôi phục đúng Blob và trạng thái, không gửi provider.
- Hồi quy `check_home_archive.py`, `check_shell_alignment.py`, `check_workflow_navigation.py`: giữ DOM/focus/vị trí cuộn, header/rail/logo, iframe/camera và dữ liệu hai workflow.

Các kiểm tra thực hiện trên Linux/Chromium. Không kiểm chứng đăng nhập, model hay hạn mức nhà cung cấp; không công bố đã hoàn thành engine thật.

## Cập nhật gallery theo phản hồi ảnh Phoma

Chọn cơ chế hữu ích quan sát được trong ảnh, tự triển khai trong SceneForge; không khẳng định đã đọc mã nguồn hay tích hợp engine Phoma.

- Nhập từng dòng hoặc JSON mảng chuỗi / object `{ "prompt": "…", "refs": [1,2] }`. Kiểm tra toàn bộ trước khi thêm, JSON sai không tạo một phần công việc. Giữ chế độ nhập cùng bản nháp qua tải lại.
- Một prompt có 1–4 kết quả, nhóm ảnh riêng với tên prompt, sản phẩm, tỉ lệ, trạng thái và số tham chiếu. Công việc bản cũ vẫn xuất hiện, không xóa hoặc đổi file.
- Tham chiếu dùng chung, ghép 1–1 theo thứ tự ảnh đã chọn, hoặc tự chỉ định refs trong JSON (số thứ tự 1-based theo gallery ảnh tham chiếu). Ghép 1–1 yêu cầu số ảnh bằng số prompt. Mock Canvas chỉ minh họa ảnh đầu tiên, hoặc kết quả trước khi bật nối; không phải mô hình hợp nhất nhiều ảnh.
- Cài đặt gọn trong mục mở rộng: đồng thời 1–4, 1–60 prompt / nhóm, nghỉ giữa nhóm và giãn lần bắt đầu 0–60 giây. Nhóm sau đợi nhóm trước kết thúc; giãn việc và nghỉ nhóm chạy thật trong bộ mô phỏng. Không lấy đây làm hạn mức provider.
- Chọn kết quả / tải nhóm thành một ZIP chứa byte PNG, JPG, WebP, MP4 hoặc WebM hiện có và prompts.json; tối đa 256 MB / ZIP. Kiểm tra thiếu file trước khi xuất. Tạo lại thêm công việc mới, giữ job và mọi phiên bản trước; không tự gọi AI.
- Trạng thái tổng hợp gọn; lọc, chuyển cỡ hiển thị, tạm dừng và hủy vẫn hoạt động. Không thêm tài khoản giả hay cơ chế tăng tốc đa tài khoản chưa được kiểm chứng.

Kiểm thử bổ sung `check_batch_gallery.py`: JSON lỗi không thêm job, 1–1 / custom đúng tham chiếu, hai kết quả mỗi prompt, khoảng nghỉ thực tế, ZIP CRC và byte PNG, tạo lại giữ kết quả cũ, giữ checkbox tham chiếu khi paint, header không di chuyển khi cuộn, responsive 760/1000/1440/1920. Các kiểm tra batch trước và checkpoint cục bộ vẫn được chạy.
