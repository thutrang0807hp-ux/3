# Từ ảnh — sửa mốc, công thức, ảnh và giọng

Bản `photo-edit-safety-20261026` bổ sung một đường xử lý chỉnh sửa chung ở
`scripts/photo-studio/edit-safety.js`. Các handler ở app.js, storyboard.js,
production.js gọi đường này; không đổi luồng duyệt/xuất của Video mẫu.

## 1. Đổi thời lượng có thể tiếp tục làm

Sửa nhịp → Rà thay đổi → Áp dụng. Trước khi áp, hiện số clip giữ nguyên, clip
có thể tận dụng và phần cần clip phù hợp. Không gửi tác vụ AI từ thao tác sửa.
Kế hoạch chia được tính lại bằng planner chung, giữ giới hạn thời lượng từng
phần và phân phối lời theo cùng danh sách mốc.

- Clip tắt tiếng/giọng riêng, hình và ảnh tham khảo không đổi, tệp đủ dài:
  dùng lại tệp cũ với mốc dựng mới. Ví dụ 6 → 5,7 giây có thể cắt từ tệp hiện có.
- Clip có thoại: không tự coi việc cắt ngắn là an toàn. Nếu lời/mốc yêu cầu mới
  không khớp thì phần đó cần tạo/nhập clip phù hợp; các phần không đổi giữ nguyên.
- Nhịp dùng nối khung cuối được xử lý thận trọng, không tự tái gán một chuỗi
  phụ thuộc sang mốc khác.
- Kế hoạch cũ 6 giây nhưng trường seconds đã là 5,7 từ bản trước có thể sửa bằng
  cùng hộp Sửa nhịp; dùng thời lượng kế hoạch cũ làm căn cứ tìm tư liệu trước.
- Các mốc hành động nằm ngoài nhịp mới được bỏ khi tính lại; lời đã sửa riêng
  từng phần được giữ và phân phối lại, trừ khi chủ động thay lời cả nhịp.

Tận dụng tạo metadata `origin=local-reuse`, `reusedFrom`, `sourceRequestId`,
`sourceSignature`, lý do và signature của mốc dựng mới. Đây không phải receipt
AI mới. Tệp dùng cùng key, không sao chép media và không trừ credit.
Khung đuôi được đọc lại ở đúng điểm cắt. Các bản cũ vẫn giữ đến khi chốt cả bản.
Nếu file thiếu hoặc lưu thất bại, không áp nửa chừng; thử lại không nhân đôi
metadata tận dụng. Lượt video chưa rõ kết quả phải được nhận/đối soát trước.

Prompt hướng cảnh đã chuẩn bị được giữ khi người dùng chủ động sửa mốc. Lịch
chỉnh sửa thủ công được ghi riêng, tối đa 30 mục; không tuyên bố Gemini đã đọc
lại dữ liệu mới. Trường prompt của lượt gen cũ giữ nguồn gốc thực tế.

## 2. Đổi công thức giữ dự án đang làm

Chọn công thức từ nút hoặc Kho:

- Chưa có tư liệu/lượt xử lý: thay khung trong dự án hiện tại, xác nhận nếu đã
  viết lời.
- Đã có clip, khung, storyboard, giọng hoặc lượt xử lý: mở bảng Tạo dự án mới.
  Chép bộ ảnh/ý chính/lựa chọn nguồn, lấy nhịp của công thức mới; không mang
  clip, giọng, storyboard, job hoặc timeline cũ sang.

Bản gốc giữ nguyên. Chọn phương án kịch bản khác cũng qua quy tắc này khi đã có
công việc sản xuất. `photoBridge.forkDraft` ghi room mới với ID ổn định theo lần
xác nhận, nên mất phản hồi rồi bấm lại sẽ mở đúng bản đã tạo, không thêm bản nữa.
Không tự gọi AI khi tạo dự án theo công thức.

## 3. Ảnh và giọng ảnh hưởng đúng phần

Thêm/bỏ/chép lại ảnh so theo từng role. Chỉ các nhịp dùng role đã đổi mới bỏ
khung riêng đã duyệt; cảnh khác giữ khung, clip và tệp. Node ảnh báo cảnh vượt
8 ảnh để người dùng chọn bớt trước khi tạo.

Giọng riêng mới được nhập/tạo khi đã có kế hoạch hoặc clip sẽ giữ số giây cũ.
File → AI local dùng chung quy tắc tắt tiếng clip, giữ hình và bản phụ đề riêng
đã hợp lệ. Muốn canh lại: bấm Canh nhịp, qua bảng rà tác động ở mục 1. Phụ đề
sửa tay còn được giữ nhưng phải rà lại nếu lời/mốc thay đổi. Mốc TTS theo nhịp được lưu kèm mã/lời; canh lại ưu tiên mốc này khi vẫn khớp kịch bản. File nhập không có mốc TTS dùng ước lượng khoảng lặng/độ dài lời và ghi rõ cần rà.

Chuyển Tiếng clip → giọng riêng/Tắt tiếng tận dụng tệp hình, tắt audio cũ khi
dựng; metadata ghi rõ việc dùng lại. Giọng ngoài không tự khớp môi người đang
nói trong clip. Chuyển ngược sang Tiếng clip không được tự biến một clip im lặng
thành clip nói đúng lời; vẫn kiểm nội dung như trước.

## Kiểm chứng

`python -m local_engine.check_photo_edit_safety` chạy Chromium, SQLite/kho và
editor thật, không gửi provider job. Kiểm sửa 6 → 5,7 và 16 giây; số phần thiếu
khi mở bảng gửi; sửa mismatch cũ; thoại không bị tự cắt; unknown không bị mất
ràng buộc; thiếu file giữa chừng và thử lại; upload ảnh role không dùng/đang dùng;
WAV thật thay giọng vẫn giữ mốc; File/AI giữ phụ đề; canh lại chủ động; tắt tiếng
native không gen; fork mất phản hồi rồi thử lại + reload; chốt bản tận dụng vẫn
còn tệp và vào editor timeline 5,7 + 4 giây.

Các bài kiểm luồng storyboard, legacy clip, Unicode/planner, toolbar, duyệt/dọn
và mất ACK được chạy lại riêng. Xem PHOTO_EDIT_SAFETY_CHECKS.json để biết lần chạy.
Chưa kiểm Windows hay gen online với tài khoản thật. Không cài thêm model/repo.
Adapter Muse vẫn trỏ muse.ai, chưa xác minh Meta AI.
