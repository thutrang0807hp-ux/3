# Gói 6 · triển khai trên app hiện tại

## Đối chiếu nhận mới

Giữ nguyên `SceneForge_Goi6.zip` và `SceneForge_TatCa.zip` trong `design/package-6-received/1` và `2`, có SHA-256 trong `package-6-integrity.json`. Gói 6 nằm trong bản tổng hợp trùng byte với gói gửi riêng. Năm ảnh và đặc tả được giải nén riêng, không thực thi nội dung từ tệp nhận.

Ảnh 04 là bố cục chính, ảnh 05 cho màn phóng to, ảnh 01–03 cho menu sản phẩm, Video mới và trạng thái phân tích. Các số/tên/tài khoản/credit trong ảnh không được nạp thành số thật. Bản tổng hợp chứa bản phân tích 9.234 byte và workbook 27 mục, cũ hơn bản 13.394 byte / 30 mục đã tích hợp trước đó: giữ bản mới, không làm mất D9–D11, bộ lọc lời, hợp đồng mã cảnh/câu hoặc kiểm ảnh gốc. So sánh tệp trong `package-6-comparison.json`.

## Tab Tạo video

- Hai nhóm Ảnh khung / Video Veo dùng lưới 6 cột. Có đếm đạt/cần xem/lỗi/đang tạo, lọc Tất cả/Lỗi/Cần xem/Chờ duyệt, viền đỏ và dải xem lỗi. Khung/clip thiếu dữ liệu không tự coi là đạt; không có tệp clip trong kho là cần xem. “Xem lỗi mẫu” vẫn hoạt động nhưng ghi rõ minh họa.
- Chỉ duyệt hàng loạt khung đạt kiểm tra, không nhận kèm khung lỗi/cần xem. Clip phải có đủ phần, tệp còn trong kho, được người dùng rà chấp nhận; nút nhận lưu bộ ID clip đã nhận, không ghi đè timeline đã chỉnh. Chuẩn bị lại nhóm lỗi hiện danh sách cảnh/giá tự nhập hoặc chưa xác minh, không gửi render.
- Mở lớn ngay trong tab: khung gốc cạnh bản mới, chọn phiên bản, kết quả kiểm ảnh, sửa prompt, nhập ảnh/clip, kiểm/rà và chuẩn bị tạo lại. ← → / Enter / R / Esc hoạt động, bỏ qua phím tắt khi đang gõ trong ô nhập. Chọn phiên bản ảnh được lưu; duyệt phiên bản khác bỏ lựa chọn clip cũ nhưng giữ mọi tệp/phiên bản. Clip tách phần a/b được chọn và rà riêng theo đúng phần; chọn bản mới không tự thay timeline. Mô hình ảnh Lite/Pro và clip Veo được chọn trong màn lớn.
- Bố cục mặc định lấy đủ node trên một màn hình, giữ kéo node, vị trí người dùng đã lưu, minimap và zoom. Danh sách chi tiết là tùy chọn giữ toàn bộ công cụ cũ. Bảng phân tích gọn năm bước máy + Gemini, có trạng thái theo tiến độ. Voice-over vẫn tùy chọn, không tách giọng bắt buộc khỏi Flow.
- Đang phân tích: xem video nguồn được, các nhóm phía sau mờ/khóa thao tác, không cho gửi phân tích thứ hai hoặc thay dữ liệu bên dưới.

## Nhận nhiều video và tiếp tục công việc

- Tạo từng phòng và lưu video trước khi phân tích, tên `<sản phẩm> · mẫu n` không trùng, bộ đếm giữ sau tải lại. Thả trong sản phẩm không hỏi; thả ở Tất cả chọn chung/từng file, thêm sản phẩm mới rồi quay lại bảng chọn. Gợi ý theo tên được ghi rõ là quy tắc tên; nút AI gợi ý riêng xin xác nhận gửi ảnh đầu/tên file, nhận mã F/P hợp lệ và vẫn chờ người chọn xác nhận.
- Tối đa hai phòng phân tích cùng lúc. CPU nặng được tuần tự hóa trong hai phòng để tránh tranh bộ nhớ và phù hợp giới hạn companion một job. Phòng chờ có thứ tự thật, có Để sau / Phân tích; gom lượt thả ở cột Đang chuẩn bị và có toast nhận tệp.
- Bước cắt cảnh trình duyệt chạy tự động. Khi có companion/thư viện phù hợp và trong giới hạn 18 MB/5 phút: tự chạy CPU/OCR/máy quay/độ nét, chép lời nếu model sẵn. Không tải model tự động. Thiếu thư viện/model/key hoặc quá giới hạn thì hiện cần bổ sung; không tô xanh giả.
- Lưu tiến độ/job ID/bước đã đo; tải lại đang chạy tiếp từ phần đã lưu, có thể tìm lại job CPU còn trên companion. Companion khởi động lại mất job thì chạy lại phần máy an toàn. Phần máy đã hoàn tất không chạy lại. Để sau chờ kết thúc bước hiện tại, không hủy dữ liệu đã xong.
- Mở phòng đang chạy hiển thị đúng iframe đang phân tích, không tạo bản thứ hai và không chuyển iframe sang DOM khác làm khởi động lại. Về trang chủ cho việc nền tiếp tục.
- **Gemini mặc định vẫn cần người dùng gửi.** Có checkbox đồng ý tự gửi ảnh/bản chữ theo lượt nhập; dùng hạn mức/điều khoản của key, không coi phân tích luôn miễn phí. Không gửi khi thiếu lời nguồn trừ khi đo được không có audio. Kết quả được lưu để rà trước áp dụng. Lượt submitted/unknown không tự gửi lại sau đóng app; OpenAI vẫn xác nhận riêng. Không tự gửi Flow/Veo hoặc tiêu credit.

## Sản phẩm, Kho kịch bản

- Menu ⋯: đổi tên, sáu màu, thêm ảnh, gộp, lưu trữ, xóa. Nháy đúp tên sửa ngay, Enter lưu/Esc hủy; tay nắm kéo đổi thứ tự và giữ sau tải lại. Badge vàng là số việc cần bạn, nếu không thì số phòng hiện hành, không cộng phòng trong thùng rác/sản phẩm đã lưu trữ.
- Gộp chuyển ngăn phòng, ghép bộ ảnh/bộ cảnh và giữ đường dẫn thư mục/bộ ảnh riêng. Không xóa dữ liệu gốc của sản phẩm được gộp, sản phẩm gốc được lưu trữ. Không gộp/xóa phòng đang phân tích.
- Hộp xóa đo số phòng, ảnh, clip bộ cảnh và tổng byte payload tệp đã lưu trong app (video, workflow, media timeline, bản xuất và ảnh gốc); không dùng số ví dụ hoặc ước tính dung lượng đĩa ngoài app. Mặc định chuyển video sang sản phẩm khác; tùy chọn đưa cả phòng vào thùng rác, có lưu trữ thay thế. Khôi phục giữ workflow/clip/timeline/export; tệp đã ghi ngoài đĩa không bị động tới.
- **Thùng rác hiện là trong app**, giữ khôi phục ít nhất 30 ngày, chưa chuyển vào Thùng rác hệ điều hành, chưa tự xóa quá hạn. Bản xuất trong app lẫn thư mục `7-xuat` luôn giữ; đây là khác biệt được nói rõ trong UI, không giả OS trash đã chạy.
- Mục Kịch bản cố định trên thanh trái mở kho toàn màn hình, tìm/xem/sửa/xóa, cùng store và bridge mà Từ ảnh đang dùng. Tự tạo khung sườn nhịp/thời gian từ mốc cảnh đã có, không lưu nguyên lời nguồn và không gọi thêm AI. Có công thức trong cùng phản hồi AI thì dùng lại; công thức đã chỉnh tay/xóa không tự ghi đè/tái tạo. Đánh giá video mẫu đã xuất được tính vào cùng kho như video từ ảnh.

## Đã kiểm tra

- `python -m local_engine.check_package6`: POST guard, chỉ ảnh/tên chứ không video, giới hạn 20 tệp, mã sản phẩm/video sai bị chặn, cần người xác nhận, không lộ secret. Transport provider giả, chưa xác nhận chất lượng gợi ý thật.
- `PYTHONPATH=/tmp/sceneforge-cpu-deps python scripts/app-shell/check_package6.py`: Chromium thực, lưới 13 cảnh/sáu cột, lỗi/cần xem không bị duyệt theo, bộ lọc, phóng to/phiên bản/phím/lưu, đổi tên/màu và cùng kho công thức; năm video thật, tối đa hai worker, tạm dừng/tiếp tục, mở phòng khi chạy không restart iframe, reload tiếp tục, CPU thật, không gửi cloud mặc định, năm công thức local, thùng rác/khôi phục giữ workflow và byte bản xuất. Điểm kiểm chất lượng trong fixture UI ghi rõ fixture, không thay kiểm ảnh thật.
- Hồi quy: backend aggregate/package5/analysis_v3/CPU, Chromium account dashboard/machine checks/local AI/analysis_v3; adapter video tương thích và xuất MP4+SRT qua FFmpeg thật. Các bài thao tác cũ dùng tùy chọn Danh sách chi tiết; bài Gói6 kiểm lưới mặc định.

`PYTHONPATH` trên là thư viện thử trong môi trường phát triển. Máy người dùng cài qua `install-cpu.bat` / requirements-cpu.txt. Chưa có model Whisper/key Gemini/OpenAI thật để chứng nhận chất lượng, chi phí hoặc quota; chưa chứng nhận Windows. Flow/Muse render/nâng ảnh/đọc credit vẫn chưa có adapter xác minh; các nút chuẩn bị không tuyên bố đã tạo ảnh/clip.
