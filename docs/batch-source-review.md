# Tạo hàng loạt — gói code để đánh giá

Phạm vi: giữ nguyên source của tab Tạo hàng loạt và các phần nối tới tài khoản, kho dữ liệu, Gemini, Video mẫu. Không đổi giao diện/logic khi đóng gói; chỉ loại build, media, model, SDK, dữ liệu người dùng và các luồng ngoài phạm vi khỏi gói đọc code.

## Chạy được đến đâu?

| Đường đi | Đã kiểm | Chưa chứng minh |
|---|---|---|
| Mô phỏng | Hàng đợi 1–4 việc, tạm dừng, phụ thuộc ảnh trước, nhiều biến thể, xuất ZIP thật, mở lại không tự chạy | Đây là ảnh minh họa trên canvas, không phải ảnh/video AI |
| Gemini Chat tạo ảnh | Xác nhận trước gửi, chọn tài khoản qua Cài đặt, token gắn request, nhận file, khôi phục không gửi lại; transport giả | Phiên Google thật, chất lượng ảnh, hạn mức, song song thật |
| Gemini API tạo ảnh | Adapter + ledger thật với HTTP giả: model, ảnh tham khảo, file gốc, duplicate/unknown/429; trình duyệt xác nhận và nhận kết quả | Quyền model, giá và tạo ảnh qua key thật |
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

- Badge/nút/hướng dẫn còn lẫn chữ “mô phỏng”, “API” khi chọn Chat. `batchWireReal` đặt nhãn Chat nhưng `batchPaint` có thể ghi đè. Đây là điểm trình bày không khớp, không phải chứng cứ ảnh Chat chỉ là mô phỏng.
- Chọn Gemini đặt song song về 1; người dùng có thể chọn 1–4 ở scheduler. Gemini Chat backend vẫn có giới hạn tài khoản riêng; không coi 4 worker tab là 4 ảnh cùng tài khoản đang gen thật.
- Ảnh tham khảo gửi từ preview và thu nhỏ tối đa 1024px. Không mặc định giữ nguyên độ phân giải file gốc khi gửi AI.
- API key và phiên Chat là hai nguồn riêng, không tự thay thế. Chưa nối ChatGPT/Grok/Flow/Muse ở tab này.
- Nhận kết quả hiện chủ yếu bấm “Kiểm tra kết quả”; hết thời gian chờ/ngắt mạng chuyển sang interrupted, không tự tạo request mới. Cần đánh giá thêm trải nghiệm nhiều lượt lỗi và giới hạn 200 việc lưu trong tab.
- Vòng chờ hiện kiểm `submitted`; nên đối chiếu hợp đồng trạng thái thực của provider trước khi kết luận hỗ trợ mọi trạng thái queue/running. Backend hiện trả `submitted` kèm phase chờ/chạy, nên không coi tên phase là state mới.
- Không đánh đồng 7 bài kiểm transport fixture với chứng nhận tài khoản online hoặc Windows.

## Ghi nhận về bài kiểm

Bài `check_batch_studio.py` cũ tìm sidebar sản phẩm lúc tab Batch đang ẩn sidebar nên timeout. Đã sửa test để chọn sản phẩm bằng dropdown có thật trong tab và về trang chủ trước khi mở Lưu trữ. Giữ log lỗi gốc trong gói, không đổi runtime để làm test qua.

Gói này để bên khác đọc/đánh giá, **không phải bộ cài**. Thiếu media/model/build là chủ đích. Test chạy trên app đầy đủ trước khi đóng gói; bản gọn không chạy độc lập. Mọi source được giữ nguyên byte, có manifest SHA-256.
