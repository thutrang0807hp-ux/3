# Củng cố luồng Video mẫu — 25/10/2026

Đợt triển khai theo `SceneForge-VideoMau-danh-sach-sua.md`, ưu tiên bảo toàn kết quả và tránh tạo trùng. Không bổ sung model lớn hoặc chuyển sang API trả phí.

## Đã triển khai

- **P0-1:** backend lưu biên nhận từ chối trước gửi, có request ID và danh tính kho. Frontend chỉ gỡ khóa khi có biên nhận khớp; HTTP 404/429 đơn thuần không chứng minh chưa gửi. Lượt cũ đã gửi không bao giờ bị đổi thành “chưa gửi”.
- **P0-2/3:** xử lý lỗi riêng từng job; job mất/stale/JSON hỏng không chặn job khác. Đồng bộ failed, cho chọn từng kết quả prompt, xem/sửa JSON đã nhận mà không gọi AI. Giữ bản gốc và kiểm contract trước áp dụng.
- **P0-4:** thanh workflow có **Các lượt đã gửi**. Có nút đối soát, xem/sửa kết quả và bỏ theo dõi sau khi kiểm lịch sử. Backend từ chối bỏ lượt còn chạy trong app. Bỏ lượt không hủy dịch vụ, không hoàn credit và không tự tạo lại.
- **P0-5, phần cơ chế:** journal bền vững ở wrapper Flow; request/account/body hash được gắn trước chạy, task tiếp tục nếu client ngắt. Ghi operation ID trước poll. Muse ghi session ID ngay khi nhận events và video identity trước tải, vào journal riêng. Nút đối soát chỉ tra/tải bằng tài khoản gốc, không chuyển tài khoản hay tạo lại. Đối soát cùng ID được khóa tránh tải đồng thời. Cần mở lại engine Flow bằng `start-flow.bat` bản mới, đồng bộ lại tài khoản trong Cài đặt.
- **P1-1/2:** poll local 12 giây khi có job hoạt động và trang đang hiển thị; không tự áp JSON/duyệt khung. GET CPU retry có backoff, giảm ghi trạng thái IndexedDB; lỗi đường đọc không tự biến thành provider thất bại.
- **P1-3:** đọc đúng một JSON object trong lời dẫn/code fence, hiểu chuỗi/escape; nhiều object hoặc JSON cụt giữ lỗi để rà, không tự sửa hoặc gửi lại.
- **P1-4/5:** evidence lấy từ video gốc trong giới hạn 768×1024, tách thumbnail 180px; tối đa 4 ảnh/tấm. Gemini Chat chia tối đa 8 cảnh/nhóm, dùng mã cảnh/câu toàn cục, ID bền từng nhóm. Có thể áp cảnh hợp lệ riêng; nhóm chưa rõ chỉ đọc lại trạng thái. Nhóm chưa gửi/bị từ chối hoặc đã bỏ sau đối soát mới được gửi bằng thao tác chủ động, ID mới khi cần. Nguồn API/OpenAI giữ contract cũ, không tự chia lượt trả phí.
- **P2-5/6/7:** sửa fixture API cũ, lưu envelope cùng transaction claim, kiểm contract SDK Gemini trước generation. Không fallback sang hàm SDK có retry.
- **P2-10:** app chỉ báo Đã xuất sau khi Blob và trạng thái phòng ghi thành công. Editor nhận ACK; lỗi quota có nút lưu lại/tải file đã tạo, không cần dựng lại. Lưu vào browser thành công chưa bảo đảm bản sao ra thư mục máy thành công; lỗi mirror vẫn hiển thị riêng.
- **P2-11, phần code:** core dependencies cache theo requirements/interpreter/platform, lần mở sau kiểm import thay vì cài lại. `start.bat repair` cài/kiểm lại, lỗi cài thì không mở app; báo FFmpeg thiếu. Chưa chạy bộ cài trên Windows thật.

## Chưa triển khai trong đợt này

- **P1-6/7:** lựa chọn model/ngôn ngữ trên UI, CPU checkpoint theo giai đoạn và tối ưu gom decode. Giữ Whisper base và pipeline CPU hiện tại; chưa tăng timeout hay tự tải small. CPU timeout vẫn cần chạy lại phần local.
- **P1-8/9:** duration theo từng model, nối tail giữa các phần và tăng concurrency Gemini. Chia clip hiện theo tối đa khoảng 8 giây; chưa giải quyết đầy đủ đoạn đuôi ngắn. Không tăng slot Gemini khi chưa thử cách ly phiên thật.
- **P2-1/2/3/4/8/9:** AdaptiveDetector/fade, OCR phụ đề dày, YuNet, hiệu chỉnh ngưỡng, UX exhausted và dọn media backend theo tham chiếu còn trong backlog. Không tự xóa file để giảm dung lượng.
- **P2-12:** giữ thông báo effect không hỗ trợ và lựa chọn engine xuất rõ ràng; chưa bổ sung effect mới.
- **P3:** chưa refactor toàn frontend hoặc chứng nhận Windows/live E2E.

## Phạm vi kiểm chứng

Đã chạy bộ kiểm admission/recovery, UI nhận nhiều kết quả và sửa JSON, batch 17 cảnh, Flow journal ngắt kết nối/khởi động lại/tra operation, Muse worker session journal/history, đối soát provider với video FFmpeg thật, ghim tài khoản và concurrency; không gửi lệnh tới tài khoản online thật. Đã chạy CPU cắt cảnh/RapidOCR, model Whisper base thật qua API local và xuất MP4 FFmpeg. Chép lời có sai số, vẫn cần nghe/rà.

Chromium kiểm xuất ghi Blob thật vào IndexedDB: không đổi trạng thái trước commit; quota fixture trả ACK lỗi. Các kiểm thử workflow/direct/voice và setup-once đã qua. `scripts/app-shell/check_home_archive.py` cũ hiện dừng ở selector `#board [data-room]` không còn khớp layout; không ghi bài này PASS và không đổi thiết kế trang chủ để chiều test.

Chưa thử account online hoặc PC Windows. Muse SDK hiện kết nối **muse.ai**, chưa chứng minh là **meta.ai**. Không có ID upstream hoặc lịch sử bị mất thì không bảo đảm thu hồi kết quả; vẫn giữ unknown để người dùng kiểm tra. “Có code đối soát” không đồng nghĩa đã chứng nhận chạy trọn vòng dịch vụ thật.

## Nâng cấp dữ liệu

Sổ request nâng lên schema v2. Trước migration có snapshot trong `schema-backups`; không xóa dữ liệu/phiên hiện có. Bản app cũ sẽ từ chối ghi DB mới; dùng bản mới nhất. Không khôi phục DB cũ để gửi lại job: phải đối soát lịch sử trước vì snapshot có thể chưa ghi các lượt mới.
