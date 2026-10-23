# SceneForge · Khôi phục công việc và việc cần làm · 23/10/2026

Bổ sung theo yêu cầu cải thiện phần mềm. Giữ trang chủ bốn cột, cấu trúc hai workflow, Storyboard, timeline và khung Cài đặt đã duyệt. Không cài thêm repo hoặc bật gọi dịch vụ trả phí.

## Thay đổi

1. **Trạng thái công việc cục bộ có SQLite.** `local-jobs.sqlite` cạnh vault lưu trạng thái CPU, chuyển bản ghi sang MP4 và xuất timeline, kể cả kết quả CPU. Ghi nhận trước khi chạy; chuyển trạng thái/kết quả ghi ngay bằng giao dịch, tiến độ trung gian giới hạn khoảng một lần/giây. Không lưu process/task, đường dẫn tùy ý hoặc lệnh thực thi vào DB. Khởi động lại dựng đường dẫn từ ID đã kiểm tra và thư mục cố định của app.
2. **Khôi phục theo kết quả thực.** Việc xong giữ kết quả để đọc/tải lại khi file tạm còn tồn tại. Việc đang nhận tư liệu, xếp lượt hoặc đang chạy khi app bị dừng được báo `error` cùng cờ `recovered` và lời giải thích bị ngắt; không tự chạy lại. Đóng server bình thường cũng ghi nhận các việc còn dang dở. File MP4 mất sau khi đọc trạng thái trả lỗi 410 và cập nhật trạng thái; không tự render file thay thế.
3. **Hàng chờ có Công việc trên máy.** Hiển thị tiến độ, lỗi, mở đúng phòng, dừng việc đang chạy hoặc chờ, tải MP4 đã xong. Tải lại kết quả có thể lưu Blob vào thư viện đúng phòng; không thay bản xuất của phòng nếu phòng đã có bản mới hơn. Kết quả CPU mở phần xem trước; người dùng vẫn chọn có áp dụng cảnh/lời hay không.
4. **Đối chiếu nguồn CPU.** Đọc kết quả phục hồi kiểm tra SHA-256 với byte nguồn đang dùng, đồng thời kiểm tra phòng và asset chưa đổi trong lúc chờ. Kết quả thiếu dữ liệu hoặc khác nguồn không được đưa vào phần áp dụng. Không tự đổi cảnh, lời hoặc clip. Việc tải kết quả chỉ GET trạng thái/file, không gửi lệnh phân tích hay render mới.
5. **Xếp lượt tác vụ nặng.** Các job phân tích CPU companion và hai loại xuất FFmpeg dùng chung một suất xử lý. Việc xuất đang chờ được ưu tiên trước phân tích đang chờ; không hủy công việc đã bắt đầu. Dừng một việc đang chờ giải phóng đúng hàng đợi. Các kiểm tra dung lượng đã có trước khi nhận việc được giữ. Chưa bao gồm TTS, tác vụ hình ảnh nhỏ hoặc bộ dò cảnh chạy trong trình duyệt.
6. **Thẻ Cần bạn rõ và có đường đi.** Dùng số đã lưu để ghi khung chưa duyệt, số cảnh chưa đủ clip, đủ clip để mở Dựng, MP4 xong để tải lại, lượt bị ngắt hoặc yêu cầu provider chưa rõ kết quả. Bấm đưa tới Hàng chờ, phòng Dựng hoặc node khung/clip tương ứng. Không suy số clip theo thời gian hoặc tự duyệt khung. Job `submitted` và `running` cũ sau tải lại được chuyển `unknown`; không gửi lại.
7. **Hiển thị nơi lưu thật.** Cài đặt Thư mục lưu chỉ rõ thư viện và đường dẫn dữ liệu nền/log. Nhận tư liệu cũng được tính là bận để chặn chuyển thư viện giữa lúc upload. Chưa có chuyển toàn bộ data root trong app: tài khoản/vault, log và các job vẫn ở data root hiện tại; chỉ thư viện có thao tác chuyển đã có. Chuyển chung an toàn cần dừng app, sao lưu từng SQLite đang mở, xác minh bản chép và cơ chế chọn gốc ở lần khởi động sau; không âm thầm chép key hoặc đổi đường dẫn giữa phiên.

## Thời hạn và giới hạn

- MP4 chuyển từ bản ghi là file tạm, được dọn khi khởi động/tạo lượt mới sau khoảng 1 giờ từ khi tạo. MP4 timeline dùng cửa sổ 24 giờ; tư liệu trung gian được dọn sau khi render kết thúc. Hàng chờ nhắc tải và lưu vào thư viện để giữ lâu dài. File trong thư viện/bản xuất riêng không thuộc các lượt dọn này.
- CPU giữ tối đa bốn lượt trong registry; khi nhận lượt mới, các kết quả cũ hơn 30 phút có thể được dọn hoặc lượt kết thúc cũ nhất được thay. Đây không thay thế việc lưu kết quả đã rà vào dự án hoặc xuất ZIP đầy đủ.
- Không tiếp tục mã hóa từ phần MP4 viết dở và không tự chạy lại phân tích. Có thông báo và nguồn/timeline đã lưu để người dùng chủ động chạy lại. SQLite không khôi phục được dữ liệu trình duyệt chưa kịp lưu trước sự cố.
- Lớp phục hồi này áp dụng công việc trên máy. Flow/Muse vẫn chưa có adapter tạo clip đã kiểm chứng; chưa có truy vấn mã việc thật của provider. Sổ Gemini từ đợt trước giữ nguyên, không gọi lại yêu cầu mơ hồ.
- Mục Công việc trên máy chỉ bật ở bộ chạy localhost, không gọi API trong `?demo=1`. Trạng thái dùng polling khi xem app, không phụ thuộc tab mở để công việc server tiếp tục.
- Chưa chứng nhận máy Windows 8 GB, mất điện phần cứng hoặc phân phối bộ cài ký số. Các bài kiểm thử dưới đây chạy Linux/Chromium, đường dẫn có dấu và khoảng trắng.

## Bằng chứng kiểm thử

- `local_engine/check_job_recovery.py`: xuất H.264 bằng FFmpeg thật ở hai luồng, dừng/mở lại server, tải cùng byte; giữ kết quả CPU; upload dở và CPU đang chạy chuyển trạng thái bị ngắt, start lại cùng upload bị chặn; file mất trả 410. Kiểm thử ưu tiên xuất và hủy người chờ bằng lịch xác định. Không gọi provider.
- `scripts/app-shell/check_recovery.py`: Chromium + companion thật; thẻ khung/clip, job submitted tải lại thành unknown, mở Hàng chờ, tải MP4 và đồng bộ thư viện, giữ bản xuất mới hơn, hiển thị root/log; không gửi lệnh AI/render từ phục hồi.
- `scripts/app-shell/check_cpu_result_guard.py`: sai hash/thiếu kết quả bị chặn; đúng byte mở xem trước và không đổi cảnh/lời; chỉ GET trạng thái.
- Hồi quy xuất timeline thực với cut/fade/dissolve/slide/wipe, CPU cắt cảnh/OCR bằng fixture, bảo vệ session/migration/ledger, thư viện, trang chủ giữ DOM/focus/cuộn và căn khung các tab.
