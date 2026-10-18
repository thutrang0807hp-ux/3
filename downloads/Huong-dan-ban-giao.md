# BÀN GIAO SCENEFORGE — ĐỌC ĐẦU TIÊN

Bản bàn giao: 19/10/2026 (Asia/Bangkok). Trạng thái cuối: `335c391` trên nhánh `gh-pages`.

Web đang dùng: https://thutrang0807hp-ux.github.io/3/?v=335c391#editor
Kho của người dùng: https://github.com/thutrang0807hp-ux/3
Nguồn tham khảo Concat: https://github.com/jub0t/concat

## Mang sang AI / lập trình viên khác

1. Gửi toàn bộ ZIP này, rồi dán nội dung `DAN_CHO_AI_MOI.md`.
2. Yêu cầu đọc tiếp `NGU_CANH_VA_LICH_SU.md`, `TRANG_THAI_KY_THUAT.md` và `source/docs/editor-feature-audit.md`.
3. Nói yêu cầu mới của bạn. Không cần bắt đầu lại dự án.

## Có gì trong gói

- `DAN_CHO_AI_MOI.md`: chỉ dẫn chuyển ngữ cảnh, có thể dán trực tiếp vào cuộc trò chuyện mới.
- `NGU_CANH_VA_LICH_SU.md`: mục tiêu, lịch sử yêu cầu, quyết định đã chốt và các hướng đã bỏ.
- `TRANG_THAI_KY_THUAT.md`: kiến trúc hiện tại, file cần sửa, cách build, kiểm tra và giới hạn.
- `source/`: mã nguồn đang có, gồm backend, web, các trình dựng tham khảo và Concat upstream.
- `preview/`: bản web tĩnh đã build tương ứng phiên bản cuối. Đây là bản có thanh âm thanh mini và vùng chuyển cảnh mới.
- `references/prompt-example-user.txt`: văn bản mẫu prompt chi tiết người dùng đã cung cấp.
- `references/ATTACHMENTS.md`: thông tin về các tệp/ảnh đã được nhắc trong cuộc trò chuyện.
- `references/screenshots/`: ảnh kiểm tra giao diện cuối nếu có.
- `open_preview.py`, `OPEN_PREVIEW.bat`: mở bản web tĩnh bằng Python 3, không cần API key.
- `PACKAGE_MANIFEST.json`: danh sách tệp và SHA-256 để đối chiếu.

## Xem bản đóng gói

Có Python 3: chạy `python open_preview.py`, hoặc bấm `OPEN_PREVIEW.bat` trên Windows.
Script phục vụ thư mục preview bằng HTTP cục bộ và mở trình duyệt sau khi đã bind cổng.
Nếu không có Python, dùng đường dẫn web ở đầu tài liệu.

## Trạng thái cần hiểu đúng

- Web xem trước hiện là trình dựng đa track của SceneForge chạy trong trình duyệt; KHÔNG phải toàn bộ engine Rust Concat chạy trên GitHub Pages.
- API phân tích → tạo clip → tự ghép chưa được nối hoàn chỉnh vào bản web tĩnh. Các tab AI còn có mô phỏng.
- Xuất trình duyệt đã kiểm tra được WebM có hình/chữ/tiếng, theo thời gian thực, tối đa 2 phút và 24 fps.
- Backend Python và tích hợp Concat native là các luồng riêng có trong source, cần kiểm tra lại khi hợp nhất.
- README gốc và một số tài liệu cũ mô tả nhiều giai đoạn khác nhau. Ưu tiên tài liệu bàn giao này và bản audit mới nhất.

Đây là bản khôi phục ngữ cảnh và bàn giao công việc từ nội dung cuộc trò chuyện có sẵn, không phải bản xuất nguyên văn từng tin nhắn của hệ thống chat. Các ảnh cũ không có tệp gốc cục bộ được mô tả trong tài liệu; mẫu prompt dạng văn bản đã được đính kèm nguyên tệp.

Không kèm `.env`, API key, dữ liệu người dùng trong `data/`, Git credentials, `node_modules`, Python venv, Rust target hay toolchain đã cài. Cần cài lại phụ thuộc theo môi trường nhận gói. Giữ các LICENSE đi kèm nguồn tham khảo.
