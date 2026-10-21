# Khung sườn SceneForge — 21/10/2026

Triển khai độc lập từ `design/app-shell-spec/DAC_TA_KHUNG_SUON_APP.md` và năm ảnh thiết kế. Không chép mã Concat/OpenMontage/FlowKit. Các con số trong ảnh không được dùng làm số liệu tài khoản.

## Chạy

```bash
python scripts/demo-web/build.py
python -m http.server 8766 --directory dist/web-demo
```

Mở `http://localhost:8766/`. Khung mới thay trang ngoài cũ; trình dựng và quy trình node giữ các công cụ đang có. `preview.html` vẫn là bản thiết kế cũ, không phải entry hiện tại.

## Đã làm và có dữ liệu thật

- Trang chủ: cột sản phẩm, bộ ảnh bốn loại, Tất cả/Lưu trữ; sáu cột chặng; tìm trong ngăn; thẻ bìa lấy từ video thật, dải trạng thái cảnh. Chờ duyệt/lỗi được nhấn vàng/đỏ. Cột cuộn riêng; chỉ thẻ đầu lớn, cột đã xuất hai thẻ lớn, Mới thêm có chồng thu gọn.
- Thêm nhiều video 9:16, tối đa 500 MB/10 phút mỗi video; mỗi video tạo một phòng. Khi ở Tất cả hỏi sản phẩm đúng một lần. Dữ liệu video lưu thành Blob trong IndexedDB, không tham chiếu tệp gốc ngoài máy. Bộ ảnh được sao chép khi tạo phòng; sửa bộ gốc không sửa các phòng đã có.
- Dò cảnh/trích ảnh tự chạy trên máy, tối đa hai phòng. Đây là bộ dò hình trình duyệt hiện có, **không phải Gemini/FFmpeg**, chưa chép lời hoặc viết prompt tự động. Trạng thái cột dựa vào dữ liệu đã lưu, không đếm tiến độ giả.
- Phòng hiển thị tên trên thanh chung, đổi qua dropdown. Tạo video và Dựng mở phòng gần nhất. Timeline, tư liệu, undo trong phiên và bản lưu tệp thật tách theo mã phòng. Khi đổi phòng đợi lưu xong; lúc xuất hoặc dò cảnh thủ công thì yêu cầu hoàn tất/dừng trước khi đổi để bảo toàn dữ liệu. Hai worker dò cảnh cục bộ ở phòng khác tiếp tục chạy.
- Đọc lại dự án workflow và bản dựng cũ trong trình duyệt, đưa vào ngăn mặc định; không xóa bản cũ. Các key lưu editor mới theo room ID; không dùng chung `current` cho tất cả phòng.
- Video từ ảnh có nút tạo phòng riêng, không trộn ảnh với nguồn video mẫu. Nút thay video nguồn ở phòng đã phân tích tạo phòng mới thay vì làm lệch ID của phòng đang mở.
- Hàng chờ chung mở từ rail hoặc phòng: lưu việc khung/clip, chặn clip chưa duyệt khung, chống thêm trùng, ưu tiên khung, đổi thứ tự, ưu tiên phòng, hủy, tạm dừng; lưu qua reload. Hiện rõ **chờ kết nối**, chưa gửi render. Nhập đủ clip đánh dấu việc clip tương ứng xong; lỗi không có cơ chế tự tiêu credit chạy lại.
- Credit còn lại luôn **Chưa xác minh**. Tổng cần dùng chỉ hiện con số khi mọi việc có giá do người dùng nhập, có nhãn rõ. Không kết luận đủ/thiếu hạn mức khi chưa đọc được số dư.
- Ô Sang Dựng: Ghép sẵn giữ tiếng Flow, các cảnh nối đúng mốc; tự ghép đưa clip/bản phụ vào Kho, có đặt sẵn giọng đọc mặc định bật và nhạc mặc định tắt. Tệp voice-over/nhạc nhập thật, đọc thời lượng thật; không tạo giọng AI.
- Bản clip mới nhập sau khi đã dựng tự thêm vào Kho, có nhãn bản mới và nút Thay vào timeline. Không tự thay timeline. Việc thay là thao tác rõ ràng có xác nhận/undo, giữ vị trí và thông số cảnh; clip mới ngắn hơn thì rút ngắn phần thay. Hiện thay một đoạn timeline phù hợp đầu tiên, chưa tự relink nhiều đoạn đã cắt từ cùng cảnh.
- Ghép sẵn khi phòng đã có nội dung dựng hỏi trước khi thay. Chuyển tự ghép không xóa timeline đang dùng.
- Xuất video thật bằng bộ ghi trình duyệt hiện có; sự kiện tải file mới đổi trạng thái đúng phòng sang Đã xuất và lưu bản Blob. Sửa tiếp mở đúng timeline. Dùng lại mẫu tạo phòng mới, giữ phân tích/cách chia/lời, chép bộ ảnh mới và bỏ khung, clip, phê duyệt cũ. Không tác động bản dựng gốc.
- Chuột phải thẻ: mở, đổi tên, thông tin thư mục, chuyển sản phẩm, lưu trữ, xóa. Đổi ngăn không âm thầm thay bộ ảnh riêng hoặc đổi thư mục vật lý của phòng. Xóa phòng xóa dữ liệu theo mã phòng trong trình duyệt, giữ các tệp đã sao chép ra máy.
- Thông báo thật từ thêm/xuất video, số chưa đọc; lỗi tại chỗ có sao chép. Nút thư mục mở quản lý lưu cục bộ, không giả làm màn tài khoản/đăng nhập chưa được thiết kế.

## Thư mục máy

Chrome/Edge có `showDirectoryPicker`: người dùng bấm chọn thư mục gốc một lần. Quyền do trình duyệt cấp. Ứng dụng tạo SceneForge/Dung-chung, sản phẩm/bo-anh, thư mục phòng và 1-video-mau đến 7-xuat. Chép video mẫu, các bản khung/clip, voice-over, bản xuất; `du-an.json` gồm workflow và timeline, tư liệu dựng chép kèm. Bản media bất biến đã có cùng kích thước không được ghi lại ở mỗi lần tự lưu. JSON dùng `createWritable()` và chỉ đóng khi ghi xong (cơ chế commit của File System Access API); không giả định có thao tác rename tạm của backend.

Nếu quyền đã hết sau khi mở lại trình duyệt, cần bấm Đồng bộ để cấp lại; không thể tự vượt hộp quyền. Trình duyệt không hỗ trợ picker vẫn dùng IndexedDB và tải JSON. JSON tải riêng không nhúng bytes video. Chưa có thao tác nhập phục hồi toàn bộ cây thư mục sang máy khác. Kho dùng chung của editor hiện vẫn trong IndexedDB; thư mục Dung-chung đã tạo nhưng chưa tự mirror toàn bộ kho đó.

## Những phần chưa kết nối

Flow tạo ảnh/video, đăng nhập Google, đọc credit, giới hạn/rate-limit Gemini, AI chép/dịch/viết prompt và TTS. Không dùng API trả phí trong đợt này, không kiểm tra giới hạn bằng cách gọi thử dịch vụ. Hàng chờ chỉ chuẩn bị và lưu thứ tự, chưa có worker Flow; chưa kiểm chứng thời gian nghỉ/xác minh tài khoản. Không hứa loại bỏ mọi watermark của Veo.

Xuất vẫn là MediaRecorder tối đa hai phút, MP4/WebM theo codec thực. Chưa có làn FFmpeg xuất MP4 nền, proxy hoặc chuyển phòng trong khi ghi. Màn chào/cài đặt tài khoản chưa thiết kế không được thêm nút giả.

## Kiểm tra

`python scripts/app-shell/check_app_shell.py`: thao tác thật trên Chromium với MP4 và ảnh/WAV thật: bộ ảnh và sao chép, hai phòng tự dò, duyệt khung, điều kiện hàng chờ/hủy/dừng/xong, ghép sẵn, cắt timeline rồi đổi phòng/reload giữ bytes và metadata, thêm bản mới không thay timeline, xuất và trạng thái phòng, tự ghép có voice-over, dùng lại mẫu, phòng từ ảnh tách biệt. Ghi cây thư mục được kiểm tra bằng FileSystemDirectoryHandle thật trong OPFS; chỉ thay picker bằng chọn OPFS trong headless. Hộp chọn thư mục hệ điều hành cần người dùng bấm trên Chrome/Edge thật.

Các bài native magnetic reorder, assembly links, node canvas interactions và timeline transitions/trim/pixel export vẫn được kiểm tra. Các bài navigation cũ dùng trang ngoài cũ/chooser làm entry đã lỗi thời; bài shell mới thay hợp đồng điều hướng đó. Không báo các bài đó là đã qua.
