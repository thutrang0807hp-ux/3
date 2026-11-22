# Rà soát luồng ảnh khung — 22/11/2026

Ghi chú sau rà soát: các thay đổi khắc phục ở bản .152 được ghi trong [image-receive-20261122.md](image-receive-20261122.md). Báo cáo dưới đây giữ nguyên kết quả tại bản .151.

Mốc kiểm tra: commit `5a5a306` / bản .151. Phạm vi: nút tạo/kiểm tra/nhận/tạo lại ảnh, chuẩn bị prompt và nguồn ảnh, dấu đối soát, lưu lượt, trạng thái hội thoại, worker Gemini, bộ tải ảnh của SDK ghim `1ad0d4a93e505e77c79769d78ef2997641f973c8`, bộ đóng gói cập nhật. Đây không phải chứng nhận toàn bộ tính năng của ứng dụng không còn lỗi.

## 1. [P1] Đã có ảnh nhưng tải thất bại trở thành lượt không thể nhận lại bằng luồng hiện tại

- `local_engine/gemini_chat_worker.py:116`: tải ảnh ngay trong lần gọi tạo; khi tải lỗi, nhánh `:137` trả lỗi và metadata hội thoại, không trả bản mô tả ảnh có thể tải lại.
- `local_engine/gemini_chat.py:404–416`: lưu mã lỗi rồi kết thúc `unknown`; `result` không có tệp ảnh. Cursor chỉ giữ metadata hội thoại cuối theo dự án/tài khoản/phạm vi, không phải bản mô tả kết quả bền vững riêng cho từng lượt. `finally` xóa tệp `.partial`.
- `workflow.html:2158`: Nhận ảnh đã tạo chỉ có khi trạng thái `done`. `directRecover` chỉ lấy tệp khi lookup trả `done`. Endpoint GET jobs chỉ đọc ledger; không gọi lại SDK để nhận kết quả. Không có endpoint đối soát/tải lại Gemini riêng.
- Vì vậy kiểm tra lại một lượt `unknown` do lỗi tải không tự biến thành có ảnh. Nút tạo mới gửi một generation khác, không phải tải lại ảnh cũ. Đây là lỗ hổng khôi phục đúng với giai đoạn lỗi người dùng đã chụp.

Cần tách kết quả đã tạo khỏi trạng thái tải tệp, lưu dấu kết quả riêng từng lượt trong kho bảo mật, và cho tải/đọc lại kết quả mà không gọi tạo. Không dùng cursor mới nhất của hội thoại để đoán ảnh của lượt cũ.

## 2. [P1] Dấu đối soát có thể phụ thuộc URL tạm, không ổn định sau khi mở lại app

`workflow.html:1390–1392`: `directEvidence` có thể trả `mediaUrl(sourceFrame.asset)`; `directSignature` băm nguyên chuỗi trả về. Khi đó dấu băm chứa `blob:...`, thay đổi khi URL được tạo lại dù asset/prompt không đổi. `directRecover` so dấu này rồi gán `stale` nếu khác.

Đã tái hiện bằng chính hàm trong source: cùng mã asset và prompt, chỉ đổi URL blob theo phiên thì hash khác. Điều kiện này không áp dụng nếu nhánh evidence đang dùng data URL cố định. Cần dùng danh tính asset/nội dung bền vững và hỗ trợ đọc dấu cũ, không đánh dấu mọi lượt cũ là stale do nâng bản.

## 3. [P1] Tạo lại toàn bộ và tạo lại một cảnh không xử lý hội thoại bị kẹt giống nhau

Trong `runImages` (`workflow.html:2424`), nhánh `retryScene` cấp `imageConversationScope` mới; nhánh `fresh` của nút tạo lại toàn bộ chỉ bỏ chờ các bản ghi phía giao diện. Nó không cấp phạm vi mới.

Adapter `gemini_chat.py:385–388` vẫn chặn cursor `unknown/in_flight`. Do đó nếu cursor cũ bị kẹt, nút tạo lại toàn bộ có thể tiếp tục bị chặn dù đã đánh dấu bỏ chờ ở giao diện. Không phải mọi lỗi HTTP tải ảnh đều đặt cursor unknown: nếu worker trả metadata hợp lệ, cursor được đặt ready. Đây là lỗi điều kiện, không phải nguyên nhân được khẳng định cho ảnh chụp mới nhất.

Cần dùng cùng một chính sách khôi phục có xác nhận cho các đường tạo lại, đồng thời ưu tiên nhận kết quả cũ trước khi cho phép tạo thêm.

## 4. [P2] Nhãn trạng thái mới và thông báo lỗi cũ có thể cùng xuất hiện

`workflow.html:174` cập nhật state nhưng không xóa `error`, `errorCode`, `waitError` khi kết quả mới đã hoàn tất. Panel `:2166` tiếp tục tổng hợp những trường này và cả lỗi action cũ. `directRecover` xóa một phần lỗi khi import nhưng không xử lý toàn bộ các trường/panel này.

Đã tái hiện bằng hàm thật: sau `jobReadRecord(job, {state:'done'})`, cả lỗi cũ, timeout cũ và mã lỗi vẫn còn. Cần phân biệt lỗi lịch sử với lỗi hiện tại; không xóa lịch sử nhưng không hiển thị nó như lỗi đang hoạt động.

## 5. [P2] Tải bản full-size không có phương án nhận lại; mã HTTP có thể mất trước khi tới adapter

Worker chỉ gọi `GeneratedImage.save(full_size=True)` một lần. SDK thử đường RPC full-size rồi suffix URL, nhưng SceneForge không có đường tải lại độc lập hoặc lựa chọn bản thường của chính ảnh đó khi lỗi. Không nên tự gọi lại generation để xử lý lỗi download.

Trong SDK ghim, `types/image.py` tự tạo `HTTPError('Error downloading image: ...')` nhưng không gắn response/status_code. `error_detail` của app chỉ đọc hai thuộc tính đó nên không thể hiện mã HTTP của trường hợp này, dù .151 có hỗ trợ trường http_status.

Đã tái hiện bằng lớp GeneratedImage thật và transport giả lập: bản full-size trả HTTP 403, exception tới app không có http_status; tải bản thường của chính ảnh đó thành công mà không gọi generation. Đây là mô phỏng chứng minh trường hợp lỗi, không phải bằng chứng máy người dùng đã gặp HTTP 403. Nếu hỗ trợ bản thường thì phải báo đúng kích thước/chất lượng, không tự duyệt ảnh hay quảng cáo 4K.

## Kiểm tra đã làm và giới hạn

- Tái hiện lỗi hash URL tạm và lỗi cũ không được tách khỏi trạng thái done bằng hàm JavaScript thật.
- Tái hiện SDK HTTPError mất mã status và đường full-size/bản thường bằng đúng SDK ghim, không gọi Google.
- Đối chiếu đường mặc định và scope hội thoại, ledger, endpoint nhận tệp và bộ đóng gói .145–.151.
- Các kiểm tra cũ dùng provider/GeneratedImage.save giả lập không mô phỏng đủ lỗi tải thực, nên việc chúng qua không chứng minh tài khoản thật tạo-và-nhận ảnh thành công.
- Ảnh chụp .151 xác định lỗi thuộc giai đoạn tải ảnh; chưa xác định được mã HTTP hoặc nguyên nhân mạng/phiên/URL cụ thể ở máy người dùng.
- Các chương trình tái hiện chỉ đặt trong `diagnostics/frame-code-audit-20261122`; chưa thay code chạy hoặc phát hành bộ cập nhật mới trong lần rà soát này.

Thứ tự sửa: (1) trạng thái và khôi phục kết quả đã tạo, (2) bộ tải ảnh/HTTP diagnostics, (3) dấu đối soát bền vững và tương thích lượt cũ, (4) thống nhất các đường retry và dọn trạng thái UI. Cần kiểm tra tạo + tải lại đúng một kết quả, không chỉ kiểm tra POST gửi đi.
