# SceneForge · Phần phía sau · 23/10/2026

Đợt này củng cố bộ chạy cục bộ. Không thay bố cục trang chủ, hai workflow, Storyboard hoặc lõi Dựng. Giữ tài liệu gốc trong `design/runtime-received/SceneForge_PhiaSau.md`.

## Đã triển khai

- **Phiên loopback:** sinh bí mật 256 bit mỗi tiến trình, cấp qua cookie HttpOnly / SameSite=Strict khi tải tài liệu HTML cùng ứng dụng. Mọi API riêng, kể cả GET tư liệu và tải ZIP, cần cookie đúng phiên; ghi còn cần `X-SceneForge-Local: 1`. Kiểm tra Host, Origin đầy đủ cả scheme/cổng và Sec-Fetch-Site; chặn nhúng giao diện từ origin khác. Health chỉ trả thông tin tối thiểu, không cần phiên. Không đưa bí mật vào URL, JavaScript hay log. Khởi động lại server cần tải lại trang để nhận phiên mới.
- **Một tiến trình qua launcher:** khóa hệ điều hành trên file, tự giải phóng khi tiến trình chết. Lần mở sau dùng URL của tiến trình đang chạy; trên bản trình duyệt có thể mở lại tab, chưa hứa đưa một cửa sổ desktop lên trước. Cổng 8840 bị chiếm thì bind cổng loopback do hệ điều hành chọn. Không tìm/diệt tiến trình đang chiếm cổng. Áp dụng khi chạy `python -m local_engine` / start.bat; người tự chạy nhiều lệnh uvicorn trực tiếp tự chịu trách nhiệm điều phối.
- **Nâng cấp SQLite:** thư viện, vault và sổ yêu cầu có `PRAGMA user_version=1`. Cơ sở dữ liệu cũ v0 được sao lưu SQLite có kiểm tra integrity trước khi nâng; DDL và tăng phiên bản trong một giao dịch. Lỗi thì rollback giao dịch, giữ bản sao. Dữ liệu có phiên bản mới hơn app bị từ chối sửa. Bản sao trước nâng nằm cạnh DB trong `schema-backups/`, không tự xóa. Các hash còn được bản sao thư viện tham chiếu được bảo vệ khi dọn; chuyển thư viện cũng chép và xác minh các bản sao này.
- **Sổ gửi Gemini:** `requests.sqlite` ghi claim trước khi gửi ở helper Gemini chung (kịch bản, công thức, phân loại, các tác vụ dùng helper này). ID sinh trước fetch trong hai helper giao diện; API cũng cấp ID nếu client cũ không gửi. Cùng ID/nội dung đã xong trả lại kết quả đã lưu; cùng ID/nội dung khác bị chặn. Đang gửi, mất mạng, hủy, kết quả không đọc được hoặc tiến trình chết chuyển/giữ `unknown`, không tự gửi lại. `/local-api/requests` chỉ trả ID, trạng thái, thời điểm, không trả prompt hay kết quả. Chỉ các 429 bị từ chối rõ ràng còn dùng chính sách chờ có giới hạn đã có. Kết quả Gemini được lưu cục bộ để trả lại cùng thao tác; không đưa DB này vào ZIP thư viện.
- **Log có giới hạn:** runtime log chỉ ghi giờ, phương thức, nhóm API, mã HTTP, thời lượng; không ghi body, query, cookie, key hoặc nội dung exception. Mỗi file tối đa khoảng 1 MiB, giữ 4 file cũ. Phần diagnostics có 20 dòng mới nhất. Log tác vụ trong vault che trường nhạy cảm/prompt trước ghi, che lại khi đọc dữ liệu cũ và giữ tối đa 5.000 dòng. Kết nối vault đóng sau mỗi giao dịch.

## Giới hạn quan trọng

Đây là nền bảo vệ và ghi nhận yêu cầu, **chưa phải toàn bộ hàng chờ Flow/Muse bền vững**. Các adapter này vẫn chưa được kiểm chứng và nút gửi thật vẫn bị khóa. Một ID nội bộ không bảo đảm nhà cung cấp chống trùng; khi tích hợp cần lưu mã việc từ provider, hỏi lại trạng thái nếu API hỗ trợ, không gửi lại việc mơ hồ. Client cố tình tạo ID mới là một thao tác mới, không được sổ yêu cầu tự đoán là bản trùng. Helper Gemini riêng của phân tích ảnh/khung chưa được chuyển hết sang sổ chung; không công bố đã bảo vệ mọi cuộc gọi AI.

CPU/FFmpeg có cơ chế hủy tiến trình con do app tạo và khóa xuất chung từ bản trước; chưa thay bằng supervisor cho mọi động cơ, chưa khôi phục các công việc CPU/xuất đang chạy sau khi mất điện. Giữ polling tiến độ hiện có; chưa thêm SSE trước khi các job provider có nguồn trạng thái bền thực sự.

Chưa áp dụng tự xóa toàn bộ cache trên 10 GB hoặc xóa tmp mỗi lần mở: các thư mục hiện chứa cả tư liệu đang dùng, chỉ dọn những file đã phân loại an toàn và có xem trước. Chưa thêm bộ điều phối chung OCR/giọng/xuất, nhả model sau 5 phút, Flow mô phỏng FFmpeg, updater, bộ cài ký số hay chứng nhận máy Windows 8 GB. Các mục này cần tích hợp và thử riêng, không coi là đã xong. Không khuyên mở tường lửa rộng cho dịch vụ loopback.

OpenReel giữ ở mức đánh giá riêng; không thay editor hoặc sao chép mã chưa kiểm tra giấy phép. Trang giấy phép tổng hợp và kiểm kê model/binary cần audit nguồn phân phối thực tế, không gắn nhãn MIT cho mọi thành phần. Thông tin riêng tư cần nói đúng: app không thêm telemetry; khi người dùng gọi Gemini/Flow, dữ liệu cần cho thao tác được gửi tới dịch vụ đã chọn. Phân tích Gemini có hạn mức/chi phí tùy key, không phải luôn 0 đồng.

## Kiểm tra

- `check_runtime_safety.py`: session thiếu/sai/đổi sau restart, GET/POST, Host/Origin/cross-site; HttpOnly; log không lộ query/prompt; migration lỗi rollback, pre-backup, chặn DB tương lai; ledger chặn gửi lại sau hủy/restart, trả cache và chặn đổi payload; OS lock và cổng bị chiếm. Provider dùng mock.
- `check_instance_live.py`: chạy launcher/server thật, cổng bận tự đổi, mở lần hai dùng cùng URL, dừng/mở lại với lock file còn trên đĩa, đường dẫn có dấu và khoảng trắng trên Linux.
- `check_library_browser.py`: Chromium thật nhận cookie, đồng bộ IndexedDB/SQLite, blob/voice/timeline, iframe Dựng, tải ZIP qua liên kết và khôi phục profile mới, mất kết nối và xung đột revision. 200 phòng metadata đo khoảng 214 ms trên máy kiểm thử, không phải cam kết cho 200 video lớn.
- Hồi quy vault/chính sách tài khoản, settings/retry/diagnostics, thư viện/API, bố cục và chuyển workflow.

Không gọi AI trả phí hoặc đăng nhập thật trong các bài kiểm tra. Chưa thử nhánh khóa Windows, antivirus, mất điện phần cứng hoặc focus cửa sổ desktop trên máy Windows thật.
