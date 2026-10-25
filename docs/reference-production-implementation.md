## Cập nhật 25/10/2026

Đường CPU mới nhận binary tới 500 MB/10 phút; đã nối VieNeu ở video mẫu, phụ đề từ audio và prompt hai giai đoạn. Trạng thái kiểm chứng hiện tại: [reference-workflow-runtime-audit.md](reference-workflow-runtime-audit.md). Nội dung cũ bên dưới mô tả bản trước.

# Từ video mẫu đến bản dựng · 23/10/2026

Giữ bộ đo cục bộ hiện có (FFmpeg/PySceneDetect/OpenCV, OCR và Whisper khi đã có model), kịch bản có mốc, các phiên bản ảnh/clip và trình dựng. Không cài thêm mô hình, không gửi yêu cầu tạo ảnh/video tự động.

## Bổ sung

- Node Phân tích có **Chuẩn bị cho Gemini Chat**: yêu cầu viết riêng prompt ảnh khung và mô tả chuyển động/máy quay, kèm dữ kiện CPU, lời hợp lệ và chỉ thị ảnh tham chiếu. Mẫu JSON giữ đúng mốc cảnh và lời nguồn. Người dùng phải đính kèm ảnh/video trong chat; bản chép không tự gửi ảnh.
- Đường nhập JSON Chat mới kiểm tra số cảnh/mốc, giữ lời gốc và thời gian nguồn nếu đã có bản chép; xem trước mô tả/prompt/lời mới rồi mới áp dụng. Kết quả hết hiệu lực nếu dự án đã sửa khi đang rà. Câu bị cách ly vẫn được giữ; không tự chuyển thành lời hợp lệ.
- Prompt ảnh tiếp tục dùng chỉ dẫn HD tự nhiên; không yêu cầu phụ đề/chữ trang trí. Prompt Veo giữ hình/động tác/giọng/lời chính xác, yêu cầu không gen nhạc nền và phụ đề, giữ chữ thật trên bao bì được yêu cầu.
- Node **Phụ đề** riêng nối Kịch bản → Phụ đề → Dựng: bật/tắt, bốn mẫu chữ, cỡ chữ/vị trí, xem mẫu, sửa riêng chữ/mốc. Không sửa lời gửi Veo. Phần lời đã chia tay theo clip được dùng đúng phần; chưa chia thì cần rà. Bản phụ đề riêng cũ không bị ghi đè khi kịch bản đổi; chặn ghép đến khi lấy lại hoặc rà/lưu bản riêng.
- Node **Nhạc nền** riêng: chọn thư mục hoặc nhiều bài, giải mã thử trước khi nhập, lưu bản sao trong tài sản dự án, không sửa file nguồn. Tối đa 100 bài, 100 MB/bài, 300 MB/lượt. Có tắt/chỉ định/ngẫu nhiên, nghe thử, âm lượng. Thư mục được nhập thành bản sao, không phải liên kết tự đồng bộ; thêm nhạc ngoài phần mềm cần chọn lại để cập nhật. Bài trùng tên/kích thước/ngày sửa không nhập lặp.
- Ghép sẵn giữ clip đã chọn và tiếng Flow. Track nhạc riêng được cắt theo thời lượng bản dựng; track chữ riêng nhận mẫu/cỡ/vị trí. Có thể kéo/sửa/tắt từng phần trong Dựng; giữ các bản clip, không cần gen lại.

## Giới hạn còn lại

- Chưa tự đăng nhập/điều khiển Gemini Chat hoặc Flow. Gemini API hiện có là đường riêng, không phải Gemini Chat; không chuyển sang API ngầm.
- Chưa tự căn lời theo tiếng clip Veo cuối, chưa tô từng từ theo giọng. Mốc phụ đề là bản nháp từ kịch bản; nghe và sửa trong Dựng. Whisper nguồn vẫn phụ thuộc model cài tại máy.
- Chưa tự giảm âm nhạc theo lời nói, chưa lặp nhạc ngắn hoặc chọn đoạn hay. Có chỉnh thủ công trên timeline. Chọn ngẫu nhiên chỉ trong danh sách bài còn tệp của dự án.
- Không thêm engine upscale. Chỉ dẫn HD không bảo đảm độ phân giải/chi tiết đầu ra.
- Cơ chế chọn mặt chuẩn và nối đuôi clip đầy đủ độ phân giải chưa được thêm ở lượt này.

## Kiểm chứng

`check_reference_production.py`: node và dây/bố cục, gói Chat, từ chối thay lời gốc không sửa dự án, phụ đề riêng/cảnh báo cũ/lấy lại, WAV thật giải mã và lưu qua reload, payload bật/tắt nhạc/âm lượng, nhập vào editor thành track audio/text riêng với cỡ/vị trí đúng; không POST API.

`check_flow_speech.py` và kiểm tra HD: giữ lời Việt chính xác, giọng và chia lời qua clip; chỉ dẫn ảnh HD không lẫn vào prompt video. Bộ `check_workflow.py` cũ không chạy đến phần dựng vì selector màn chọn workflow đã lỗi thời; không coi là kiểm tra đạt cho bản này.

## Chỉ dẫn đầu ra sạch · 24/10/2026

Prompt ảnh khung Việt/Anh và prompt Veo tự kèm yêu cầu không thêm watermark, logo góc, chữ trang trí/phụ đề; ảnh có thêm chữ ký, video có thêm huy hiệu kênh. Giữ thương hiệu thật/chữ trên bao bì. Veo chừa mép an toàn, không tự thêm chuyển động zoom 10%. Gói Gemini Chat yêu cầu cùng nguyên tắc. Đây là chỉ dẫn cho mô hình, không bảo đảm loại watermark do dịch vụ chèn. Không sửa file đã tạo, không gửi tác vụ AI hoặc tạo lại clip.
