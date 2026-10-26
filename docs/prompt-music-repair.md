# Sửa nhận prompt và nhạc — 26/10/2026

Phạm vi đã chốt: sửa JSON gây kẹt, bảo vệ nhịp/prompt không cần viết lại, đồng bộ bài nhạc. Giữ nguyên node, trình tự duyệt cả bản ghép và quy tắc dọn phiên bản. Không thêm model/repo.

## Nhận JSON

- Yêu cầu mới chỉ cần mã nhịp và các trường chỉ dẫn/prompt; app giữ nguyên lời, kiểu và số giây. Nhận theo mã, không phụ thuộc thứ tự các dòng trả về.
- Kết quả cũ có echo lời/số giây vẫn đọc được: dung sai số thực rất nhỏ, chuẩn NFC và khoảng trắng; thay lời thực sự, sai mã, sai phần hoặc thiếu prompt vẫn bị chặn. Không dùng lời/số giây AI trả về để ghi vào kịch bản.
- JSON sai được giữ nguyên trong `rawResult`, trạng thái `invalid`; vòng nhận tự động bỏ qua, không đọc/báo lỗi mãi mỗi 12 giây. Lượt chưa xử lý vẫn ngăn gửi trùng.
- Trong **Tiến độ → Chi tiết lượt gửi**, bấm **Xem / sửa JSON · không gọi AI**. Bản sửa được kiểm trước khi áp dụng, lưu riêng trong `correctedText`; không gửi thêm Gemini và không xóa bản gốc.
- Đầu vào đã thay đổi thì bản sửa cũng không được gán vào dự án mới. Mở lại app không tự phát sinh lượt gửi.

## Giữ chỉ dẫn và clip

- Nhóm tối đa 8 nhịp vẫn giữ; mỗi job mới ghi rõ những nhịp cần cập nhật và dấu chỉ dẫn lúc gửi.
- Khi nhận, chỉ cập nhật nhịp thực sự thay đầu vào; nhịp không đổi giữ nguyên prompt. Thay lời một nhịp không ghi đè chỉ dẫn của cả nhóm.
- Sửa tay từ bảng clip, Storyboard hoặc hộp sửa nhịp được bảo vệ. Sửa chỉ dẫn trong lúc chờ Gemini cũng được giữ; không dùng phản hồi cũ đè lên.
- Nhóm toàn chỉ dẫn cần giữ được ghi nhận cục bộ là **Giữ chỉ dẫn · không gọi AI**, không giả làm một lượt tạo của nhà cung cấp. Kết quả đã đủ thì bước chuẩn bị gửi 0 yêu cầu.
- Clip hiện có không bị xóa bởi bước viết prompt. Chỉ clip thật sự đổi prompt/ảnh/lời native/mốc mới cần xem lại theo quy tắc hiện có.
- Lượt từ bản trước vẫn đối chiếu đầu vào đã lưu, không bị bỏ chỉ vì mẫu yêu cầu JSON của phần mềm thay đổi.

## Một bài nhạc cho các lần dùng

- Hai luồng dùng chung cách chốt bài ngẫu nhiên, lưu khóa bài trong dự án.
- Nghe thử, mở bản ghép, chuyển sang Dựng và mở lại dự án dùng cùng bài đã chốt. Bản Ảnh lưu lựa chọn ngay khi chốt, kể cả khi chọn bài lần đầu từ bản xem thử.
- Chỉ khi người dùng đổi chế độ/bài thì bỏ lựa chọn ngẫu nhiên cũ. Đổi âm lượng hoặc render giao diện không bốc bài khác.
- Nếu file của bài đã chốt mất, dừng để chọn lại; không âm thầm thay bài.

## Kiểm chứng và giới hạn

`artifacts/prompt-music-fix-checks.json` ghi các bài Chromium/SQLite/file/editor và provider fixture. Bài mới kiểm sửa JSON thật qua UI, giữ prompt sửa tay + clip lưu thật ở nhịp bên cạnh, sửa khi job đang chạy, nhóm toàn chỉ dẫn tay và khôi phục bài nhạc sau reload. Bài Video mẫu kiểm nghe thử rồi handoff với giá trị ngẫu nhiên khác vẫn cùng bài.

Chưa kiểm tài khoản online thật hoặc Windows. Muse vẫn trỏ muse.ai, chưa phải Meta AI. Đợt này không thay cơ chế phiên/tài khoản, chất lượng Whisper/camera, chia câu, phụ đề theo tiếng thật hoặc chính sách xóa.
