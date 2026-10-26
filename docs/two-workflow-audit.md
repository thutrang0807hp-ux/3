# Rà hai luồng sản xuất — 26/10/2026

Đợt này sửa đường gửi/nhận và điều kiện dùng lại kết quả; không thêm node, model hay nhà cung cấp. Đây là kiểm code và thử Chromium + lưu trữ thật với transport AI giả lập, không chứng nhận tạo video online bằng tài khoản thật.

## Luồng giữ lại

| Luồng | Công việc chính | Điều kiện sang bước tiếp |
|---|---|---|
| Video mẫu | Nhập video vào phòng → CPU dò mốc, trích bằng chứng, Whisper chép lời, OCR/đo camera khi có → Gemini Chat hiểu cảnh/dịch/viết hướng dẫn → ảnh khung + bộ ảnh thay thế → duyệt khung → prompt video → gen từng phần → nhận/duyệt clip → Dựng → xuất | Ảnh khung đã duyệt; clip khớp khung/prompt/mốc và đủ thời lượng; kết quả chưa rõ phải đối soát |
| Ảnh & ý tưởng | Ảnh tham khảo từ sản phẩm hoặc máy → kịch bản → một storyboard tổng → Gemini đọc storyboard + bộ ảnh gốc và viết prompt theo nhóm → gen clip vào Bộ cảnh video → xem bản ghép → tạo lại đúng phần sai → chốt → Dựng → xuất | Có storyboard, prompt khớp dữ liệu và không có lượt chưa rõ; không bắt tạo/duyệt ảnh riêng từng cảnh hoặc duyệt từng clip trước khi xem bản ghép |

Nếu chọn giọng riêng, tạo/nhập file trước để chốt mốc. Tiếng clip/native không cần lượt VieNeu riêng. Phụ đề và nhạc là tùy chọn; ghép và xuất dùng xử lý trên máy. Storyboard được dùng thật làm đầu vào viết prompt, không gửi lưới nhiều ô làm ảnh đầu của từng clip.

Hai tab mở hai dự án riêng trong cùng sản phẩm, ghi nhớ phòng gần nhất. Chuyển tab không chuyển đổi hay chép toàn bộ dự án. Kho kịch bản là đường dùng lại công thức; bộ ảnh sản phẩm được chụp riêng khi tạo phòng mới. Dự án cũ và tư liệu đã tạo được giữ.

## Những điểm đã sửa hoặc gom lại

1. **Giữ prompt đã viết ở luồng Ảnh.** Trước đây chạy lại bước chuẩn bị xóa danh sách nhóm đang dùng và gửi toàn bộ. Nay lưu dấu đầu vào từng nhóm tối đa 8 nhịp; giữ nhóm đã nhận hợp lệ, chỉ xác nhận/gửi nhóm thiếu hoặc đã sửa. Dữ liệu đã đủ thì gửi 0 lượt. Không tự gửi lại khi chỉ mở lại tab hoặc nhận kết quả.
2. **Kết quả nhóm độc lập.** Thay lời ở nhóm khác không làm bỏ kết quả hợp lệ của nhóm đang về. Cả dự án chỉ được coi là sẵn sàng khi tất cả nhóm khớp dữ liệu hiện tại. Nhóm sai cấu trúc hoặc chưa rõ vẫn chặn; không âm thầm tạo một lượt mới.
3. **Clip cũ không che ô đang thiếu.** Video mẫu trước đây bỏ qua ô chỉ vì có clip bất kỳ. Nay bỏ qua khi bản mới nhất thực sự còn dùng được; bản nhận về đang chờ duyệt không bị gửi gen thêm. Khung/prompt/mốc sai hoặc clip quá ngắn bị chặn duyệt/ghép, có thể tạo lại đúng phần.
4. **Ảnh đã nhận không bị tạo thừa.** Ảnh mới đang chờ duyệt được giữ làm ứng viên. Ảnh tự tạo ghi dấu đầu vào; lấy bằng chứng video gốc ổn định làm nguồn, không vô tình thay bằng chính ảnh vừa gen khi đối soát. Nút Tạo lại vẫn là thao tác chủ động.
5. **Lưu ý định trước khi gửi AI.** Hai luồng dùng chung một hàm lưu ý định và đợi checkpoint thật. Nếu ổ/kho lưu chưa xác nhận, dừng trước HTTP gửi AI và ghi chưa gửi. Mất phản hồi sau dispatch vẫn là chưa rõ, không suy thành chưa gửi.
6. **Nhận lại phân tích chỉ đọc.** Endpoint đọc JSON đã có yêu cầu đúng kho dữ liệu. ID biến mất hoặc kho đổi thì dừng; không biến thao tác nhận kết quả thành một lần gọi Gemini mới. Đổi nguồn sang API cũng không được dùng để đọc lại theo cách phát sinh yêu cầu mới.
7. **Theo dõi trạng thái hàng đợi.** Video mẫu nhận tiếp job ở `queued/preparing`, không chỉ `submitted/running`. Lượt thiếu/JSON lỗi vẫn khóa gửi trùng ở cùng ô.
8. **Kho công thức còn một nhánh.** Code cũ có nhánh gọi AI bổ sung, nhưng bản build đang chạy đã ghi đè bằng nhánh lưu cục bộ ở package6. Đã bỏ phần định nghĩa trùng và đưa nhánh thực về recipes.js. Không tính đây là lỗi tốn credit đang xảy ra. Khi có công thức từ phân tích về sau, cập nhật khung tự lưu; giữ bản người dùng đã sửa. Không sao chép lời nguồn vào công thức tự dựng.
9. **Không tạo phòng ma khi lưu thất bại.** Chỉ thêm phòng mới vào danh sách sau khi lưu thành công. Dòng chỉ dẫn hai tab nói rõ đang mở dự án riêng, có giới hạn chiều rộng để giữ thanh công cụ ổn định.

## Các lượt AI nên có và không nên có

| Việc | Dùng gì | Phát sinh khi nào |
|---|---|---|
| Dò cảnh, chép lời, OCR, đo camera | Thư viện/model CPU đã cài | Xử lý trên máy; không phải credit Flow |
| Hiểu/dịch cảnh và viết prompt | Gemini Chat đã chọn | Khi xác nhận gửi; nhóm đã xong không tự gửi lại |
| Storyboard tổng (luồng Ảnh) | Gemini tạo ảnh hoặc nhập ảnh sẵn | Một tài liệu định hướng; không bắt một lượt tạo ảnh cho mỗi nhịp |
| Ảnh khung (Video mẫu) | Gemini Chat hoặc nhập file | Chỉ cảnh thiếu/đã đổi, hoặc chủ động Tạo lại |
| Clip | Flow hoặc Muse adapter hiện có | Hiện số yêu cầu trước gửi; nhận kết quả không tạo thêm clip |
| Giọng riêng | VieNeu hoặc file | Tùy chọn; không tạo thêm nếu đã dùng tiếng native của clip |
| Phụ đề, nhạc, dựng, xuất | Whisper khi chọn nghe thật; file nhạc; FFmpeg/editor | Không gen video lại chỉ để sửa phụ đề hoặc nhạc |
| Lưu công thức | Kho cục bộ | Không gọi thêm AI tự động |

Không bỏ xác nhận trước cloud send, khóa lượt chưa rõ, kiểm khớp dữ liệu, duyệt khung ở Video mẫu hay bảo vệ tệp đang dùng khi dọn: đó là những phần ngăn mất credit/dữ liệu.

## Giới hạn còn lại, không nên che bằng chữ “đã xong”

- **Muse hiện trỏ muse.ai; chưa phải Meta AI người dùng mong muốn.** Có giao diện và adapter không chứng minh đã nối đúng dịch vụ. Không tự thay repo hoặc nhận cookie Meta vào bộ muse.ai.
- Chưa kiểm tài khoản thật/Windows; hạn mức, song song thực và giá credit cần dữ liệu của dịch vụ. Không có số credit ước đoán giả.
- Khung storyboard giúp bố cục/prompt; không đảm bảo tuyệt đối mặt, sản phẩm hoặc đồng nhất giữa clip. Vẫn cần xem bản ghép, sửa đúng ô sai.
- CPU đo camera từ khung liên tiếp không tương đương mô hình hiểu mọi hành động người/tay. Whisper còn nghe sai khi tiếng nhỏ/nhạc lớn; không thêm model nặng trong đợt này.
- Video mẫu còn cách viết prompt riêng từng cảnh trong công cụ chi tiết; có thể dùng prompt phân tích hiện có mà không buộc gọi thêm Gemini. Chưa viết lại toàn bộ UI hoặc hợp nhất hai kiểu dự án.
- Việc sửa thời lượng sau khi đã tạo clip ở Video mẫu vẫn bảo thủ để tránh gán nhầm mốc/lời. Không tự tái chia và gen hàng loạt khi đổi mốc.
- Bảo vệ dung lượng và dọn phiên bản giữ quy tắc hiện có; đợt này không thêm một hệ thống lưu trữ thứ hai.

## Cách kiểm và đọc code

`artifacts/two-workflow-audit-checks.json` ghi từng bài kiểm và phạm vi thật/giả lập. Bản code gọn đi kèm chứa nguyên các file của hai luồng, thứ tự build, phần shell/editor/backend cần truy vết, bản thay đổi so với gói nguồn đang phát hành trước đợt sửa. Không kèm model/media/tài khoản.

Ưu tiên lần tới: kiểm một video thật trên Windows + tài khoản Flow/Gemini đúng dịch vụ; xác minh Meta AI riêng. Không thêm node hoặc model để thay cho việc kiểm đó.
