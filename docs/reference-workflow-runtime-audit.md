# Kiểm lại quy trình video mẫu và model

Cập nhật 26/10: xem `reference-flow-improvements.md` và báo cáo mới về tiếp tục CPU, receipt lưu/dọn, evidence/hash Worker và chia clip. Các mục dưới ghi đợt kiểm trước, không phải mọi hạn chế vẫn giữ nguyên.

Ngày 25/10/2026. Kiểm trên Linux phát triển; không coi là đã cài trên Windows của người dùng.

## Đã sửa

- Video local có đường gửi binary tối đa 500 MB/10 phút/120 fps/8,4 triệu pixel, không base64 cả file. Backend FFmpeg tạo bản đo cạnh tối đa 480 px, tối đa 24 fps. Bản gốc trong dự án giữ nguyên; ảnh nguồn được lấy lại từ nguồn, không lấy từ proxy để xuất thành phẩm. Proxy chỉ phục vụ đo, có sai số mốc cỡ một khung proxy; video VFR vẫn cần rà.
- Khi bộ CPU sẵn sàng, pipeline dùng kết quả CPU trực tiếp, không dò lại một lượt trong trình duyệt trước đó. Thiếu bộ CPU mới dùng dò trình duyệt và báo bước còn thiếu.
- Phân tích chuyển động vẫn là OpenCV Lucas–Kanade optical flow + RANSAC, đo chuyển động nền/lia/zoom/xoay/rung. Không phải model hiểu hành động người/tay. Gemini nhận ảnh bằng chứng và lời để suy luận nội dung; chưa chứng nhận hiểu mọi hành động liên tục.
- Thanh canvas có **Viết prompt theo bộ ảnh**: giai đoạn ảnh nhận ảnh cảnh nguồn + bộ ảnh tham khảo. Giai đoạn video bị chặn nếu chưa duyệt khung; nhận khung đã duyệt + ảnh cảnh nguồn + bộ ảnh + lời/mốc/đo chuyển động. JSON cần rà trước khi áp dụng; giữ lịch sử prompt, không tự tạo media hoặc sửa lời nguồn. Sau khi viết ảnh mới cần tạo/duyệt ảnh rồi mới viết/tạo video.
- Node Giọng đọc có VieNeu thật qua backend hiện có: đọc danh sách preset thật, tạo WAV trên CPU, nghe và giữ phiên bản. Mặc định giữ tiếng trong clip. Giọng riêng cho chọn giữ/hạ tiếng clip còn 15%/tắt, áp dụng xuống timeline. Đây là giảm âm lượng cố định, không phải duck tự động theo từng từ.
- Node Phụ đề có **Nghe tiếng clip / giọng riêng → tạo phụ đề**: Whisper nghe audio thực tế, không dịch hoặc thay kịch bản nguồn. Nhận dạng/mốc có thể sai, phải rà. Có bản phụ đề riêng và lịch sử, kiểu chữ vẫn sửa tại node/Dựng. Mỗi tệp tối đa 100 MB/30 phút. Không có auto lipsync/forced alignment bảo đảm từng từ; đây là ASR có mốc từ.

## Đã kiểm thật

- Model Whisper base đủ file, khoảng 142 MiB. Môi trường app bị thiếu thư viện CPU đã được cài lại và pip check qua. Whisper nhận dạng video qua API và trả mốc từ offline thật.
- VieNeu tạo được PCM WAV thật qua API, sau đó WAV đi qua endpoint Whisper mới và trả lời/mốc thật. Có lỗi nhận dạng: ví dụ “giọng đọc” có thể thành “dọc độc”, vì vậy không tự áp phụ đề.
- PySceneDetect, OpenCV optical flow/inpaint và RapidOCR chạy trên video/ảnh kiểm thử thật. Mốc cắt kiểm ở sai số tối đa một khung proxy. Đo camera có ngưỡng tạm, chưa chứng nhận mọi video thực tế.
- File MP4 HD tổng 200 MiB đã qua đường binary, tạo proxy và phân tích, kiểm SHA-256 nguồn, dọn file tạm. Đây là video tổng hợp 0,5 giây có free atom padding hợp chuẩn MP4 để kiểm dung lượng truyền; KHÔNG phải benchmark tốc độ video HD dài 200 MB trên PC người dùng.
- Chromium kiểm giọng riêng, rà phụ đề không đổi lời gốc, chặn prompt video trước duyệt ảnh, tham khảo ở cả hai giai đoạn, và payload giọng/tắt tiếng clip sang Dựng. FFmpeg xuất timeline thực với audio gain/phụ đề qua kiểm thử.
- Pip check môi trường app, Gemini, Muse, Flow, VieNeu đều qua.

## Cài và tự kiểm trên PC

Gói có sẵn model: chạy **local_engine/install-and-check-local.bat**. Bộ này cài thư viện vào đúng .venv app, nhập model Whisper/VieNeu đã kèm nếu có, kiểm model và ghi **local-runtime-check.json** trong thư mục dữ liệu. Không báo thành công nếu còn thiếu; không tự tải trọng số model khi gói không có. SDK/thư viện vẫn cần mạng lần cài đầu. Nếu model đã cài đúng thư mục dữ liệu thì không cần gửi/tải lại trọng số.

Gói app nhỏ không chứa model; giữ bộ model đã cài hoặc dùng gói kèm model đã cung cấp. File có trên ổ chưa đồng nghĩa app đang nhìn đúng đường dẫn: báo cáo phải chạy từ chính Python và thư mục dữ liệu của app.

## Còn chưa xác minh / chưa làm xong

- Chưa đăng nhập/generation thật Gemini/Flow/Muse trong lần kiểm này; không suy fixture thành dịch vụ online hoạt động. Muse SDK trỏ muse.ai, chưa xác nhận meta.ai.
- Chia clip vẫn có mốc khoảng 8 giây; chưa ánh xạ duration theo toàn bộ model và chưa kiểm độ khớp hình/tiếng từng nhà cung cấp. Câu vắt qua clip phải được chia lời, không tự lặp.
- Không có local VLM hiểu toàn bộ chuyển động/hành động. M2M100 dịch local và Ollama không có model chạy trong luồng; Gemini Chat là đường dịch đã chọn, không trả phí API ngầm.
- Chưa benchmark PC Windows hoặc một video thực tế dài 200 MB; codec nhập còn phụ thuộc trình duyệt và FFmpeg. Không hứa tốc độ từ dung lượng file.
