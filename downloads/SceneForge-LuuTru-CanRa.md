# Những điểm còn cần đánh giá

- Thử Windows thật với file đang mở/antivirus; hiện mới có Linux và fixture lỗi/crash.
- Dọn hiện đợi tác vụ đang chạy kết thúc; chưa cho dọn song song tùy hash trong lúc gen.
- Chỉ dọn file đủ bằng chứng sở hữu/tham chiếu. Backend cũ không nhận diện được vẫn giữ, không đoán theo tuổi file.
- Không quản lý file người dùng đã tự chép ngoài app; published có lựa chọn riêng khi xóa dự án.
- Snapshot vẫn ghi toàn metadata, chưa delta; quét backup/hash còn I/O, chưa benchmark 10 video thật.
- Không hỗ trợ nhiều máy cùng ghi qua NAS/Drive; khóa OS chỉ cho một máy.
- ZIP không mang pending quarantine: phải chốt/lấy lại trước, hoặc chuyển nguyên thư viện. Policy toàn thư viện chỉ nhập vào kho mới chưa có dự án/lịch sử xóa.
- Restore thiếu shared/pin vẫn chặn; partial restore chỉ khi bỏ qua được các phòng hỏng mà không làm mất shared data.
- Giữ bản ghim, live refs, upload lease và job chưa nhập; xóa ngay không đảm bảo xóa mọi hash vừa mới upload.
- Cần rà root DATA temp/cache/logs riêng; không hứa dọn mọi byte trong toàn ổ.
- Xem TEST_RESULTS: các bài browser cũ timeout không được tính PASS. Không có thử tài khoản online.
