# Tạo hàng loạt — thiết kế theo lượt, 27/10/2026

## Giao diện và dữ liệu
- Cột chuẩn bị 330px, kết quả là lưới ảnh dọc; năm ô trạng thái đồng thời làm bộ lọc. Mỗi job mới nhất của một prompt/biến thể là một ô. Số đếm và danh sách lấy cùng trạng thái; bản không ưng thuộc Cần bạn, không tính hoàn tất.
- Lượt có mã độc lập, tên, thời gian; menu chọn lượt và nút Lượt mới. Lượt mới xóa draft, không xóa ảnh lượt trước. Dữ liệu cũ được nhận theo group có sẵn; không bỏ job/ảnh cũ.
- Tự nhận prompt đánh số: dòng tiếp theo thuộc cùng prompt đến số kế tiếp; đoạn cách dòng trống hoặc từng dòng; có lựa chọn Từng dòng/JSON và hộp rà sửa trước gửi. Không dùng AI để tách, không tự gửi khi dán. Giới hạn vẫn 60 prompt/lượt, 200 job lưu chung.
- Thông tin nguồn/tài khoản hiện dưới Động cơ. Nút chạy thật vẫn rà đúng source, model, account selection token và checkpoint kho máy trước gửi; đổi lựa chọn sau rà bị chặn. Không tự đổi API/nguồn khi chat lỗi.
- Hàng đợi chỉ lấy việc chưa gửi thuộc lượt đang mở. Tác vụ đã gửi tiếp tục nhận kết quả dù đổi lượt. Tạm dừng chỉ chặn gửi mới.
- Tạo lại tạo request ID mới, cùng group/promptKey/variant; hiện bản mới nhất trong cùng ô, bản cũ giữ tới khi đóng/dọn. Không tự chạy hoặc xác nhận khoản phí; lượt chưa rõ phải lấy lại/đối soát trước khi tạo thêm.
- Thanh chọn ảnh: tải N, ghim/bỏ ghim và dùng ảnh làm khung qua luồng đang có. Chuyển khung hiện chọn đúng một ảnh/phòng/cảnh mỗi lần, không tự phân nhiều ảnh vào nhiều cảnh.
- Bỏ = người dùng đánh dấu không ưng, loại khỏi tải mặc định. Không có tự phát hiện nhãn mờ/khác mặt. Đã bỏ vẫn có thể xem trong Cần bạn và tạo lại.
- Tải ảnh đạt của lượt đang mở; thanh Tải N chỉ lấy những ô được chọn. ZIP chỉ lấy ảnh hiện được chọn trong mỗi ô, không tự kèm các ảnh khác do provider trả cùng lượt; ảnh phụ vẫn chọn trong hộp kết quả.

## Đóng & dọn
- Có xác nhận, chặn việc đang chạy hoặc chưa rõ. Các việc chưa gửi được hủy khi đóng.
- Quét tham chiếu ở các store trước khi bỏ alias file. Giữ job ghim, job đã giao vào workflow, file được sản phẩm/phòng/draft khác tham chiếu và các dependency cần thiết. Giữ cả chuỗi tổ tiên của job được bảo vệ. Ghi prefs + xóa alias files một transaction IndexedDB.
- Lượt đã đóng có ảnh cần giữ vẫn chọn xem/tải được. Lượt dọn hết không còn chiếm danh sách chọn; metadata tên/thời gian đóng giữ lại. Không xóa canonical file thẳng từ frontend. Kho máy/sao lưu/ledger vẫn có thể giữ file; không gọi số mục dọn là số GB giải phóng.
- Chưa bật tự xóa 24h hoặc quota tự dọn Batch trong đợt này. Không thay chính sách lưu trữ toàn app. Thư mục media và model không bị dọn bởi thay đổi này.

## Kiểm thử và giới hạn
- UI Chromium/IndexedDB/Blob thật: lượt riêng, ZIP thực chỉ có ảnh chọn, ảnh phụ ẩn không bị tải kèm, cờ không ưng, gen lại cùng ô và paused, draft mới, đóng giữ ghim + tham chiếu phòng, loader sau restart, mobile.
- Flow/Grok/ChatGPT/Meta có test HTTP/SQLite và provider giả: đúng nguồn/tài khoản/token, chặn đổi token, nhận ảnh gốc, recovery không gửi lại, Settings dùng chung. Không chứng nhận selector website online hoặc quota thật.
- Settings, Thùng rác/Lưu trữ, backend result receipts và storage jobs hồi quy đạt. Một bài fixture chờ app chưa boot xong đã sửa điều kiện chờ; log lỗi ban đầu giữ riêng. Không có bằng chứng Windows hoặc gen thật.
- batch-design-demo.html là dữ liệu mô phỏng riêng: 10 prompt, 7 xong, 2 chờ, 1 lỗi minh họa; có thể chạy simulation thực trên trình duyệt. Không dùng account/provider online.

Code chính: scripts/app-shell/batch-redesign.js/.css; batch-studio.js giữ submission/receipts, chỉ thêm scope lượt vào scheduler/start và validation metadata. Kết quả kiểm: batch-redesign-checks.json.
