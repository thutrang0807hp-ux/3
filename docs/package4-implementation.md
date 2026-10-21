# SceneForge · Gói 4 · Phạm vi triển khai (21/10/2026)

Nguồn yêu cầu: `design/package-4-spec/DAC_TA_GOI_4.md` và bảy ảnh đi kèm. Gói này thay giao diện sáu cột của gói 3; dữ liệu sản phẩm, room ID, nguồn video, bộ ảnh và bản dựng cũ không bị đặt lại.

## Dùng ngay trên bản web

- Trang chủ bốn cột: Cần bạn, Máy đang chạy, Đang chuẩn bị, Đã xuất. Cột chạy chỉ có việc khi dữ liệu thật báo running; không dùng các số minh họa trong ảnh. Bỏ thanh đo credit, thanh chặng và mô tả dài trong cột sản phẩm; thay bằng số việc cần bạn/lỗi hoặc số video.
- Video / Bộ ảnh / Bộ cảnh / Chi phí trong từng sản phẩm; lọc mẫu/ảnh; Bảng/Danh sách và sắp xếp cột. Thẻ đầu lớn, thẻ còn lại gọn, cột cuộn riêng. Nút Video mới có hai hướng; thả video vẫn vào luồng tham khảo.
- Hàng chờ hai làn Flow/Muse: lưu riêng, tạm dừng từng làn hoặc cả hai, ưu tiên phòng, kéo thứ tự, hủy việc chưa chạy. Sau khi mở lại app, việc từng chạy được đánh dấu chưa rõ kết quả, không tự gửi lại hoặc giả là còn đang chạy. Tạo thêm hai bản là lựa chọn rõ ràng. Khung-trước được ghi thành việc riêng, clip có mã phụ thuộc khung. Chưa có worker dịch vụ nên tất cả chỉ là chuẩn bị, không tự gửi lệnh hoặc trừ lượt.
- Không gian Từ ảnh có bảy node: ảnh đầu vào, Bộ cảnh, công thức, kịch bản, giọng, đạo diễn và Sang Dựng. Kéo node theo đúng mức zoom, phóng/thu/kéo nền, lưu vị trí. Dây cập nhật theo node, không chạy hiệu ứng tiến độ giả.
- Bộ cảnh tám kiểu: prompt quay/ánh sáng/chuyển động, 9:16, no talking/mouth closed/no text. Nhập clip thật, kiểm tra khung/thời lượng, giữ các bản. Clip dùng chung theo sản phẩm, còn lời/giọng/kế hoạch ghép riêng từng phòng. Có tùy chọn khung trước, sửa yêu cầu, tạo hai bản. Lỗi nhập tệp thật có khung đỏ và giữ các bản cũ.
- Ảnh đầu vào chép từ sản phẩm, thêm/bỏ ảnh riêng trong phòng không sửa bộ gốc.
- Ba công thức chỉ có nhịp/loại cảnh/thời lượng, không bịa lời hay công dụng sản phẩm. Viết/dán lời, sửa tên/nhãn/giây từng nhịp. Kho kịch bản đầy đủ chưa chốt nên không thêm trang kho giả.
- Nhập WAV/MP3/M4A, sóng lấy từ âm thanh giải mã thật, phát nghe. Canh nhịp bằng khoảng lặng; nếu thiếu khoảng lặng thì chia ước lượng theo độ dài lời và ghi rõ. Không gọi đây là nhận dạng lời hoặc căn từng từ chính xác. Có Không lời.
- Ghép cục bộ theo nhãn, cắt clip theo giây, không dùng cùng một clip hai lần liền nhau; nhịp dài nối nhiều clip. Thiếu thì hiện đỏ và hai đường: tạo bổ sung có xác nhận xếp hàng hoặc dùng tạm kiểu khác. Không tự tạo phần thiếu. Ghép kiểu khác đổi thứ tự chọn khi Bộ cảnh có đủ lựa chọn.
- Ghép cục bộ **không giả là Đạo diễn AI**. Gemini chỉ có trong bản cục bộ khi đã lưu key; nút AI bị khóa khi chưa có kết nối/SDK phù hợp.
- Sang Dựng chuyển clip và giọng thật; tiếng gốc Muse tắt, giọng riêng giữ. Giữ luật hỏi trước khi thay bản dựng; nhập bản mới vào Kho không tự thay timeline. Video mẫu vẫn giữ tiếng Flow hiện có, chưa đổi toàn bộ pipeline video mẫu sang giọng đọc chung/lipsync mới của gói 4.
- Dùng lại video từ ảnh tạo phòng mới từ lời/công thức với bộ ảnh mới, kế hoạch ghép được bỏ. Các phòng ảnh cũ được giữ lời và mốc khi chuyển sang khung mới; vẫn giữ workflow cũ trong DB. Clip trong workflow cũ chưa tự phân loại thành tám kiểu vì không có dữ kiện xác nhận loại cảnh.

## Dọn dữ liệu

Dọn trong **bộ nhớ trình duyệt**; không xóa bản sao đã ghi ra thư mục hệ điều hành. Trước khi thực hiện, tính tổng bytes của các bản có thể dọn và ghi rõ dung lượng vật lý do trình duyệt thu hồi sau. Giữ phân tích, ảnh đầu cảnh, lời, prompt, clip đang chọn, mọi clip mà timeline còn dùng, âm thanh và bản xuất. Vì vậy một bản cũ đã cắt ghép vẫn sống dù node video đã chọn bản mới hơn. Dừng/lưu và tháo phòng đang giữ dữ liệu trước khi sửa DB để autosave cũ không đưa tệp đã dọn trở lại.

Có Dọn tất cả trong Lưu trữ và tự dọn khi mở Lưu trữ (mặc định tắt). Không còn xem/phân tích lại nguồn sau khi dọn. Sửa tiếp và dùng lại mẫu vẫn giữ dữ liệu cần thiết. Không đụng Bộ cảnh sản phẩm. Chưa tự xóa media mirror trong thư mục máy hoặc quét toàn bộ tệp mồ côi.

## Bản chạy cục bộ

Tệp `downloads/SceneForge-Goi4-Local.zip` chứa giao diện build, `local_engine`, cách chạy và bằng chứng repo/license; không chứa cookie/key/mô hình. Chạy bằng `local_engine/start.bat` hoặc `sh local_engine/start.sh`, mở `http://127.0.0.1:8840/`. Hướng dẫn chi tiết trong `local_engine/README.md`.

- FastAPI phục vụ cùng origin, bind loopback, chặn Host lạ, Origin khác và POST thiếu header ứng dụng. Bản Pages không âm thầm gọi localhost hoặc nhận cookie.
- Kết nối tài khoản mở Chromium riêng để người dùng tự đăng nhập/xác minh, không có trường mật khẩu của app. Lưu phiên thu cookie đúng miền, mã hóa AES-GCM rồi đóng cửa sổ. Trạng thái là chưa kiểm chứng, không cho dùng làm tài khoản tạo clip khi chưa xác minh được.
- Key Gemini lưu mã hóa, không trả ngược cho giao diện; input bị khóa trên Pages. Unix dùng khóa riêng quyền 0600; Windows có bọc DPAPI (chưa thử trên Windows thật). Không có key/admin mặc định nhúng trong ứng dụng.
- VieNeu v3 qua SDK tùy chọn 3.8.3, ONNX/CPU: tạo từng nhịp, lấy thời lượng WAV thật và nối; không tự dùng V4. SDK/mô hình chưa được cài/chạy để kiểm chứng giọng/tốc độ trong đợt này. Bài kiểm tra WAV không được diễn giải thành benchmark VieNeu.
- Gemini viết lời/đề xuất thứ tự từ dữ kiện chữ, chỉ khi bấm nút. Không thử key tự động, không tự gửi lại khi mạng đứt. Nhật ký có usage từ phản hồi; chưa có bảng giá xác minh nên không bịa số tiền. Đạo diễn AI ưu tiên clip, vẫn qua bộ kiểm tra nhãn/độ dài/không lặp cục bộ.

**Flow/Muse tự động vẫn chưa kết nối.** Tài khoản, số dư/quota, gia hạn, đổi ưu tiên tài khoản, cooldown và chạy hai engine thật chưa được kiểm chứng đầu-cuối. Các hàm policy có bài kiểm tra: 401 cần đăng nhập, 403/429/lỗi mạng giữ số cũ, xác minh dừng xoay, ba lỗi nghỉ, việc không rõ kết quả không gửi lại; đó chưa phải một worker dịch vụ hoàn chỉnh. Nút xoay/kiểm tra bị khóa khi chưa có adapter. Chưa có biểu đồ credit thực khi không có log xác minh.

## Những điều phát hiện khi đọc repo

Đã lấy đúng repo gốc bằng git, đọc README, LICENSE, cấu hình, store/auth/keepalive và API; không chạy mã ba repo trong đợt này. Revision cố định ở `docs/engine-audit/upstream-revisions.json`.

- flow2api MIT: cấu hình mẫu còn bind 0.0.0.0, admin/admin, key mẫu, captcha thuê mặc định và tự refresh. Không chạy nguyên trạng; chưa phát hành một bản fork đã sửa/kiểm chứng mọi điểm trong đặc tả.
- muse2api MIT: mã dùng **muse.ai**, không xác nhận là Meta AI. Cấu hình mã có bind 0.0.0.0, concurrency 2, cookie JSON và keepalive. Không đưa cookie tài khoản thật vào bản nguyên gốc này và không gửi cookie Meta/Google sang Muse.
- VieNeu Apache-2.0: README mặc định v3 Turbo, CPU/ONNX. Chưa có benchmark thật trên máy người dùng.

Không sử dụng AGPL/FlowKit hay captcha thuê. Còn cần tài khoản do người dùng tự đăng nhập và các adapter đã sửa/kiểm chứng để đo quota, giới hạn, watermark, độ giữ nhãn/mặt, giá nâng 1080p và thời gian nghỉ thực.

## Kiểm tra

- `scripts/app-shell/check_package4.py`: trình duyệt thật, MP4/ảnh/WAV thật; bốn cột/tab/lọc/list; hai làn và hai bản có phụ thuộc; ảnh phòng độc lập; Bộ cảnh chung; thiếu loại cảnh không tự tạo; canh khoảng lặng, nhịp dài/no-repeat/đổi phương án; kéo node lưu; Sang Dựng tắt tiếng Muse, giọng thật; cleanup cơ bản; reload cả bytes/timeline; account offline không bịa dữ liệu.
- `scripts/app-shell/check_cleanup.py`: ba phiên bản clip; v1 bị cắt trên timeline + v3 đang chọn sống, v2 và nguồn bị dọn; tệp xuất thật còn, bản dựng mở lại và dùng lại mẫu sau dọn được.
- `local_engine/check_local.py`: AES-GCM, mở lại vault, quyền khóa, không trả secret, policy, chặn Origin/Host/header, không kích hoạt account chưa kiểm chứng, vận chuyển WAV thật. Không gọi dịch vụ.
- `local_engine/check_browser.py`: máy chủ localhost thật + UI, lưu key thử tổng hợp vào vault, không gửi key ngược; không đăng nhập hoặc gọi AI.
- Các bài node canvas và timeline magnetic reorder tiếp tục kiểm tra thao tác cũ. Các bài gói 3 còn đòi sáu cột/luồng ảnh cũ không phải hợp đồng giao diện mới.

Pages và localhost là hai origin khác nhau: dữ liệu trình duyệt không tự chuyển qua lại. Không hứa ZIP tự mang dự án hiện có sang bản cục bộ; JSON riêng không chứa hết media. Xuất vẫn MediaRecorder, chưa có FFmpeg chạy nền.
