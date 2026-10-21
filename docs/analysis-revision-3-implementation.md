# Phân tích video · bản chốt 22/10/2026

## Đối chiếu và bảo toàn

Giữ nguyên năm tệp nhận được trong `design/analysis-revision-3/1` đến `5`; SHA-256 trong `analysis-revision-3-integrity.json`. Hai ZIP được giải nén riêng để đối chiếu, không chạy mã/tệp từ tài liệu. Bản MD 13.394 byte có thêm mục 2.1–2.3 được dùng làm chuẩn; bản 9.234 byte giữ đối chiếu. Các gói cũ còn nguyên. Thay đổi trong Gói 5 chủ yếu là chỉ dẫn sang quy trình mới và bảng thử 30 mục.

Giữ giao diện trang chủ, tài khoản, hai hướng video mẫu / từ ảnh, kéo node/minimap, timeline, effect/âm thanh/chuyển cảnh, phụ đề trong trình dựng và các phiên bản clip cũ. Không xóa adapter tương thích, chức năng Ollama/rà clip đã có hoặc dữ liệu người dùng chỉ vì đặc tả mới để chúng ở giai đoạn sau.

## Luồng chính đã nối

1. CPU: PySceneDetect và FFmpeg giữ mốc, khung; RapidOCR đọc chữ; faster-whisper với Silero VAD chép lời nếu đã có model. Proxy chuyển sang tối đa 480px; giới hạn tệp, thời lượng, hủy và dọn tệp tạm giữ nguyên.
2. Máy quay: LK/RANSAC lấy khoảng 6 mẫu/giây, cân điểm trên lưới nền và kiểm độ phủ. Có hướng lia, zoom, xoay, rung và cộng dồn. Thiếu điểm/nền không rõ thì ghi không đo chắc và không tự điền prompt. Ngưỡng còn tạm, không coi thử fixture là hiệu chỉnh D9.
3. Lời: giữ no_speech_prob / avg_logprob; bộ lọc `speech_guard.json` có danh sách câu, lặp VI/ZH, chỉ số và ngưỡng điểm. Nhãn Thật chỉ là chưa thấy dấu hiệu, không xác nhận lời đúng. Câu Nghi bịa không bị xóa, có nút Giữ câu này / Giữ riêng trong Kịch bản; chưa giữ thì không vào AI, prompt Flow hoặc phụ đề. Mảnh vụn vẫn được giữ. Lời tự viết không có nguyên văn nguồn không được giả thành lời máy nghe, vẫn giữ qua lần áp dụng AI.
4. Gemini nhận 1–3 ảnh/cảnh và bản chữ/OCR/số đo, không nhận nguyên video qua đường chính. Cảnh C01… và câu L001… được gán trên máy. AI trả mã cùng phần diễn giải/dịch/prompt; app tự ráp lại nguyên văn và mốc nguồn. Mã lạ, thiếu, lặp, chuyển câu sai cảnh, tự trả thời gian/nguyên văn hoặc trường sai: báo vàng, chặn áp dụng.
5. Lưu kết quả chờ trước khi mở xem trước; reload mở lại không gửi thêm lượt. Áp dụng/khôi phục giữ clip và timeline; áp dụng phân tích mới bật kiểm ảnh trước duyệt nhanh, khôi phục trả chính sách cũ. Dự án đang có không tự đổi model hoặc bị ép chuyển chính sách.
6. Cài đặt AI thêm OpenAI key mã hóa; kiểm key đọc models.list, chọn model thật được liệt kê. Không nhúng key, không khẳng định quota hay giá. Gemini 429 miễn phí chờ tối đa hai lần, mỗi lần không quá 30 giây; mạng mất không tự gửi lại. 404 khám phá model lại một lần, chỉ gửi lại nếu model đổi. OpenAI chỉ gửi sau bấm xác nhận riêng có phí; không tự đổi nguồn, không gợi ý đổi vì 429. Lỗi có tên nguồn/HTTP/mã, chép chi tiết đã bỏ key/nội dung nguồn. Nhật ký ghi cả lỗi/429/kết quả không rõ, không coi phí chưa đọc là 0.
7. Khung nhập JPEG/PNG giữ Blob gốc, SHA-256, kích thước; ảnh xem trước riêng. Tải và đồng bộ thư mục dùng byte gốc. Dọn dữ liệu giữ ảnh gốc của khung hiện tại và lịch sử. Kiểm CPU đo kích thước đủ 2K, nét và OCR đối chiếu nhãn; thay ảnh/nhãn phải kiểm lại. Kiểm đạt vẫn cần người duyệt, không chứng minh mặt/sản phẩm hoàn hảo.
8. Mỗi cảnh mới mặc định Veo Lite; ảnh có lựa chọn Lite/Pro. Chuẩn bị hai yêu cầu khung để dùng trên Flow, có nút chuẩn bị nâng 2K / tạo lại Pro khi ảnh chưa đạt. Không tạo ảnh giả, không tự tiêu credit từ tuyên bố giá trong tài liệu.
9. Bảng thử lên 30 mục, giữ kết quả thủ công theo mã. Workbook gốc và các phiên bản cũ đều được giữ; workbook đối chiếu có trang triển khai riêng, không đánh dấu Đạt thật bằng kết quả giả lập.

## Kiểm tra

- `PYTHONPATH=/tmp/sceneforge-cpu-deps python -m local_engine.check_analysis_v3`: OpenCV thực trên nền cố định với vật thể đi qua, lia, zoom, cảnh ít điểm; JPEG/2K/nét/SHA thực; lọc VI/ZH; sai mã, giữ nguyên lời/mốc; bảo vệ POST; trả model từ danh sách; không tự gửi OpenAI, giới hạn retry429, lỗi mạng không lặp, chi tiết không lộ key. Provider dùng transport giả.
- `PYTHONPATH=/tmp/sceneforge-cpu-deps python scripts/workflow/check_analysis_v3.py`: Chromium → companion → provider giả; ảnh/bản chữ không có video; xem trước/reload/áp dụng/khôi phục; giữ câu và loại khỏi phụ đề; JPEG nhập/lưu/tải khớp byte gốc; kiểm ảnh CPU thật; sai mã chặn áp dụng; demo khóa nhập key.
- `python -m local_engine.check_cpu_analysis` và `scripts/workflow/check_cpu_analysis.py` với thư viện CPU: PySceneDetect/OCR/OpenCV thực, xem trước, lưu/khôi phục, hủy/dọn tệp. Chưa có Whisper model thật.
- Kiểm hồi quy: backend package5/aggregate/machine_checks/account_settings; trình duyệt local_ai/account_dashboard/desk_design/machine_checks; adapter video cũ và xuất MP4+SRT qua `scripts/app-shell/check_aggregate.py` (provider giả, FFmpeg/tệp thật).

`PYTHONPATH` trên là thư mục thư viện thử trong môi trường phát triển, không phải đường dẫn cần có trên máy người dùng. Cài bằng `local_engine/install-cpu.bat` / requirements-cpu.txt trên máy dùng app.

## Còn cần kết nối / đo thật

Flow/Muse tạo khung, nâng 2K, render clip, đọc quota/credit và thời gian thật chưa có adapter xác minh. Các nút chuẩn bị không giả là đã gửi tác vụ. Chưa có key thật để xác minh Gemini/OpenAI, và chưa chạy model Whisper/Ollama thật. Bộ lọc/độ nét/máy quay chưa hiệu chỉnh trên video người dùng. D8–D11/A10 giữ chưa thử thật. Các mức “miễn phí”, tên model tương lai, tốc độ và giá trong tài liệu không được dùng làm cam kết hoặc căn cứ tự chi tiền.
