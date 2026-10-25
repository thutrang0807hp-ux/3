# Củng cố luồng Video mẫu — 26/10/2026

Đợt sửa sau phản hồi về job “ma”, dự phòng ổ, mất phản hồi lưu/dọn, CPU quá giờ, ảnh prompt nhỏ và chia clip. Không nâng Whisper, không cài model dịch/VLM, không đổi số luồng Gemini và không coi muse.ai là Meta AI.

## Đã thay đổi

### Gửi việc và dung lượng

- `request_ledger.py`: ghi `preparing` trước khi chép ảnh tham khảo, chỉ chuyển `submitted` sau khi đăng ký đầu vào xong. Lỗi chuẩn bị ghi `not_submitted`; nếu app bị ngắt trong `preparing`, khởi động lại cũng xác nhận chưa gửi. Task provider chỉ được tạo sau khi claim hoàn tất. Không tái sử dụng ID để tự gửi lại.
- `admission.py`: lỗi ghi đĩa có biên nhận âm được trả 507 kèm `submitted:false`, thay vì biến thành lượt chưa rõ trên UI. Không biến một request đã gửi thành biên nhận âm chỉ vì có OSError.
- `storage_jobs.py`: job unknown vẫn giữ media/chứng cứ đối soát, nhưng không giữ dự phòng 500 MB vô thời hạn. Job submitted đang xếp/chạy vẫn có dự phòng. Thông báo 507 ghi dung lượng trống/cần/dự phòng và các ID đang giữ chỗ.
- Kiểm chỗ trống khi tải/chép kết quả: Flow kiểm trước và trong stream; Muse kiểm trước thao tác và trước SDK download; canonical capture kiểm dung lượng cho bản chép thật. Lỗi sau khi dịch vụ có thể đã nhận việc vẫn là unknown, không tự tạo lại. SDK Muse không cung cấp bảo đảm quota ổ nguyên tử suốt toàn download.

### Lưu và khôi phục sau mất phản hồi

- Kho SQLite schema **3**, có `mutation_receipt` (tối đa 100 biên nhận) trong cùng transaction với checkpoint hoặc lượt dọn. Receipt gắn mã thao tác, library ID qua snapshot, revision trước/sau và operation dọn nếu có. Nâng schema có sao lưu; bản app cũ schema 2 không mở trực tiếp kho schema 3.
- Browser ghi intent + digest metadata trước khi gửi. Khi mở lại, so nội dung và biên nhận; chỉ tự nhận snapshot khi nội dung khớp hoặc chứng minh đúng thao tác đã gửi và cache chưa có sửa mới. Không lấy riêng số revision làm bằng chứng xung đột hoặc bằng chứng được phép ghi đè.
- So Blob bằng SHA theo khối trong Worker, không upload lại file chỉ để so cache. Khi có sửa local mới khác với bản đã gửi: giữ cả hai, tạm ngừng ghi kho, mở UI để xuất bản trình duyệt/chọn nạp kho trong Cài đặt. Chặn gửi AI mới trong trạng thái này; vẫn cho đọc trạng thái. Không âm thầm bỏ sửa local.
- Áp dụng cho checkpoint, dọn một dự án, duyệt/dọn phiên bản và đường chọn nhiều. Mất phản hồi không tự phát lại generation. Receipt hết vòng lưu hoặc khác thư viện không được dùng để suy đoán thành công.

### Phân tích CPU có thể tiếp tục

- Đầu vào vẫn tối đa 500 MB/10 phút. Một lượt worker vẫn tối đa 600 giây; bước tạo proxy có giới hạn riêng. Không chạy vô hạn.
- Nguồn/options được giữ bền trước xếp task. `cpu_checkpoint.py` gắn checkpoint với SHA nguồn và tùy chọn; lưu mốc cắt, từng cảnh và từng đoạn lời thành file atomic riêng. Đổi nguồn/tùy chọn không dùng nhầm checkpoint.
- Whisper xử lý theo lõi 30 giây, có ngữ cảnh chồng 0,5 giây ở biên. Chỉ giữ từ thuộc lõi, quy về mốc tuyệt đối để tránh lặp. Vẫn là ASR, không phải forced alignment; phải rà lời, đặc biệt gần biên đoạn và khi nhạc nền lớn.
- Hết thời gian, dừng hoặc app bị ngắt: hiện **Tạm dừng / Tiếp tục CPU**. POST `analysis/local/jobs/{id}/resume` cần xác nhận và dùng lại ID/nguồn cũ; không tải video lên lại. Pipeline tự động và bảng CPU thủ công đều có đường tiếp tục; chưa hoàn tất không tự áp số đo dở vào cảnh.
- Khi thành công, dọn nguồn/proxy/checkpoint tạm. Lượt dở giữ tối đa 7 ngày từ lúc tạo/tiếp tục; tối đa 4 lượt trong registry. Có **Bỏ dữ liệu tạm** (`.../{id}/discard`) trong bảng CPU và hàng chờ sau khi dừng, không xóa video nguồn trong dự án. Việc dọn TTL hiện chạy khi mở/tạo lượt phân tích, không phải dịch vụ chạy khi app đóng.
- Chưa chia checkpoint bên trong PySceneDetect hoặc từng scene đang đo: nếu bị ngắt trong một bước chưa xong, phải làm lại bước đó; các cảnh/đoạn lời đã hoàn tất không phải chạy lại. Thời gian `elapsed_seconds` trong kết quả là lần chạy worker cuối, không phải tổng mọi lần tiếp tục.

### Ảnh đầu vào và RAM

- `referencePromptFiles()` ưu tiên `scene.cpu.evidence_frames` thay thumbnail 180 px. Vẫn dùng thumbnail khi cảnh chưa có bằng chứng lớn. Giới hạn 8 ảnh/lượt vẫn giữ, không bỏ ảnh tham khảo âm thầm.
- Kiểm SHA nguồn CPU dùng `fingerprintWorker` theo khối, có sẵn cả khi mở workflow trực tiếp. Không gọi whole-file `file.arrayBuffer()` cho video để xác minh nguồn. Hash giống backend mới cho áp kết quả.
- `displayFrame()` ưu tiên bản mới, ảnh nguồn thực hoặc ảnh bằng chứng. Khung cuối clip mới lấy tối đa 768 px cạnh ngang, không phóng lớn nguồn nhỏ, dùng làm đầu vào nối cảnh thay thumbnail 180 px.

### Chia clip và liên tục hình

- Node Video có nút **Chia clip**. Cảnh chưa có clip/lượt tạo/lời riêng được chia cân đối theo mốc câu và các mốc hành động người dùng nhập. Không tuyên bố local AI đã hiểu hành động. Số phần cơ bản là số tối thiểu theo trần 8 giây hiện có; tránh để một phần đuôi quá ngắn khi có thể cân lại.
- **Thời lượng dựng khác thời lượng nhà cung cấp trả về.** Chưa có hợp đồng xác minh toàn bộ duration model; không tự khai hỗ trợ 4/6 giây hay hứa ít credit hơn chỉ vì prompt ngắn. Clip trả dài hơn sẽ được dùng phần phù hợp trên timeline.
- Tùy chọn **đuôi tĩnh ≤1,2 giây, không lời**: dùng giữ khung cuối cục bộ thay một job video nữa. Không áp nếu có lời nguồn trong vùng giữ; cửa sổ thoại không vượt thời gian gen. Đây là ảnh giữ, không phải AI tạo thêm hành động. Dùng khi người dùng xác định đuôi cảnh có thể tĩnh.
- Tùy chọn **nối khung cuối**: chỉ chuẩn bị phần kế tiếp khi phần trước đã nhận/duyệt và có khung cuối. Dùng khung đó làm ảnh đầu vào + prompt continuity. Các phần trong cùng chuỗi chạy tuần tự; các cảnh độc lập vẫn có thể song song. Đổi phần trước làm các phần phụ thuộc cần rà/nối lại. Không bảo đảm model giữ giống nhân vật/sản phẩm tuyệt đối.
- Giữ cách chia của clip/lượt cũ để không gán nhầm phiên bản. Khi đã có lời riêng từng phần, không tự xóa lời để đổi mốc. Các phần đang tạo và chưa rõ kết quả không được gửi lặp.

### Dọn kho

- Chỉ tính freed bytes khi file thực sự có trước unlink. File đã mất từ trước không được tính như vừa xóa.
- Tính bảo vệ hiện hành một lần cho lượt dọn; cache tập bảo vệ từ backup theo đường dẫn, stat và chính sách release/deleted. Cache backup ước lượng giới hạn 32 MB; backup/chính sách đổi thì đọc lại. Không cache “quyền được xóa” vĩnh viễn.
- Cache chỉ mục import theo revision, tận dụng record vừa commit khi revision khớp. Không có done job thì không quét nội dung để ACK. Cache hash permanent theo revision/pin, nhưng kích thước asset và chỗ trống vẫn đọc hiện tại.
- Job legacy không rõ room có thông báo chỉ đích danh ID cần đối soát. Không tự bỏ job đó để cho dọn.

## Kiểm chứng và giới hạn

`review/REFERENCE_FLOW_FIX_CHECKS.json` trong gói review ghi bài thực sự chạy. Có kiểm file/SQLite, Chromium/API, FFmpeg/PySceneDetect/RapidOCR thật, Whisper base offline thật; có fixture lỗi ổ đầy, timeout, mất ACK và provider transport. Tất cả trong thư mục/profile thử, không xóa dữ liệu người dùng hoặc gửi tài khoản thật.

Chưa chứng nhận Windows, vòng Gemini → Flow/Muse thật, hạn mức tài khoản, chất lượng mọi ngôn ngữ hoặc benchmark 10 video thật. File 200 MiB trong bài transport là MP4 tổng hợp 0,5 giây có padding, không phải video dài để đo tốc độ. Whisper vẫn có thể nghe sai; không vì các phép thử qua mà coi lời/prompt đã đúng hết.
