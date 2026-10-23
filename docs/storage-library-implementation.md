# Thư viện lưu trữ · SQLite, kho chống trùng và ZIP đầy đủ

Triển khai phương án đã trao đổi từ `SceneForge_LuuTru (1).md`. Giữ giao diện Lưu trữ đã duyệt; không tự dọn khi lưu trữ/xuất xong, không tự xóa bản gốc trước xử lý logo.

## Bản cục bộ

- `thu-vien.db`: SQLite WAL, synchronous FULL, foreign keys, giao dịch và revision compare-and-swap. Giữ sản phẩm/phòng, workflow, script, prompt, phiên bản, công thức, hàng chờ, timeline, thông báo và tùy chọn của app qua các bản ghi. Có bảng asset, asset_ref, pin và room_index kèm chỉ mục. Snapshot workflow/editor vẫn là JSON trong SQLite, chưa tách từng cảnh/lời thành các bảng chuẩn hóa riêng.
- `kho/<2 ký tự đầu>/<SHA-256>`: bytes thật, bất biến, không phụ thuộc tên phòng/sản phẩm; cùng bytes chỉ lưu một lần trong kho. Marker giữ MIME, tên File và lastModified để khôi phục. Ảnh data URL cũng tách thành asset. Upload theo luồng, file tạm + fsync + đổi tên trước khi metadata tham chiếu. File upload chưa gắn metadata không làm hỏng bản cũ.
- IndexedDB là bản làm việc tương thích với workflow/editor hiện tại; SQLite là checkpoint bền vững của bộ cục bộ. Theo dõi giao dịch parent và iframe, gom thay đổi khoảng 1,8 giây khi ổn định; chỉ mã hóa lại bản ghi thay đổi. Đọc lại metadata để đối chiếu sau commit. Giữ dirty marker khi lỗi; bật cảnh báo rời trang nếu còn thay đổi chưa đồng bộ. Đây là chuyển đổi theo lớp, không xóa IndexedDB hoặc cưỡng bức sửa mọi màn hình sang SQL trực tiếp.
- Trước lần chuyển dữ liệu có sẵn: tạo ZIP đủ metadata + bytes trong `sao-luu/trinh-duyet-*.zip`, rồi commit và kiểm tra. Không xóa dữ liệu cũ. Thư mục JSON/mirror cũ trên ổ không bị quét/xóa hoặc tự nhận là đã chuyển hết.
- Mở ở browser profile mới: đọc metadata/file và kiểm tra file trước khi ghi cache. Đánh dấu phục hồi giữa chừng để lần mở tiếp theo nạp lại đúng thư viện. Cùng origin dùng Web Locks để giữ một cửa sổ điều phối; khác phiên bản dùng CAS để chặn ghi đè, giữ bản trình duyệt và có nút xuất/nạp lại.
- Key, cookie, tài khoản và nhật ký động cơ tiếp tục ở vault mã hóa cũ, không được đưa vào ZIP thư viện dự án. Chưa gộp nhật ký tài khoản/chi phí ở vault thành bảng cost_log riêng của thư viện.

## Dọn và giữ bản

- Nút ghim trong inspector khung/clip, độc lập bản đang chọn. Ghim lưu vào metadata và bảng pin theo hash trên máy.
- Nút Dọn các bản cũ · xem trước: giữ bản chọn, hai bản mới nhất mỗi nhóm/part, bản ghim và mọi tư liệu còn trong kho Dựng (bảo vệ rộng hơn chỉ các mục đang trên timeline). Xác nhận rồi mới gỡ phiên bản khỏi workflow; giữ Blob nếu source/history/phần khác của dự án còn nhắc tới. Bản web không bật thao tác dọn phiên bản theo disk protection; ghim metadata và xuất ZIP vẫn dùng được.
- Dọn file không dùng: đo byte thật từ file, chỉ xét asset hết tham chiếu của mọi record/timeline/Thùng rác/pin và 14 bản sao lưu SQLite. Bỏ qua file mới dưới 24 giờ để không quét upload đang chuẩn bị. Xem trước + token kiểm tra lại; khóa giao dịch khi đưa file vào Send2Trash. Không có fallback xóa vĩnh viễn nếu Send2Trash lỗi. Báo phần dọn được và phần được giữ khi hệ điều hành từ chối.
- Dọn phiên bản không đồng nghĩa thu hồi ngay số MB đó trên ổ. Backup hoặc phòng khác có thể còn cần cùng asset; bảng dọn file mới báo số byte có thể thu hồi thực tế.
- Thùng rác logic trong app được giữ nguyên: xóa phòng/sản phẩm vẫn khôi phục cả metadata và liên kết; chỉ file thật hết tham chiếu mới vào Thùng rác hệ điều hành. Không cố đưa một bản ghi SQLite vào Thùng rác Windows.
- Cache riêng của thư viện có nút dọn ZIP xem trước quá một giờ; không chạm kho, xuất, sao lưu hoặc file tạm không nhận diện. Cache/working directories cũ của các engine không bị tự dọn bởi nút này.

## Sao lưu, ZIP, chuyển máy

- SQLite `connection.backup`, integrity_check, tệp tạm rồi đổi tên; mỗi ngày có dữ liệu tạo một bản, giữ 14 bản gần nhất (cả bản tạo tay). File được backup tham chiếu vẫn được giữ. Backup SQLite không thay cho sao lưu media ra ổ khác.
- Khôi phục kiểm tra integrity + đủ hash trước khi thay metadata; sao lưu hiện tại trước, tăng revision đơn điệu. Tạm dừng hàng chờ, chặn tự gửi Gemini và chuyển việc đã gửi/chưa rõ sang trạng thái cần kiểm tra.
- ZIP toàn thư viện/từng phòng chứa `du-an.json` và `assets/<hash>`. Bao gồm media timeline, voice file và thư viện sản phẩm mà phòng tham chiếu. Import kiểm tra hash, đường dẫn/định dạng/kích thước, chặn mã trùng nhưng khác nội dung; không ghi đè. Pin theo hash đi cùng ZIP.
- Bản web/GitHub Pages có bộ xuất ZIP chạy hoàn toàn trên trình duyệt, không cần companion và không gửi file tới server. Hash SHA-256 theo khối, CRC32 + ZIP STORE; bytes giống nhau chỉ đóng gói một lần. Dùng ZIP này để chuyển dữ liệu giữa origin web và localhost. Browser không được đọc chéo IndexedDB giữa hai origin.
- Giới hạn hiện tại: mỗi upload asset tối đa 2 GiB; import ZIP tối đa 4 GiB giải nén, metadata 64 MiB; xuất browser giới hạn dưới 3,5 GiB và 60.000 entry (chưa ZIP64). Dự án lớn nên xuất từng phòng hoặc dùng bản cục bộ. Phiên bản đầu không tự gộp/đổi ID hai dự án khác nhau khi import bị xung đột.
- Chuyển thư viện: đường dẫn đích mới chưa tồn tại; chép DB bằng backup cùng kho/xuat/sao-luu, bỏ cache, kiểm tra SHA-256 bản chép rồi đổi cấu hình nguyên tử. Giữ nguyên thư mục cũ để người dùng tự kiểm tra; không tự xóa. Thư mục xuất riêng nằm ngoài thư viện vẫn giữ ở nơi người dùng đã chọn.

## Thành phẩm

Bản xuất ghi trong app được chép thành file tên dễ đọc ở `xuat/<sản phẩm>/` hoặc thư mục xuất chọn riêng. Không ghi đè file khác đã có; xóa export khỏi cache/app không xóa thành phẩm bên ngoài. Không tự tạo lại file mà người dùng đã tự xóa ở thư mục xuất. Nút Mở thư mục gửi yêu cầu mở folder qua hệ điều hành của máy đang chạy companion. Không đổi tên WebM thành MP4 giả; định dạng theo output thật.

Chống trùng áp dụng trong kho. Bản MP4 thành phẩm, ZIP đầy đủ và bản sao trên ổ khác là các bản sao có chủ đích, vẫn chiếm thêm dung lượng.

## Kiểm tra

Đã qua:

- `local_engine/check_library.py`: file thật/SQLite thật; dedup, đổi tên và dùng chung, CAS/rollback/WAL, hai writer, SQLite backup/restore, bảo vệ theo backup và pin, reviewed cleanup, ZIP phòng/voice/timeline, hỏng ZIP/hash, chuyển ổ giữ gốc, bản xuất tồn tại sau dọn. Tắt tiến trình đang mở transaction bằng kill: dữ liệu/revision trước đó khôi phục nguyên vẹn.
- `local_engine/check_library_browser.py`: uvicorn thật + Chromium, chuyển thư viện IndexedDB cũ, ZIP trước chuyển, profile trống khôi phục File/voice/script/timeline; lỗi mạng giữ dirty rồi nạp lại; revision khác không ghi đè; thao tác Settings và tải ZIP phòng; ghi IndexedDB từ iframe Dựng được theo dõi và checkpoint.
- 200 phòng chỉ có metadata: đo render + checkpoint khoảng 192–252 ms trên máy thử. Không suy rộng thành cam kết 200 video dung lượng lớn tải tức thì hoặc mượt trên mọi máy.
- `local_engine/check_library_api.py`: loopback, Origin/header, path traversal, mã hash, ZIP sai, CAS.
- `scripts/app-shell/check_portable_library.py`: SHA-256 vector 0/1/63/64/65 và trên 1 MiB; CRC/ZIP bằng Python; browser-only ZIP nhập được vào SQLite, giữ file/voice/timeline và pin; không gọi API trên demo.
- `scripts/app-shell/check_version_retention.py`: giữ chọn + hai mới nhất + ghim; lookup bảo vệ timeline giả lập rõ ràng; chỉ gỡ bản đã xác nhận, ghi IndexedDB thật.
- Home/archive, workflow navigation, shell alignment, Gói 6, setup-once, package5/local account guards vẫn qua. Không gọi AI/render trả phí trong kiểm tra.

Send2Trash và thao tác mở folder chưa thử trực tiếp trên Windows. Test dọn dùng mock để không đụng Thùng rác thật của máy chạy kiểm tra. Chưa thử mất điện phần cứng hoặc di chuyển ổ đang hỏng; kill process kiểm tra transaction không thay thế hai tình huống đó. Trường hợp thu-vien.db bị hỏng đến mức companion không khởi động cần phục hồi file từ bản SQLite/ZIP hợp lệ sau khi giữ bản lỗi; chưa có recovery launcher riêng.
