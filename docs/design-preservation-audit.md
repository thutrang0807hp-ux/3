# Rà soát các gói SceneForge · 21/10/2026

## File gốc

Đã đọc lại các đặc tả Tạo video, Dựng, Khung sườn app và cả hai bản Gói 4. Đã đối chiếu từng file trong 5 ZIP với thư mục `design/`: **41 file Markdown/PNG còn nguyên và SHA-256 khớp từng byte**. Kết quả đầy đủ ở `design-archive-integrity.json`; chạy lại bằng `python scripts/app-shell/check_design_archives.py`.

Hai lần cập nhật giao diện Gói 4 trước chỉ sửa trang web, tài liệu triển khai và ZIP phần mềm; lịch sử xuất bản không ghi nhận xóa các tệp giao diện khác. Gói bàn giao cũ trong `downloads/SceneForge-BanGiao.zip` được giữ. Điều này không có nghĩa là mọi tính năng đã được triển khai đầy đủ: có tính năng bị khóa/che và có tính năng còn thiếu.

## So trực tiếp với ảnh trang chủ

Người dùng chỉ rõ bản trước vẫn sai logo và tỷ lệ. Lần này lấy phần app của ảnh 01 làm chuẩn: gốc khung ở (48,138), kích thước nội thất 2018×1258. Chụp trình duyệt cùng kích thước; kiểm tra mốc thanh trái 100px, cột sản phẩm 330px, nội dung x=480, thẻ khoảng 300px, nút Video mới 194×54px. Các mốc hình học được kiểm tra trong sai số 7px; đây không phải tuyên bố mọi pixel/màu/nội dung đều giống.

- Logo là SVG hình chữ nhật bo góc, không còn ký tự ◫. Icon lọc, Bảng/Danh sách, hàng chờ và lưu trữ đều dùng SVG để tránh glyph/font khác máy.
- Sửa chữ, khoảng cách, tỷ lệ bìa, xuống dòng bìa mẫu, cột cuộn riêng và thanh cuộn mảnh. Mẫu 7 video hiện đủ thẻ; khi bảng đông (như ví dụ 20 video) mới dùng dòng gọn.
- Thứ tự sản phẩm được giữ ổn định; mẫu không đổi thứ tự mỗi lần đọc IndexedDB theo UUID. Gói xem mẫu cũ chỉ được nâng hình minh họa/bố cục có nhận diện, không xóa dự án hay media người dùng đã thêm.
- Dữ liệu/quota/tiến độ thật chưa có không được bịa để khớp số ví dụ trong ảnh. Nhãn trạng thái mẫu được phân biệt bằng banner xem thử.

## Lỗi đã xác nhận và sửa

| Vấn đề | Sửa / kiểm chứng |
|---|---|
| Trong phòng video mẫu, “Từ ảnh & ý tưởng” bị vô hiệu hóa | Hai nút dùng chung ở đầu không gian Tạo video, đều bấm được. Lưu phòng trước khi chuyển, mở phòng riêng của cùng sản phẩm, nhớ phòng gần nhất cho từng cách. Không đổi mode hoặc đè dữ liệu phòng hiện tại. |
| Phòng ảnh cũ có storyboard/khung/clip bị mở bằng giao diện Bộ cảnh, khiến tài nguyên cũ không xuất hiện | Nhận diện dữ liệu cũ, mở lại giao diện theo cảnh. Có nút đổi giữa bản cũ và Bộ cảnh, giữ riêng cả hai dữ liệu. Không tự gắn clip cũ vào 8 loại cảnh khi chưa biết loại. Bài trình duyệt kiểm tra lời, ảnh đã duyệt, clip Blob và lựa chọn bản cũ qua nhiều lần đổi. |
| Màn chọn cách làm đôi lúc che toàn bộ canvas của phòng mới | Không hiện màn chọn độc lập khi app đã chọn một phòng. Kiểm tra bằng trình duyệt trống dữ liệu. |
| Khung canvas tính bằng nhiều giá trị top cố định, sai khi thêm/bớt hàng hoặc xuống dòng | App chia vùng bằng flex; canvas video mẫu đo chiều cao thực của các hàng bằng ResizeObserver. Không đè projectbar/hạn mức ở 1700, 1366 và 390px. |
| Luồng ảnh có vị trí và độ rộng node khác ảnh 06; director có thể lấn sang voice | Bố trí lại 2 hàng: ảnh/Bộ cảnh phía trên, công thức/kịch bản/giọng bên dưới, đạo diễn bên phải, Sang Dựng cuối. Node hàng dưới tự nhường độ cao cho hàng trên. Kiểm tra mọi cặp node không giao nhau. |
| Bản xếp cũ hoặc vị trí người dùng kéo làm khó so sánh ảnh thiết kế | Nút “Xếp như mẫu”, có hoàn tác. Không tự xóa vị trí đã kéo; chọn node vẫn tô màu. Thu phóng vừa khung theo kích thước thực của các node. |

## Những phần giữ lại

- Video mẫu: chia cảnh cục bộ, ảnh gốc/ảnh mới, tham chiếu 4 loại, prompt chi tiết, lời thoại trong Flow, voice-over tùy chọn, duyệt ảnh, các bản clip, báo lỗi đỏ, hạn mức chưa xác minh, xử lý watermark trong node, Sang Dựng, kéo node và minimap.
- Từ ảnh: Bộ cảnh 8 kiểu dùng chung theo sản phẩm, khung trước, nhập và giữ các bản clip, kịch bản theo nhịp, kho công thức, AI/file/không lời, phân tích khoảng lặng, ghép cục bộ/đổi phương án, báo thiếu cảnh và chuyển clip/giọng sang Dựng.
- Dựng: model timeline, media và bản xuất không bị viết lại trong đợt này. Kiểm tra thứ tự từ 1→2→3 thành 1→3→2 khít nhau, chuyển cảnh/kéo mép/hoàn tác, bảng âm thanh và tăng âm lượng thực trong file xuất. Thanh âm lượng mini đã được người dùng yêu cầu bỏ trước đây, nên không khôi phục nó chỉ để thỏa bài kiểm thử cũ.
- Khung app và Gói 4: sản phẩm, tham chiếu riêng từng phòng, thư mục đã ghi, bảng 4 cột, bộ lọc, hàng chờ 2 làn, kho công thức, cleanup có xem trước/xác nhận, trạng thái chưa rõ khi app đóng. Không tự dọn hay xóa dự án trong lần nâng cấp này.

## Còn thiếu / chưa được xác minh, không tính là hoàn thiện

- Flow/Muse chưa có adapter tạo clip và worker thực thi tự động. Vì thế kiểm tra tài khoản/credit/quota, tiến độ và hết lượt thực chưa hoàn thiện; bảng tài khoản cũng chưa đủ mọi cột/biểu đồ của ảnh 03.
- Phân tích tham khảo hiện dò hình tại máy và nhận dữ liệu có cấu trúc; chưa tự hoàn thành chép lời/dịch/viết prompt bằng AI xuyên suốt như đặc tả. API Gemini trong companion và kho công thức chưa được nghiệm thu bằng key thật.
- VieNeu có đường gọi nhưng chưa chạy mô hình thật để kiểm chứng giọng/tốc độ; chưa đủ phần đọc lại từng câu trong editor.
- Xuất trên web vẫn dùng MediaRecorder. Chưa đạt xuất FFmpeg nền, kiểm tra ổ đĩa, đổi tên file tạm nguyên tử, GPU→CPU fallback như toàn bộ mục 9 của đặc tả Dựng. Không được gọi bản xem thử là phần mềm đã hoàn thiện các mục này.
- Không đánh đồng “file còn nguyên”, “nút có mặt” hoặc “test giao diện qua” với dịch vụ thật đã vận hành đúng.

## Kiểm tra tái lập

- `check_design_archives.py`: tính toàn vẹn 41 file gốc.
- `check_desk_design.py`: logo/icon SVG, thứ tự sản phẩm, thẻ đủ ở 7 video/gọn khi đông, so mốc bố cục với ảnh gốc ở cùng kích thước. Kết quả tại `desk-design-landmarks.json`.
- `check_workflow_navigation.py`: chuyển hai hướng, giữ phòng riêng, layout không đè, header không che, mở lại cả hai không gian của dự án ảnh cũ mà giữ khung/clip/lời.
- `check_package4.py`, `check_recipes.py`, `check_showcase.py`, `check_cleanup.py`: các hợp đồng web, dữ liệu và bàn giao của Gói 4.
- `check_magnetic_reorder.py`, `check_transition_details.py`, `check_audio_preservation.py`: timeline, chuyển cảnh và âm thanh thật. Bài `check_audio_core.py` cũ còn đòi thanh mini mà người dùng đã bỏ; không dùng nó làm bằng chứng nút mini bị xóa trái yêu cầu.

Không gọi dịch vụ trả phí trong các bài này. Các phản hồi Gemini dùng trong kiểm thử là fixture được ghi rõ.
