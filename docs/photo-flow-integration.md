# Storyboard tổng và kết nối Flow

## Thay đổi giao diện

Thanh đầu workspace Từ ảnh & ý tưởng có hai nút Gemini / Muse cho bước sáng tạo và hai nút Flow / Muse cho bước tạo clip. Lựa chọn lưu riêng theo video, không xóa ảnh, clip hoặc kịch bản cũ.

Storyboard là một ảnh tổng, lưu nguyên tệp và giữ các phiên bản. Yêu cầu viết prompt kết hợp storyboard tổng, ảnh sản phẩm và kịch bản. Không cắt ô bắt buộc. Prompt video từng clip có bố cục, một hành động chính, chuyển động máy, điểm kết thúc và yêu cầu giữ sản phẩm. Các góc máy chưa quan sát từ video mẫu là đề xuất, không phải dữ liệu đo được.

Node “Tạo clip theo Storyboard” thay yêu cầu bắt buộc nhập/duyệt ảnh khung từng cảnh. Ảnh khung riêng vẫn có trong mục tùy chọn để giữ dữ liệu dự án cũ. Có thể chọn clip từ Bộ cảnh hoặc nhập clip thật.

## Flow: phần đã thực hiện

- Cài repo `TheSmallHanCat/flow2api` revision `018f75539fe97d5602e0dcac6783638093bb6479` vào môi trường riêng, kiểm tra dependencies và nạp ứng dụng.
- Có bộ cài `local_engine/install-flow.bat`, trình chạy `start-flow.bat`, hoặc `python -m local_engine.setup_flow --connect --start`.
- Bộ cài pin revision, tạo key/password mới, bind `127.0.0.1:8766`, không dùng captcha thuê mặc định. Chế độ browser personal cần máy có màn hình và người dùng đăng nhập Google.
- Kết nối SceneForge đọc `/v1/models`, gửi `/v1/chat/completions`, lưu kết quả ảnh/video thật khi engine trả về; không dựng kết quả giả.
- Adapter giới hạn ba tác vụ cùng lúc; mã yêu cầu lưu bền trước khi gửi. Đóng app/timeout/chưa rõ kết quả không tự gửi lại.
- Màn rà trước khi gửi hiển thị số yêu cầu, model, ảnh tham chiếu và cảnh báo credit. Nút Kiểm tra kết quả chỉ đọc trạng thái/lấy file, không tạo mới.
- Clip nhận về được kiểm bằng ffprobe ở backend và giải mã video ở trình duyệt trước khi thêm phiên bản. Prompt/ảnh đổi trong lúc xử lý thì giữ clip như một phiên bản, không tự chọn thay kết quả cũ.

Tệp kết quả engine còn lưu trong thư mục dữ liệu `flow-results` để lấy lại khi trình duyệt đóng giữa chừng. Chưa tự dọn các bản này sau nhập; không coi thu gọn một dự án là đã giải phóng các bản engine bên ngoài kho dự án.

## Giới hạn còn lại

- Chưa có tài khoản Flow thật trong môi trường phát triển. Kiểm thử đồng thời dùng transport giả lập; không chứng nhận credit/quota, chất lượng hay đa luồng Google thực tế.
- Engine upstream vẫn là dịch vụ riêng, có database tài khoản/nhật ký riêng; mã hóa vault của SceneForge không tự mã hóa database/cookie upstream; cấu hình log debug tắt không có nghĩa database upstream không lưu prompt. Cần rà chính sách lưu và retry nội bộ trước khi dùng rộng rãi. Adapter SceneForge không retry; không khẳng định kiểm soát hoàn toàn retry của upstream.
- Gemini Chat vẫn chuẩn bị yêu cầu và nhận JSON/ảnh bằng thao tác tay; chưa tự điều khiển tài khoản Chat. Gemini API là đường riêng, không dùng gói Gemini Chat.
- Muse/Meta chưa xác định chính xác dịch vụ. Lựa chọn Muse lưu được nhưng gửi tạo bị chặn rõ ràng. Không chuyển ngầm sang muse.ai hoặc Flow.
- Ollama được để trống theo yêu cầu; không tải model.
- Chưa áp dụng UI Flow mới vào tab tạo hàng loạt hoặc workflow video mẫu. API nhận cả tác vụ ảnh và video, nhưng đường gửi mới từ giao diện hiện dành cho clip của workflow ảnh.

## Kiểm tra

- `python -m local_engine.check_flow_provider`: adapter thật với transport fixture, ba việc song song, ảnh/video thật có kiểm tra định dạng, ảnh tham chiếu gốc, duplicate/restart/timeout và URL tải không được phép.
- `scripts/app-shell/check_photo_provider_toolbar.py`: trình duyệt thật, storyboard tổng, lưu lựa chọn, rà trước gửi, nhập năm clip fixture, giữ dữ liệu cũ, Muse bị chặn.
- `scripts/app-shell/check_photo_archive_lifecycle.py`: hồi quy kịch bản, ảnh, clip, nhạc, phụ đề và thu gọn lưu trữ.
- `python -m local_engine.check_local`: bảo vệ local API, mã hóa tài khoản và trạng thái phiên chưa xác minh.

Các kiểm tra không gửi yêu cầu AI thật hoặc sử dụng credit.
