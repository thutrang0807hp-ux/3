# Gói tổng hợp — đối chiếu và phần bổ sung

## Đọc gói nhận được

`SceneForge_TatCa.zip` chứa 5 ZIP đặc tả, hướng dẫn ưu tiên và bảng 22 phép thử thật. Đã đối chiếu cả 7 tệp bên ngoài và 38 tệp bên trong: 35 tệp giống hệt những gì đã nhận trước; hai tài liệu Gói 1 có bổ sung và có thêm bảng thử. Toàn bộ ảnh thiết kế trùng bản đã có. Không thay lại trang chủ/node theo một hình cũ, không xóa đặc tả hay dự án trước.

Đối chiếu byte: `aggregate-archive-integrity.json`. Bảng ghi chú riêng: `SceneForge_BangThuThat_DoiChieu.xlsx`; bản Excel người dùng gửi không sửa. Các mục đòi clip/tài khoản Flow/Muse thật và máy Windows vẫn ghi **Chưa thử**, không lấy kiểm tra giả lập thay cho kết quả đó. Sheet riêng “Kiểm tra app cục bộ” ghi bằng chứng các chức năng đã chạy.

## Đã bổ sung hoặc sửa

### Phân tích Gemini nối vào node hiện tại

- Dò/chia mốc cục bộ và nhập AI/SRT cũ giữ nguyên. Nút “AI Gemini · đọc cảnh & lời” mở giải thích trước; chỉ khi người dùng bấm Phân tích mới gửi video tới Google qua key mã hóa trong companion.
- Video MP4/MOV/WebM tối đa 18 MB, 1–200 cảnh, tối đa 60 phút. Không tự tải lên trong nền khi mở video hoặc bản demo.
- Gemini nhận video và âm thanh, trả mô tả từng cảnh, Visual/Motion Việt–Anh, prompt khung và lời gốc/dịch/lời Việt có mốc giây. Backend kiểm tra số cảnh/mốc/kiểu dữ liệu; dữ liệu lệch hoặc thiếu bị từ chối, không ghi đè bản cũ. Chỉ một yêu cầu phân tích video được thực thi tại một thời điểm.
- Kết quả nhận được lưu vào dự án trước khi xem trước. Đóng hoặc tải lại trang có thể mở kết quả đã nhận, không gửi thêm lượt. Cần bấm Áp dụng riêng; được khôi phục prompt/lời/lựa chọn trước AI. Clip và timeline cũ vẫn giữ.
- Không cho đổi phòng giữa lượt đang chờ. Lượt không rõ kết quả không tự gửi lại. Nếu có công thức hợp lệ kèm cùng phản hồi, lưu Kho kịch bản từ dữ liệu đó; nếu thiếu, không tự gửi thêm một yêu cầu AI để rút công thức.
- Key, video base64 và lời nguồn không đưa vào nhật ký yêu cầu. Chi phí thực chưa được nhà cung cấp xác minh thì không đổi ra tiền. Chất lượng nghe/nhìn/viết prompt và quota với key thật **chưa kiểm chứng**; bài kiểm tra dùng phản hồi Gemini giả lập.

### MP4 thật qua FFmpeg trên máy

- Bộ ghi trình duyệt vẫn dựng hình, hiệu ứng, phụ đề và trộn tiếng như trước. Nếu companion có FFmpeg/ffprobe, hộp Xuất có lựa chọn hoàn tất thành MP4 H.264/AAC/yuv420p/faststart bằng FFmpeg.
- Có tiến độ, hủy, hai lượt tối đa trong hàng đợi và một tiến trình mã hóa thực thi. Giữ bản ghi trình duyệt trong bộ nhớ để tải dự phòng nếu FFmpeg lỗi; không giả là đã xuất MP4 khi động cơ lỗi.
- Tùy chọn cân âm lượng dùng FFmpeg loudnorm, mục tiêu -16 LUFS, true peak -1,5 dB. Nguồn không có âm thanh vẫn xuất được. Chỉnh gain thủ công trên timeline vẫn giữ nguyên.
- Giới hạn hiện tại: bản dựng ≤2 phút, bản ghi ≤100 MB, tối đa khoảng 8,4 triệu điểm ảnh. Kiểm tra chỗ trống ổ chứa companion trước khi nhận. Chỉ nhận tệp MP4/WebM do trình duyệt gửi; không nhận đường dẫn/URL hay lệnh shell.
- Tệp MP4 và SRT được tải và lưu theo phòng. Sửa lỗi so sánh mã phòng với cả đối tượng phòng khiến SRT trước đây tải được nhưng chưa được lưu vào kho phòng. Khi đã chọn thư mục, bản sao SRT đi cùng `7-xuat/`.
- Đây là bước mã hóa/hoàn tất FFmpeg sau trình duyệt, **chưa là bộ dựng timeline nền thuần FFmpeg**. Chưa bỏ giới hạn 2 phút hay yêu cầu giữ tab phía trước khi ghi. Bản web công khai không có companion vẫn dùng định dạng trình duyệt, không hiện nút MP4 cục bộ giả.

### Timeline và chữ

- Đo bằng cùng thao tác kéo qua hai track với 3/30/100 clip. Phát hiện preview tạo decoder cho cả clip chưa đến lượt và đặt transform cho những clip không đổi.
- Preview chỉ tạo nguồn đang hiển thị/chuẩn bị tới, dọn decoder xa vị trí phát; export vẫn kiểm tra đủ nguồn. Trong lúc kéo, clip không đổi không bị gán transform 0 dư thừa. Giữ nguyên quy tắc chèn từ tính, tạo hàng, nguồn/mediaIn, tiếng và hoàn tác.
- Fixture 100 clip trên Linux/Chromium headless: p95 khoảng cách khung hình từ 83,3 ms xuống 16,8 ms. Vẫn có đợt dừng tới 150 ms trong lần đo sau, nên chưa khẳng định hết khựng. Kết quả chưa đại diện Windows/video nặng; xem hai tệp `timeline-measurements*.json`.
- Nhúng DejaVu Sans, giữ giấy phép; các mẫu phụ đề dùng font có đủ dấu “Ữ ặ ỡ ợ ẫ”. Không đổi phông của dự án cũ. Đã nạp font thật trong trình duyệt và xuất chữ trong bài thử; chưa chứng nhận mọi font thay thế trên Windows.
- Sửa màn chào lần đầu tự mở đè lên menu/form khi người dùng đã thao tác.

## Chưa thể gọi là hoàn tất

- Flow/Muse tự render, đọc credit/quota, xác minh phiên và engine installer Windows; những chỗ này vẫn dùng nhập clip thủ công và trạng thái chưa xác minh.
- Kiểm tra mặt/nhãn, khớp miệng, giá credit/nâng 1080p, số việc trước xác minh, giới hạn tài khoản thật.
- VieNeu model/giọng thật/tốc độ trên máy đích; gwmr với clip Flow 720/1080p và nhiều kiểu logo; thông báo Windows khi thu nhỏ.
- Dựng timeline nền trực tiếp FFmpeg, xuất trên 2 phút, duck nhạc tự động, chuyển ổ có kiểm chứng. Các phần chưa có không được núp dưới nút thành công giả.

## Bằng chứng kiểm tra

- `python -m local_engine.check_aggregate`: FFmpeg thật, kiểm tra codec/âm thanh/kích thước/thời lượng/hủy/định dạng/origin và hợp đồng JSON Gemini. Google giả lập.
- `python scripts/app-shell/check_aggregate.py`: trình duyệt thật → companion → Gemini giả lập → xem lại sau reload/áp dụng/khôi phục → nhập clip → FFmpeg thật → MP4 + SRT; cả hai lưu đúng phòng. Không gửi lặp để mở lại kết quả hoặc tự rút công thức.
- `python scripts/native-preview/measure_timeline.py`: đo thao tác kéo và kiểm tra font, xuất JSON số liệu.
- Hồi quy: node/setting/thông báo Gói 5, Kho kịch bản, dọn dữ liệu, điều hướng hai workflow, trang chủ theo ảnh, chèn từ tính/chuyển cảnh, gain âm thanh xuất thật. Những kiểm tra cần provider thật không thay bằng số ví dụ.

## Bổ sung bảng thử thật

Thêm Cài đặt → Động cơ/Thông báo → Kiểm tra theo bảng thử: 22 tiêu chí gốc, kết quả tự ghi nhận riêng với số đo MP4/font/thông báo. Xem [chi tiết và giới hạn](testing-implementation.md). Gemini được xếp tuần tự trên toàn bộ công cụ. Không chứng nhận các mục dịch vụ/Windows chưa chạy thật.

## Gói tổng hợp nhận lại

Có thêm CPU trong node Phân tích, 25 phép thử và ảnh Cài đặt thứ ba. Xem [phần đã nối / chưa thử](aggregate-2-implementation.md). Bản gốc của cả hai gói vẫn giữ riêng; không xóa các engine/luồng hoặc thay thiết kế trang chủ.
