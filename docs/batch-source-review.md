# Tạo hàng loạt — gói code để đánh giá

Cập nhật 27/10/2026: đọc `chat-source-reliability.md` về nhóm nhiều ảnh, trạng thái tài khoản, URL hội thoại và phiên theo miền. Các giới hạn/tài liệu bản cũ dưới đây phải đối chiếu cập nhật này.

Phạm vi: giữ nguyên source của tab Tạo hàng loạt và các phần nối tới tài khoản, kho dữ liệu, Gemini, Video mẫu. Nguồn đã cập nhật đa nguồn (xem `batch-multisource.md`); bước đóng gói không đổi giao diện/logic; chỉ loại build, media, model, SDK, dữ liệu người dùng và các luồng ngoài phạm vi khỏi gói đọc code.

## Chạy được đến đâu?

| Đường đi | Đã kiểm | Chưa chứng minh |
|---|---|---|
| Mô phỏng | Hàng đợi 1–4 việc, tạm dừng, phụ thuộc ảnh trước, nhiều biến thể, xuất ZIP thật, mở lại không tự chạy | Đây là ảnh minh họa trên canvas, không phải ảnh/video AI |
| Gemini Chat tạo ảnh | Xác nhận trước gửi, chọn tài khoản qua Cài đặt, token gắn request, nhận file, khôi phục không gửi lại; transport giả | Phiên Google thật, chất lượng ảnh, hạn mức, song song thật |
| Gemini API tạo ảnh | Adapter + ledger thật với HTTP giả: model, ảnh tham khảo, file gốc, duplicate/unknown/429; trình duyệt xác nhận và nhận kết quả | Quyền model, giá và tạo ảnh qua key thật |
| Flow / Grok / ChatGPT / Meta AI | Đường UI → account/token → job → nhận file qua provider giả; adapter chat kiểm trên trình duyệt intercept | **Chưa kiểm selector hoặc gen trên dịch vụ thật** |
| Đưa ảnh vào Video mẫu | PNG nhập đúng sản phẩm/phòng/cảnh, chờ duyệt, không thay clip/khung đã duyệt, giao lại không trùng | Không tự gen clip hay tự duyệt ảnh |
| Lưu thư viện | Checkpoint SQLite + PNG thật; trình duyệt mới khôi phục metadata và file | Chưa thử Windows |
| Video hàng loạt | Có mô phỏng và nhập video sẵn vào kho | **Chưa nối tạo MP4 từ prompt bằng Flow/Muse trong tab này** |

Luồng dùng: chọn sản phẩm → prompt dạng dòng/JSON → chọn/ghép ảnh tham khảo → thêm hàng chờ → rà và xác nhận lượt thật → scheduler → provider/ledger → file vào kho → gallery → tải ZIP/lưu ảnh sản phẩm/đưa khung vào Video mẫu.

## Đọc code theo thứ tự

1. `scripts/demo-web/build.py`: thứ tự ghép JS thật. Nhiều hàm được định nghĩa lại; đọc cả file `batch-studio.js`, không dừng ở định nghĩa đầu.
2. `scripts/app-shell/batch-studio.js` và `.css`: UI, validation, scheduler, grouping, versions, imports, ZIP, real bridge; cuối file là provider/persistence bổ sung.
3. `local_engine/server.py`, `batch_images.py`, `gemini_chat.py`, `request_ledger.py`, `admission.py`, `storage_jobs.py`: route, submit/receipt, tài khoản và file.
4. Các module app-shell đi kèm: `app.js`, `library-runtime.js`, `account-dispatch.js`, `accounts-dashboard.js`, `storage-actions.js`; `workflow/room-shell.js`: nhận ảnh vào cảnh.
5. `review/CHECKS.json`, test sources và log. Phân biệt browser/backend/file thật với provider giả.

## Những giới hạn và chỗ đáng hỏi khi đánh giá

- Đọc `batch-multisource.md` để phân biệt adapter mới và đường cũ. Không suy từ test provider giả thành chứng nhận tài khoản online.
- Không tự chuyển Chat → API. ChatGPT/Grok/Meta có phiên mã hóa riêng, một job/tài khoản; Flow dùng engine pin tài khoản cũ. Meta AI không phải muse.ai.
- Ảnh tải từ máy và ảnh nối tiếp gửi file gốc, tối đa 24 MB; ảnh sản phẩm cũ vẫn có thể chỉ có data URL đã lưu.
- Sau timeout hoặc mất kết quả thì interrupted/unknown, không tự gửi lại. Adapter chat mới chưa có đối soát hội thoại bền sau restart; kiểm lịch sử dịch vụ và nhập file thủ công nếu cần.
- Chưa thêm lô riêng/TTL 24h/quota theo lô. Giới hạn 200 job theo cơ chế cũ. Video Batch từ prompt chưa nối thật.
- Chưa thử Windows; trình duyệt thật phải cài riêng. Không có cookie/key/model trong gói đọc code.

## Ghi nhận về bài kiểm

Bài `check_batch_studio.py` cũ tìm sidebar sản phẩm lúc tab Batch đang ẩn sidebar nên timeout. Đã sửa test để chọn sản phẩm bằng dropdown có thật trong tab và về trang chủ trước khi mở Lưu trữ. Giữ log lỗi gốc trong gói, không đổi runtime để làm test qua.

Gói này để bên khác đọc/đánh giá, **không phải bộ cài**. Thiếu media/model/build là chủ đích. Test chạy trên app đầy đủ trước khi đóng gói; bản gọn không chạy độc lập. Mọi source được giữ nguyên byte, có manifest SHA-256.
