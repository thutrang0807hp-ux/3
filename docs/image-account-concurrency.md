# Ảnh chạy đồng thời trên một tài khoản — 27/10/2026

## Cách dùng
Tạo ảnh hàng loạt → chọn nguồn thật → Đổi / cài đặt lượt tạo. Đặt **Song song** phía app và **Tối đa trên mỗi tài khoản**, rồi bấm **Lưu giới hạn nguồn**. Ví dụ cả hai bằng 3 thì một tài khoản có tối đa 3 lượt được app đưa vào xử lý đồng thời, còn lại chờ. Không tăng số bản ảnh/prompt và không tự gửi thêm yêu cầu. Mặc định mỗi tài khoản vẫn là 1, chọn được 1–4; chỉ đổi lúc nguồn rảnh.

Áp dụng Gemini Chat, Flow ảnh, Grok, ChatGPT Chat, Meta AI. API ảnh bằng key đã có lane riêng, không dùng nút tài khoản. Mô phỏng không sửa tài khoản thật; bộ chọn nguồn chỉ lưu được qua bản local. Mức này là cấu hình app/adapter, không phải cam kết hạn mức hoặc tốc độ từ dịch vụ.

## Thay đổi backend
- ImageSlots: lưu chính sách mỗi nguồn trong vault, per-account 1–4, tối đa 4 ảnh toàn lane. Hàng chờ dùng Condition, hủy task trả permit. Chặn đổi chính sách nếu đang chạy/chờ; không tháo mọi giới hạn.
- Gemini Chat: ảnh dùng image slots thay khóa cứng 1. Chữ/phân tích/kiểm phiên vẫn có gate độc quyền với ảnh trên cùng tài khoản, giữ tính nhất quán phiên. Mỗi lượt SDK worker có workspace và output riêng. Khi bật song song, phản hồi generation không ghi đè cookie chung. Không gọi API trả phí thay thế.
- Grok/ChatGPT/Meta: mỗi lượt có Chromium context/worker riêng, output gắn request ID; dùng image slots thay Lock mỗi tài khoản. Giữ global semaphore 4 giữa các nguồn web. Chỉ lưu lại phiên generation khi limit=1 và phiên gốc chưa đổi. Kiểm phiên không ghi đè phiên mới hoặc phiên đang có job dùng.
- Flow: tách ImageSlots khỏi VideoSlots. Gọi endpoint mới `/sceneforge/accounts/{id}/image-concurrency` và yêu cầu engine xác nhận đúng kind=image trước khi gửi. Giới hạn video giữ riêng. Extension không reset semaphore đang chạy nếu cấu hình không đổi; nếu muốn đổi mà engine có việc đang chạy thì chặn. Giữ giá trị giới hạn loại công việc còn lại.
- Sau cập nhật cần khởi động lại app local. Với Flow cần dừng engine cũ rồi mở `local_engine/start-flow.bat` để nạp extension mới. Engine cũ không có endpoint/không xác nhận kind sẽ bị chặn trước khi gửi tạo; app không giả rằng đã mở giới hạn.

## Không thay đổi
Quota/credit, login/xác minh, account binding, request journal/receipt, kiểm selection token, không replay lượt chưa rõ, không gửi lại sau timeout. Nguồn vẫn có thể tự xếp hàng, từ chối hoặc hết lượt. Cấu hình mới không có nghĩa đã chứng nhận nhiều lượt trên tài khoản online thật.

## Kiểm tra
- Adapter thật + runner/transport fixture cho cả năm nguồn: một tài khoản, 7 request, peak=3, file PNG đúng từng request, 4 việc chờ, cấu hình lưu qua Vault mới, không clobber cookie, không phát sinh send khi chỉ đọc lại; Flow thiếu xác nhận đúng loại bị chặn trước generation.
- Ba Chromium worker thực cùng một tài khoản fixture: ba trang bị intercept riêng, mỗi trang gửi một lần, ba PNG khác nhau về đúng request, cookie chung giữ nguyên. Không ra dịch vụ online.
- Local HTTP setting routes: strict 1–4 (không nhận bool/string), busy=409, status trả mức đã lưu. Owned Flow extension dùng manager fixture: xác nhận ảnh riêng, giữ video, không reset permit đang dùng, kiểm auth/giới hạn/mã tài khoản. Chưa chạy với checkout vendor/engine online.
- Chromium UI → API/vault thật: lưu mức cho Gemini/Flow/Grok/ChatGPT/Meta, đổi nguồn và profile mới vẫn giữ; giới hạn app không bị đặt lại, giới hạn video Flow không đổi, không gửi generation.
- Hồi quy web worker (trang intercept), Gemini viết/dịch/phân tích, Muse/Flow video (fixture), gallery và nhiều nguồn (fixture) đạt. Chưa kiểm tài khoản thật hoặc Windows; không chứng nhận hạn mức dịch vụ.
