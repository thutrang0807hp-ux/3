# Local AI · triển khai từ tài liệu nhận ngày 22/10/2026

Nguồn: `Local-AI-phan-mem-tai-tao-video.docx`, giữ nguyên trong `design/local-ai-received/` cùng bản trích nội dung để đối chiếu. Bổ sung trên SceneForge hiện tại; không thay trang chủ, không tách thêm workflow, không xóa file hay clip cũ.

## Ưu tiên 1 · hướng máy quay trong prompt

Bộ CPU có optical flow/affine từ bản trước. Lần này diễn giải **hướng**: dịch nội dung ảnh sang trái → máy có vẻ lia phải và ngược lại; tương tự lên/xuống, hệ số scale dương → có vẻ zoom vào, âm → có vẻ zoom ra. Cặp điểm không đủ thì ghi chưa xác định. Đây là chuyển động ảnh 2D, không bảo đảm máy quay thực sự chuyển động: chủ thể di chuyển có thể gây nhầm.

Khi áp số đo CPU, điền Việt/Anh vào ô Máy quay còn trống hoặc câu đã sinh tự động. Không thay câu người dùng tự viết. Dự án cũ có nút **Điền hướng lia / zoom** để áp lại. Prompt Veo hiện có dùng ô Máy quay này; không gọi thêm Gemini chỉ để suy ra hướng.

## Ưu tiên 2 · rà clip sau Veo

- Sau khi nhập clip và xử lý logo nếu bật, tự lấy mẫu **5 khung** bằng bộ giải mã/canvas trình duyệt trên máy, không gửi dịch vụ. Có thể tắt tự lấy mẫu ở bảng Kiểm clip. Clip đã có trước bản cập nhật không bị tự quét/gửi model khi mở dự án.
- Gắn ảnh khung đúng phiên bản dùng tạo clip, không tùy tiện lấy ảnh mới nhất để so. Giữ reference snapshot trên từng phiên bản, bao gồm bản xử lý logo phát sinh trong lượt nhập. Thiếu nguồn/khung thì báo chưa thể kiểm, không báo đạt.
- Nút dưới từng clip mở khung đã dùng, video có điều khiển phát và dải ảnh theo giây. Số đo chỉ báo tối, ít chi tiết và **màu toàn khung** khác nhiều. Không gọi đó là xác minh mặt, màu của riêng sản phẩm hoặc logo. Không có dấu hiệu vẫn ghi **chờ bạn rà**.
- Người dùng bấm **Đạt · tôi đã xem** hoặc **Cần sửa · giữ bản này**. Quyết định lưu theo chữ ký của lần kiểm; lấy mẫu/model lại xóa quyết định cũ. Clip đánh dấu cần sửa bị chặn khi ghép tự động; có thể chọn bản khác hoặc duyệt lại. Không xóa clip hay tự tạo lại/trừ credit. Timeline đã sửa không bị đổi.
- Các lượt lấy mẫu nối hàng tuần tự, chặn đổi phòng trong khi còn việc để không ghi kết quả sang phòng khác. Kết quả và quyết định giữ sau reload.

## Ollama · đường model nhìn ảnh local

Trong node Phân tích: **Mô tả local · Ollama**, chọn cảnh và model đã chuẩn bị. Gửi 2–4 khung nguồn tới Ollama tại **127.0.0.1:11434**, nhận mô tả người/sản phẩm/trang phục/bối cảnh, quan sát Việt–Anh và prompt ảnh Việt–Anh. Có xem trước, lưu kết quả chờ áp sau reload, lưu lịch sử mô tả để khôi phục. Áp mới yêu cầu duyệt lại khung, giữ mọi phiên bản clip. Không tự viết lời thoại từ ảnh.

Trong **Kiểm clip → Kiểm sâu bằng model local**: chọn model đã có, gửi khung tạo clip, 3 ảnh clip theo thời gian và ảnh người/sản phẩm đã nối nếu có (tối đa 6 ảnh). Vai trò ảnh là enum cố định, tránh nhầm ảnh tham chiếu thành khung video. Model gợi ý khác biệt mặt, nhãn, màu, bố cục hoặc bất thường; **không có chứng nhận danh tính/logo**. Mọi kết quả vẫn cần người duyệt. Không tự gọi model khi nhập clip; bước tự động chỉ là lấy mẫu/đo trên trình duyệt.

Cài đặt → Phân tích (AI) hoặc Động cơ có nút kiểm tra Ollama. Adapter chỉ nói chuyện endpoint loopback cố định, bỏ proxy môi trường. Kiểm model đã có, có dung lượng trọng số và capability `vision`; từ chối tên `cloud`/metadata chuyển tiếp remote. Không tự pull model, không dùng tài khoản ChatGPT/Gemini web, không dự phòng sang API trả phí. Giới hạn 2–6 JPEG/PNG, tối đa 1 MB/ảnh, 1600px mỗi chiều và 2 triệu điểm ảnh. Kiểm cấu trúc JSON; lỗi/timeout không tự gửi lại hay áp dữ liệu.

Chuẩn bị riêng Ollama và model hỗ trợ ảnh phù hợp máy. App không chọn sẵn model vài GB để tự tải. Chưa có Ollama/model trên máy thì bảng báo rõ. Pillow để kiểm ảnh có trong `requirements-cpu.txt`; không thêm PyTorch/CUDA vào companion.

## Luồng và mặc định giữ đúng

Cảnh mới mặc định **Veo Fast** theo tài liệu; lựa chọn trong dự án cũ giữ nguyên. Mặc định xuất 1080p đã có. Đây là lựa chọn/prompt trong app: Flow/Veo vẫn nhập clip thủ công, chưa điều khiển dịch vụ thật hoặc xác nhận credit/chế độ 1080p. Tài liệu đưa hướng tiết kiệm, không chứng minh mức giá/quota thực.

Bộ tham chiếu người/sản phẩm chung theo dự án đã có. Giọng Flow-native vẫn giữ theo yêu cầu người dùng trước; nhạc/voiceover riêng là tùy chọn trên toàn video, không âm thầm thay giọng trong clip. Gemini API còn làm đường dự phòng hiểu/dịch/viết; không tự gửi chỉ vì local thiếu model. Duyệt ảnh vẫn trước chuẩn bị clip.

## Đã kiểm tra và chưa kiểm chứng

- `python scripts/workflow/check_local_ai.py`: Chromium giải mã video thật, nhập clip tự lấy 5 khung **không gọi API**, không tự duyệt; quyết định người dùng lưu sau reload; reject chặn ghép; hướng lia/zoom và bảo vệ câu tự viết; mô tả local xem trước/reload/áp/khôi phục vẫn giữ clip. Transport model được giả lập rõ ràng.
- `PYTHONPATH=/tmp/sceneforge-cpu-deps python -m local_engine.check_local_vision`: schema, ảnh, origin/header, endpoint cố định, chỉ model có sẵn + vision; chặn model cloud/remote, không pull, không tự fallback; đầu ra luôn cần rà. Transport Ollama giả lập.
- Hồi quy CPU, Gemini/FFmpeg xuất MP4+SRT, node/Cài đặt/bảng thử. Không dùng transport giả để đánh đạt chất lượng model.

**Ollama hiện không cài/chạy trong môi trường kiểm tra: chưa chạy suy luận model nhìn ảnh thật.** Chưa chứng minh tự bắt méo logo, sai màu riêng sản phẩm, lệch mặt trên clip Veo thật; số đo màu/ảnh mẫu không đủ để bảo đảm các việc này. Cần thử thực tế với bộ clip/ảnh chuẩn của người dùng, đo độ bỏ sót/báo nhầm.

Các phần để sau trong tài liệu vẫn chưa triển khai model: Grounding DINO/YOLO, CLIP embeddings/face matching, SAM, Flux/Qwen-Image-Edit, Wan, tìm footage theo chữ, phát hiện trùng/crowd hoàn chỉnh, beat nhạc và auto lọc/xóa cảnh. Lọc mờ/rung/tối trước đã có cảnh báo CPU, không tự bỏ cảnh. Tách ảnh local 12–24GB cần kiểm phần cứng; không hứa mọi việc chạy thoải mái trên một mức VRAM. Không thêm YOLO AGPL vào app do chỉ là gợi ý trong tài liệu, chưa chọn giấy phép/phương án phân phối.
