# Bảng thử thật → công cụ kiểm tra trong app

Nguồn: SceneForge_BangThuThat.xlsx (25 mục A1–D7 (bản nhận lại; giữ kết quả 22 mục cũ)), giữ nguyên workbook gốc. File nhận lại trùng byte với workbook của gói tổng hợp, không triển khai trùng.

Mở **Cài đặt → Động cơ hoặc Thông báo → Kiểm tra theo bảng thử**. Bảng cho xem cách thử, tiêu chí đạt và phương án dự phòng của từng mục. Chỉ ghi Đạt/Không đạt sau khi nhập bằng chứng; kết quả này luôn mang nhãn **bạn tự ghi nhận**, không phải app chứng nhận.

- Kiểm tra máy thật: chỉ bản cục bộ. Tạo MP4 tổng hợp 1 giây H.264/AAC 180×320, đọc thông số bằng ffprobe rồi giải mã hết video bằng FFmpeg. Dọn tệp thử; lưu báo cáo mã hóa. SDK có mặt không đồng nghĩa provider đang chạy.
- Font: kiểm SHA-256, mẫu dấu trong cmap và nạp font thật bằng FontFace. Chỉ chứng nhận font nhúng mặc định; không đại diện mọi preset/font hệ điều hành.
- Thông báo: người dùng bấm thử, cấp quyền và thu nhỏ cửa sổ; sau 8 giây app thử Notification API + âm báo. App chỉ ghi API đã gọi, không tự kết luận người dùng đã nhìn/nghe. Tự ghi D4 sau quan sát thực tế.
- Tải JSON hoặc CSV UTF-8 BOM; CSV chống công thức từ ghi chú. Một số mẫu key/cookie/token được che trong ghi chú nhưng không nên nhập thông tin bí mật.
- Mọi tác vụ Gemini dùng chung một khóa tuần tự, tránh các nút khác nhau vô tình gọi song song. Không đoán RPM miễn phí. Giữ quy tắc retry cũ: chỉ retry 429 miễn phí đã xác nhận, không tự gửi lại khi mất kết nối/chưa biết kết quả.

## Đã kiểm tra ở bản này

`python -m local_engine.check_machine_checks`: MP4 mã hóa/đọc/giải mã thật, dọn tệp, báo cáo lưu mã hóa, thiếu công cụ, bảo vệ POST; Gemini tuần tự bằng transport giả.

`python scripts/app-shell/check_machine_checks.py`: Chromium thật, đủ 22 mục, bộ lọc, tải font thật, yêu cầu bằng chứng, che token, tải JSON/CSV và lưu sau reload. Bản demo không gọi API cục bộ.

Không dùng các phép thử trên để đánh Đạt A3 (flow2api thật), C2 (gwmr/clip Veo thật), D2 (Windows thật), quota/credit, môi trường thông báo Windows hay chất lượng giọng/nhãn/mặt. Cần tài khoản, clip và máy đích để thử. Không cài gwmr hay giả kết quả Flow/Muse trong thay đổi này.
