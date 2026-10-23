# Từ ảnh & ý tưởng và thu gọn dự án · 24/10/2026

## Ảnh / kịch bản / Storyboard / clip / dựng

- Bộ ảnh sản phẩm vẫn là kho dùng chung ở trang sản phẩm. Mỗi phòng dùng bản sao, có thể chọn lại bộ hiện tại hoặc thêm file PNG/JPEG/WebP trên máy. Ảnh mới giữ file gốc trong thư viện; preview giảm kích thước chỉ phục vụ hiển thị.
- Kịch bản tự viết/dán, thêm/xóa/sửa nhịp; hoặc chọn bản từ Kho (gồm công thức trích từ video mẫu). Chọn Kho chép sang bản riêng, giữ lời ví dụ/bản lời đầy đủ khi có; không tự gọi Gemini API. Lưu vào Kho tạo bản mới, không ghi đè công thức nguồn.
- **Gemini Chat → Storyboard** tạo gói yêu cầu + dữ liệu kịch bản/ảnh tham chiếu theo vai trò. Người dùng chép vào chat và đính kèm ảnh, nhập JSON về. Kiểm tra id, số nhịp, thời lượng và lời chính xác; xem trước rồi mới áp dụng, chặn nếu dự án đổi trong lúc rà. Không giả vờ đã kết nối Gemini Chat hoặc xác minh model Lite/gói miễn phí.
- Storyboard có prompt ảnh và chuyển động sửa riêng. Node **Ảnh khung → Clip Muse** nhập ảnh, giữ phiên bản, duyệt một bản; chuẩn bị prompt clip và tải khung đã duyệt; nhập/chọn clip theo nhịp. Nhập ảnh/clip không tự coi là đã duyệt. Đổi ảnh khung bỏ lựa chọn clip cũ.
- Prompt ảnh thêm HD tự nhiên và yêu cầu không watermark/logo góc/chữ ký/phụ đề/chữ trang trí; giữ nhãn thật. Prompt clip có hình, động tác, mốc đầu/cuối, thời lượng, chỉ dẫn không logo/phụ đề/nhạc nền. Prompt không bảo đảm bỏ được dấu do nhà cung cấp chèn.
- Giữ tiếng clip hoặc dùng giọng riêng/tắt tiếng. Chỉ dẫn lời chính xác được đưa vào prompt khi chọn tiếng clip. Chọn clip riêng đủ thời lượng rồi ghép; Bộ cảnh dùng chung vẫn là đường dùng lại clip theo nhãn có sẵn.
- Node **Phụ đề**: bật/tắt, bốn mẫu chữ, cỡ/vị trí, sửa chữ/mốc riêng hoặc lấy lại từ kịch bản. Mốc từ kịch bản là nháp; chưa tự căn theo âm thanh thành phẩm. Chặn bản chữ riêng đã cũ trước khi ghép.
- Node **Nhạc nền**: thư mục/nhiều bài, nghe thử, chỉ định/ngẫu nhiên/tắt, âm lượng. Nhập bản sao, không theo dõi thư mục ngoài app; chọn lại khi thêm nhạc. Giới hạn 100 bài, 100 MB/bài, 300 MB/lượt. Nhạc và phụ đề sang editor thành track riêng; nhạc dài cắt theo độ dài video.
- **Muse Meta chưa có adapter được xác minh.** Repo đã khảo sát nhắm muse.ai; chưa xác nhận đúng dịch vụ/tài khoản người dùng. Luồng mới chuẩn bị và nhận file thật, không tự gửi tạo video, không hứa miễn phí/vô hạn. Gemini API và VieNeu đã có vẫn là đường tùy chọn, không tự dùng thay Chat.

## Lưu trữ

- Chuyển vào Lưu trữ giữ nguyên tư liệu. Trạng thái **Còn sửa được** hoặc **Chỉ giữ thành phẩm** hiện trên từng dự án. Sau xuất có nút chuyển vào Lưu trữ; không xóa file lúc xuất.
- **Thu gọn ngay** yêu cầu xác nhận đã xem thành phẩm, giải mã được file thật, đối chiếu hash, xem danh sách/ước tính dữ liệu trước khi chốt. Không có file xuất/đang chạy hoặc chờ tác vụ/chưa rõ kết quả thì chặn. Có chọn nhiều dự án; xử lý tuần tự, dừng và báo phần đã làm nếu có lỗi.
- Giữ video xuất trong app, SRT nếu có, ảnh đại diện nhỏ, toàn bộ lời/kịch bản/prompt/nội dung chữ trên timeline, snapshot công thức. Xóa timeline chỉnh sửa và tư liệu riêng của dự án. Không xóa Bộ ảnh/Bộ cảnh, Kho kịch bản, file được phòng khác tham chiếu hoặc file ngoài app. Có tải JSON kịch bản và lưu bản riêng lại vào Kho.
- Lịch 1–3650 ngày tùy chỉnh, hoặc dọn ngay. Mặc định không tự dọn. Tự dọn phải bật rõ ràng và xác nhận thành phẩm; ghim chặn lịch. Mở lại chỉnh/khôi phục tạm dừng lịch; khôi phục từ sao lưu cũng tạm dừng. App tắt không có tác vụ nền; kiểm tra lúc mở và mỗi phút.
- Mốc bắt đầu lịch là lúc lưu cấu hình, không phải mốc xuất cũ. File xuất đổi hash sẽ chặn lịch và yêu cầu rà lại. Chỉ chạy khi dự án đã vào Lưu trữ (hoặc sản phẩm đã lưu trữ).
- Journal ghi bền trước khi sửa các database. Lỗi/gián đoạn trước commit phục hồi dữ liệu; sau commit dọn journal. Checkpoint SQLite tạm hoãn trong đợt ghi nhiều database. Phát hiện dự án/bản dựng/tham chiếu chia sẻ mới sẽ yêu cầu xem lại kế hoạch.

## Dung lượng trên máy

- Ước tính trong dự án có thể tính trùng nội dung, không phải cam kết số byte trống trên ổ.
- Bản cục bộ: lấy các hash tư liệu cũ, checkpoint trạng thái đã chốt, chỉ dọn hash không còn tham chiếu. Endpoint `release-compacted` có CAS revision, chỉ nhận dự án đã compact và danh sách hash đã ghi; bảo vệ tham chiếu live/Thùng rác, ghim và toàn bộ sao lưu metadata. Không đụng file ngoài app/thư mục bản sao đã xuất.
- Giao diện báo **số byte thật được dọn trong kho máy** và số file được bảo vệ. Có thử dọn lại kho cho dự án đã chốt nếu lần trước lỗi hoặc sau khi hết bảo vệ sao lưu. Sao lưu còn tham chiếu thì file vẫn giữ; không tự phá sao lưu để đạt số dung lượng đã ước tính.
- Bản web: xóa dữ liệu dự án trong IndexedDB, trình duyệt quyết định thời điểm thu hồi bộ nhớ. Không tự xóa file đã tải về máy.

## Kiểm chứng

- `scripts/app-shell/check_photo_archive_lifecycle.py`: gói Chat và preview, không sửa recipe nguồn, ảnh/clip/WAV thật, duyệt/chọn riêng, phụ đề không đổi lời, bản chữ cũ, reload; giữ export/SRT/lời/prompt/file chia sẻ; yêu cầu xác nhận/hủy/không export; journal; thu gọn nhiều dự án.
- `scripts/app-shell/check_archive_local.py`: SQLite thật, journal khôi phục trong profile mới, lịch có consent/hash và ghim, compact đúng hạn; kho máy giải phóng file, profile mới còn video + script và không còn nguồn trung gian.
- `python -m local_engine.check_archive_release`: dọn đúng hash đã thu gọn; bảo vệ hash chung/ghim/sao lưu/thành phẩm, không dọn orphan khác, CAS và chặn dự án còn chỉnh sửa.
- `scripts/app-shell/check_home_archive.py`: giao diện trang chủ ổn định, cuộn/focus, khôi phục và xóa đúng phạm vi, màn nhỏ.
