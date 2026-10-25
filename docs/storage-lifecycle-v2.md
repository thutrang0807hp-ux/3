# Lưu trữ và dọn dung lượng v2 — 26/10/2026

Đợt này triển khai riêng lưu trữ. Không cài thêm model/repo, không chạy tài khoản AI thật và không dọn dữ liệu người dùng trong môi trường làm việc. Kiểm thử dùng thư mục/profile tạm.

## Cách dùng

Bản local đã kết nối kho máy có các thao tác sau:

- Trong Lưu trữ: **Dọn / xóa hẳn** trên từng dự án. Menu chuột phải dự án có **Dọn bản không dùng** và **Xóa hẳn dự án**. Canvas workflow có **Dọn bản thừa** để lưu/đóng phòng rồi mở cùng hộp quản lý.
- **Dọn phiên bản không dùng**: bỏ clip/ảnh không được chọn; giữ bản trên timeline, khung được duyệt/chọn và bản ảnh mới nhất chưa duyệt. Những tham chiếu còn trong lịch sử cũng được bảo vệ, vì vậy không cam kết dọn hết mọi phiên bản cũ.
- **Chốt thành phẩm & dọn tư liệu**: giữ video xuất, SRT, ảnh đại diện, phần chữ/kịch bản/bản dịch/prompt; bỏ bản dựng đầy đủ và media trung gian riêng. Backend kiểm hash và đọc thành phẩm bằng ffprobe trước khi cho chốt.
- **Xóa hẳn dự án**: bỏ dự án và media riêng trong kho. Không xóa Bộ ảnh/Bộ cảnh dùng chung, bản ghim hay kịch bản đã lưu độc lập vào Kho. Có checkbox riêng để xóa cả những bản xuất được app ghi trong bảng published; file đã thay đổi ngoài app hoặc đường dẫn không còn khớp được giữ và báo lỗi. Bản sao khác ngoài app không bị xóa.
- Chọn **chờ 7/30 ngày** hoặc **xóa ngay**. Chờ xóa chưa làm ổ nhẹ ngay. Trong **Lượt dọn / lấy lại** có lấy lại dự án bị xóa còn trong thời hạn chờ, đẩy sang xóa ngay, hoặc thử lại lỗi. Xóa ngay không có đường lấy lại file đã xóa.
- Có nút **Dọn / xóa các dự án đã chọn**, xử lý tuần tự; lỗi thì dừng và giữ kết quả những dự án đã xử lý.
- **Kết quả chờ nhận / đối soát** cho xem job chưa nhập, tải kết quả đã lưu và chủ động bỏ sau khi kiểm lịch sử. Bỏ kết quả không hủy tác vụ online, không hoàn credit và không tạo lại. Backend từ chối bỏ khi việc còn chạy trong app.
- Cài đặt → Thư mục lưu: đặt dung lượng trống tối thiểu (mặc định 256 MB) và trần media trung gian được quản lý (mặc định 0 = không đặt trần). Mức dự phòng mới là ước lượng có biên an toàn, không bảo đảm mọi thao tác sẽ đủ ổ.

## Cơ chế backend

`storage_lifecycle.py`, `storage_jobs.py`, `library_lock.py` bổ sung vào kho SQLite schema v2:

- Trạng thái file và operation/item; khu `kho/.cho-xoa/<op>/`. Ghi intent bền trước đổi tên; chỉ cộng số byte file bị xóa sau unlink. Có thử lại, phục hồi file khi commit/upload cần dùng và xử lý tiếp operation đã được xác nhận sau restart.
- Lease 24 giờ cho mỗi upload, kể cả dedup. Commit tham chiếu sẽ gỡ lease. File có lease, pin, tham chiếu hiện hành hoặc kết quả chưa nhập không bị dọn. Vì vậy một số file mới có thể vẫn được bảo vệ khi chọn xóa ngay.
- Ghi nhận release theo **room + hash**, và deleted_room. Bản sao lưu cũ không bị sửa/xóa để làm trống ổ. Khi tính bảo vệ và restore, chỉ bỏ phần tham chiếu mà chính dự án đó đã được cho phép giải phóng. Một dự án khác hoặc tài nguyên dùng chung vẫn bảo vệ file.
- Restore mặc định bỏ dự án đã xóa hẳn. Tư liệu đã chủ động giải phóng được đánh dấu; timeline/phiên bản thiếu được gỡ hoặc đưa về final-only tương ứng, kèm báo cáo. Thiếu ngoài ý muốn không được âm thầm bỏ qua: có lựa chọn khôi phục dự án còn đủ; nếu thiếu tài nguyên dùng chung/pin thì vẫn chặn.
- Ghi nhận release/deleted đi theo SQLite khi chuyển nguyên thư viện. ZIP toàn thư viện mang chính sách sang kho đích mới chưa có dự án/lịch sử xóa; không áp chính sách của thư viện khác đè lên kho đang dùng. Mã dự án trùng một dự án đã xóa bị từ chối thay vì hồi sinh âm thầm.
- ZIP dự án không mang lịch sử xóa toàn thư viện. Nếu còn dữ liệu có thể lấy lại trong thời hạn chờ thì xuất ZIP bị chặn để tránh bỏ sót; lấy lại/chốt xóa trước, hoặc chuyển nguyên thư viện để giữ cả khu chờ.
- Có khóa OS cho mỗi root thư viện trong một máy. Không hỗ trợ hai máy cùng ghi qua thư mục đồng bộ/NAS; không coi file khóa chứa PID là bảo đảm khóa phân tán.

## Nối với media

- Request ledger vẫn giữ chống gửi trùng, không bị thay. room/scene/kind được lưu cùng claim; registry kho được ghi trước khi tạo task. Nếu đứt giữa hai DB, startup đối soát từ metadata bền; không phát lại generation.
- Flow/Muse/Gemini và ảnh API mới: kết quả được kiểm ở adapter rồi chép vào kho hash, ghi catalogue trước khi bỏ bản riêng ở thư mục results. Download vẫn qua route cũ. Bản sao chưa bỏ được được ghi alias để dọn lại có kiểm hash.
- Photo Studio: đọc receipt trong `rooms.photoDraft` (Flow/Muse/Gemini), không nhầm với project workflow. Dọn bản thừa giữ clip đang chọn/trên timeline, storyboard đang chọn và bản mới nhất; file chưa nhận diện được vẫn giữ.
- Import được xác nhận khi canonical snapshot có **đúng job ID + đúng room + hash media**. Ảnh khung giữ thêm file nguyên gốc để chứng minh đúng hash dù preview là JPEG. Không dùng việc hiện thumbnail làm ACK.
- VieNeu mới: WAV vào cùng kho, URL cũ được ánh xạ bền; nhận giọng dựa đúng request ID trong version và hash. Các WAV cũ chưa đủ liên kết không bị xóa đoán.
- MP4 FFmpeg theo room vào kho ngay khi render hoàn tất, trước khi browser nhận file. Chỉ khi hash nằm ở `<room>:export` mới đánh dấu nhập. Kết quả chưa nhập có đường tải riêng từ catalogue.
- Sổ job và dấu vết thao tác được giữ để đối soát; media có thể được giải phóng. Xóa dự án trong app không phải công cụ xóa dấu vết/secure erase mọi metadata trong sao lưu SQLite cũ.

## RAM và dung lượng

- Đường dọn local mới xử lý metadata/marker ở backend, không ghi journal chứa toàn bộ Blob như đường browser cũ.
- Hash file lớn theo khối trong Web Worker; file lớn đã có trong kho được xác minh và tạo lease qua assets/check, tránh upload lại nguyên file chỉ để lưu metadata. Backend hash theo stream.
- Cache có giới hạn số lượng và dung lượng tham chiếu/data URL. ArrayBuffer/typed array mới lưu thành asset thay vì mảng số JSON; vẫn đọc được định dạng cũ.
- AI admission dự phòng 500 MB/job video, 32 MB/job khác, cộng việc đang gửi và phần trống tối thiểu. CPU/export có chặn ingress khi thiếu chỗ. Đây là ước lượng; chưa benchmark 10 video thật trên PC người dùng.
- Chỉ số freed_bytes đếm kích thước file được thao tác xóa trong kho/alias/bản xuất đã chọn, không là cam kết số free-space toàn ổ sẽ tăng đúng từng byte do filesystem, hoạt động khác và bản sao ngoài phạm vi.

## Giới hạn hiện còn

- Thao tác dọn hiện thận trọng: đợi việc local/cloud đang chạy kết thúc trước khi thực hiện. Các receipt restored/legacy thiếu sổ request được đưa vào danh sách đối soát, không tự gửi lại.
- Không tự xóa file backend cũ không đủ bằng chứng thuộc dự án, file bên ngoài, logs/model hoặc sao lưu độc lập đã xuất. Nguồn không nhận diện phải được giữ; không báo là đã dọn toàn bộ ổ.
- Native export không có room vẫn dùng TTL cũ. CPU/temp/archive cache giữ cơ chế cleanup riêng; chưa có bảng đo thống nhất tất cả thư mục tạm.
- Snapshot checkpoint vẫn là toàn bộ metadata, chưa chuyển sang delta. Journal metadata, quét backup và xác minh hash vẫn có chi phí I/O. Không tuyên bố đã tối ưu xong thư viện rất lớn.
- Bản web tĩnh chỉ có đường lưu browser cũ; ba thao tác backend mới cần bộ chạy local. Quyền storage.persist được xin từ thao tác người dùng, không bảo đảm chống mọi trường hợp mất browser data.
- Chưa chạy Windows thật, chưa chứng nhận đồng bộ nhiều máy hay vòng gen tài khoản online thật. PermissionError/crash/low disk được kiểm bằng fixture trên Linux.

## Kiểm thử

- `check_storage_lifecycle`: SQLite/file thật; release vượt bảo vệ backup đúng scope; giữ final/text/shared; lease dedup; quarantine/revive; ngắt sau rename; retry không đếm trùng; cancel chờ xóa; chọn published; ZIP mang policy; partial restore có lựa chọn.
- `check_storage_jobs`: canonical result + bỏ alias, room/job/hash import proof, unknown/active discard, low disk trước claim, không phát generation.
- `check_storage_voice_api`: WAV thật qua API/kho/hash/URL và xóa cùng dự án; synthesis fixture.
- `check_storage_ui`: Chromium → API/SQLite thật: xác nhận, compact/delete/unused, giữ timeline, bulk, reload; Worker hash 9 MB và round-trip typed array.
- Kiểm lại library/API, archive release, admission/recovery, runtime safety, direct workflow/voice UI, Gemini routes, Flow/Muse fixtures và FFmpeg export thật.

Chỉ đánh dấu bài thực sự chạy PASS trong báo cáo kèm gói; không dùng bài browser cũ timeout làm bằng chứng.
