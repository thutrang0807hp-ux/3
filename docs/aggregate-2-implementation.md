# Gói tổng hợp nhận lại · phần mới đã triển khai

Nguồn `SceneForge_TatCa (1).zip`, SHA-256 `40e5b4d911b3d2d3c2ece1ad020955aec75575469529e4116569309918eb41b5`.

## Đối chiếu

5/7 tệp ngoài giống byte bản tổng hợp trước. Hai tệp đổi: bảng thử 22 → **25 mục** (D5 faster-whisper, D6 PySceneDetect, D7 RapidOCR/OpenCV) và Gói 5. Bên trong Gói 5 chỉ tài liệu mục 8, workbook và ảnh Cài đặt thứ ba thay đổi/thêm; không có mã app mới. Giữ nguyên toàn bộ bản cũ tại `design/all-spec-received`; bản mới tại `design/aggregate-received-2`, gồm mọi tệp và ảnh được giải nén nguyên byte. Xem `aggregate-2-integrity.json`.

Ảnh thứ ba bổ sung tham chiếu cho Giọng đọc/Thư mục/Xuất. Giữ bố cục Cài đặt hiện tại; không lấy tên giọng, giá tiền, số GB ví dụ trong ảnh làm dữ liệu thật. Những mục đã nối trước không làm trùng hoặc xóa. Không thay lại trang chủ, timeline, hai workflow và node gộp.

## Cách dùng phần mới

1. Chạy bản cục bộ, có FFmpeg + ffprobe. CPU tùy chọn cần Python **3.10–3.12**, chạy `local_engine/install-cpu.bat` sau khi đã khởi động app một lần. Linux: kích hoạt môi trường app rồi `python -m pip install -r local_engine/requirements-cpu.txt`.
2. Trong workflow **Từ video mẫu**, mở node **Phân tích → Đo trên máy · CPU**. Giới hạn 18 MB, 5 phút, ≤60 fps, ≤8,4 triệu điểm ảnh, tối đa 100 cảnh. Chọn ngưỡng/cảnh ngắn nhất; OCR và chép lời là tùy chọn. Không tự thay thuật toán cũ hoặc tải/gửi video khi mở dự án.
3. Có tiến độ, ẩn tiến độ, dừng và mở lại lượt trước. Kết quả được lưu trong dự án trước khi xem; tải lại trang mở kết quả không chạy thêm. Chọn riêng áp mốc hoặc lời; tệp nguồn/clip, bản dựng hiện tại giữ nguyên. Lịch sử cấu trúc cảnh/lời có thể khôi phục; không tự bỏ cảnh vàng. Dọn dữ liệu giữ blob của clip trong lịch sử để hoàn tác vẫn dùng được. Bản sao thư mục gồm cả phiên bản clip trong lịch sử; Dùng lại mẫu không mang lịch sử hay lượt đang chờ sang phòng mới.
4. Trong cảnh có số đo, mở **Số đo trên máy / Rà số đo**. Các mâu thuẫn và cảnh tối/mờ/rung tô vàng. Rà trước khi duyệt. Không ghi “không có người” chỉ vì bộ dò không thấy mặt.
5. OCR có chữ ở khung giữa: **Chọn chữ để che trên khung** → tích vùng, xem hộp đánh dấu và ảnh trước/sau → lưu khung mới **chưa duyệt**. Tô lấp OpenCV có thể để vệt; giữ ảnh gốc. Không tự che mọi chữ, không thay nhãn sản phẩm. Đây là ảnh tĩnh, không phải bộ xóa logo video.

## Công cụ thật và giới hạn đo

- **PySceneDetect 0.7.2**: ContentDetector, duyệt các khung của proxy CFR do FFmpeg tạo ở fps trung bình nguồn. Không gộp nhầm mọi cảnh ngắn; người dùng điều chỉnh ngưỡng/cảnh tối thiểu. Video VFR cần rà lại: chưa chứng nhận chính xác từng frame nguồn VFR. Đường dò trình duyệt cũ và Chia lại vẫn còn.
- **FFmpeg/OpenCV**: trích đầu/giữa/cuối, kích thước ảnh theo nguồn; optical flow + affine 2D ước lượng đứng yên/lia/zoom, độ sáng, Laplacian trên proxy và độ biến thiên chuyển động. Chủ thể chuyển động có thể bị nhầm là máy quay. Độ nét trên proxy không phải điểm chất lượng tuyệt đối. Bộ dò mặt Haar chỉ gợi ý mặt, không biết danh tính, sản phẩm hay người đang nói.
- **RapidOCR ONNX Runtime 1.4.4**: thư viện/model đi kèm gói cài, chạy CPU. Lấy mẫu 3 khung/cảnh, lưu thời điểm, nội dung, độ tin cậy và đa giác theo tỷ lệ ảnh. **Chưa tích hợp RapidVideOCR quét phụ đề cứng toàn video**; có thể bỏ sót chữ xuất hiện giữa các mẫu.
- **faster-whisper 1.2.1**: có adapter CPU int8, mốc từng từ và xác suất. Chỉ nạp model có sẵn bằng `local_files_only=True`; không tải model trong lượt phân tích. Chuẩn bị riêng bằng `python -m local_engine.prepare_whisper --model base --download` (tải model từ Hugging Face; base khoảng 150 MB). Không tự tạo lời Việt từ lời Trung: lời mới để trống cho Gemini/người dùng viết. Không xác định người nói/khớp miệng từ ASR.
- **Gemini**: giữ một yêu cầu đã xác nhận để hiểu, viết và dịch. Gửi kèm bản tóm tắt số đo/lời CPU nếu có (không gửi thêm lượt chỉ vì có OCR). Backend giới hạn và kiểm tra các trường số đo. Chữ OCR/lời được coi là dữ liệu không đáng tin, không phải chỉ dẫn. Lời khác nội dung/mốc >0,6s, mặt/chữ khác cờ AI, hoặc mốc khác số đo thì tô vàng để rà, không tự sửa/dùng làm chân lý.
- Khi Gemini đã xác nhận rõ **không người, không sản phẩm, không chữ cần xử lý**, không có tham chiếu thay thế, không có khung nhập và không có cảnh báo CPU: tự dùng khung gốc, ghi nhãn. Kết luận không được suy từ bộ dò mặt không thấy gì. Thay người/sản phẩm vẫn cần Flow/Muse.
- Bảng 25 phép thử giữ kết quả tự ghi nhận cũ. Không tự đánh Đạt D5/D6/D7 bằng fixture tổng hợp. Giá Flow và số dư vẫn chưa xác minh; không đổi thành 0/10/20/100 chỉ vì tài liệu đưa bảng tham khảo.

## Kiểm tra đã chạy

- `PYTHONPATH=/tmp/sceneforge-cpu-deps python -m local_engine.check_cpu_analysis`: FFmpeg tạo video 2 cảnh, cắt đúng 1s trong sai số một frame, RapidOCR nhận BRAND và vùng chữ thật, OpenCV tạo bản tô lấp, từ chối vùng quá lớn/đầu vào hỏng/thiếu header, chỉ một job, dừng và dọn tệp tạm. Không gọi dịch vụ.
- `PYTHONPATH=/tmp/sceneforge-cpu-deps python scripts/workflow/check_cpu_analysis.py`: Chromium → companion → engine thật; xem trước, reload, áp, cảnh báo, OCR chọn vùng/xem/lưu ảnh chưa duyệt, phân tích lại giữ clip, hoàn tác. Không gửi Gemini/Flow/Muse.
- Hồi quy: Cài đặt, thông báo, node gộp/kéo/minimap; bảng thử 25 mục; MP4 thật/font; hợp đồng Gemini, retry và giới hạn cũ. Các kiểm tra Gemini dùng transport giả.

## Chưa xác minh / để sau

Chưa thử 3 video Trung, 5 TikTok cắt nhanh, 3 ảnh logo đối thủ như D5–D7 yêu cầu. **Chưa chạy suy luận whisper model thật**: tải model bị proxy 403 cả khi thử lại với quyền mạng; không dùng lời mẫu để giả là engine đã chép đúng. Chưa chứng nhận CPU/installer trên Windows hoặc chất lượng mặt/nhãn/giọng/credit thật.

Chưa có RapidVideOCR toàn video, nhận diện sản phẩm CPU, dán sản phẩm rembg, dựng FFmpeg nền toàn timeline, chuyển ổ có kiểm chứng, thư mục xuất chung và danh sách giọng VieNeu thật. Không đưa YOLO/PyTorch/CUDA vào bộ CPU. Flow/Muse tự render/quota vẫn chưa nối.

Phụ thuộc được cài riêng, không đóng gói binary/model trong ZIP. Metadata giấy phép và các license có trong distribution được lưu ở `docs/engine-audit/cpu-*`, `scenedetect-LICENSE`, `opencv_python-LICENSE`, `faster_whisper-LICENSE`. Nhánh RapidOCR này có metadata Apache-2.0; cần giữ license của phụ thuộc khi tự phân phối binary.
