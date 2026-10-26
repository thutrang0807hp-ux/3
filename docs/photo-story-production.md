# Từ ảnh & ý tưởng — storyboard tổng thành bản ghép

Bản cập nhật `photo-story-production-20261026` thay luồng duyệt từng clip của tab
Từ ảnh & ý tưởng. Không thay luồng duyệt ảnh/clip bên Video mẫu.

## Cách dùng

1. Thêm ảnh sản phẩm (thêm người/bối cảnh nếu muốn), dán hoặc lấy kịch bản từ Kho.
2. Dự án mới mặc định Tiếng clip. Có thể chọn Không lời, hoặc chuẩn bị giọng riêng trước khi chốt thời lượng.
3. **Tạo storyboard tổng** bằng Gemini Chat hoặc nhập một ảnh storyboard đã có.
4. **Chốt storyboard & chuẩn bị**: Gemini đọc ảnh tổng + ảnh gốc + kịch bản,
   viết prompt cho từng phần clip, tối đa 8 nhịp mỗi nhóm. Kết quả hợp lệ tự áp
   vào đúng cảnh, không bắt chép JSON hoặc duyệt từng dòng prompt.
5. **Tạo video**: xem số yêu cầu, nguồn và tài khoản trước khi bấm gửi. Không tự
   gửi tạo video sau bước chuẩn bị prompt. Hạn mức/credit theo dịch vụ thực tế.
6. **Bộ cảnh video** hiện clip mới nhất đúng nội dung trong từng cảnh storyboard.
   Nhận kết quả mỗi 12 giây khi app đang hiện và không mở hộp thoại. Cũng có nút
   Kiểm tra kết quả. Tạo lại đúng đoạn ngay trong ô, không có node Clip thứ hai.
7. **Xem bản ghép thử**: phát lần lượt theo timeline, giữ tiếng clip hoặc giọng
   riêng, nhạc và phụ đề theo tùy chọn. Phần chưa có clip được đánh dấu và vẫn
   chiếm đúng thời gian, không kéo lệch những cảnh sau. Đây là player xem thử,
   chưa phải MP4 đã render. Hiệu ứng/chữ hiển thị cuối cần rà ở Dựng.
8. **Giữ bản này & sang Dựng**: kiểm lại file, lời/phụ đề, giọng, nhạc, thời lượng,
   toàn bộ clip và đúng phiên bản vừa xem. Lúc này mới duyệt cả bản và dùng
   giao dịch dọn bản cũ đã có. Tư liệu dùng chung, ghim, hoặc đang ở timeline
   được bảo vệ. Sau đó chuyển timeline thật sang Dựng để chỉnh và xuất MP4.

Không giới hạn số lần gen lại thành 5/10/15. Các số đó chỉ là ví dụ/bài thử.
Bản gen trước còn giữ đến khi chốt bản ghép; kết quả cũ/lỗi thời đến muộn không
được thay clip hiện tại. Chốt bản ghép không đồng nghĩa đã xuất video.

## Vai trò node

- **Ảnh đầu vào**: bản sao riêng của dự án; giữ ảnh gốc để gửi AI.
- **Công thức / Kịch bản**: lấy khung, viết lời, đặt nhịp và lưu lại vào Kho.
- **Storyboard tổng**: một ảnh định hướng cả video; Gemini thật sự đọc ảnh đó
  lúc chuẩn bị prompt. Không cắt ô, không gửi lưới storyboard để model animate.
  Các trường chi tiết ở mục thu gọn, chỉ sửa nếu cần.
- **Bộ cảnh video**: các cảnh của dự án hiện tại theo storyboard, mỗi phần một
  clip; xem, sửa lời/chuyển động, tạo lại hoặc nhập clip đã có. Kho clip dùng
  chung của sản phẩm vẫn ở thư viện sản phẩm và có thể nhập vào từng ô.
- **Giọng / Phụ đề / Nhạc**: tùy chọn. Phụ đề là lớp ghép riêng; nhạc dùng file.
- **Bản ghép xem thử / Dựng & xuất**: xem cả video, chốt một lần rồi xuất thật.

## Nối dữ liệu và phục hồi

File cuối trong thứ tự JS: `story-production.js`; CSS: `story-production.css`.
Đọc build.py để xem thứ tự thực tế. Các override mới dùng tiếp clip planner,
provider adapter, account selection/token, checkpoint, request ledger, thư viện
SQLite và giao dịch approveVersions đang có; không tạo một backend giả mới.

`draft.production` lưu dấu storyboard/kịch bản, danh sách nhóm prompt, preview
manifest và dấu bản cuối. Mỗi job viết có source + danh sách beat/part. Chỉ áp
khi đủ mã/thứ tự/loại/thời lượng/lời/ảnh tham khảo và prompt tất cả phần clip.
Kết quả sai JSON/thiếu cảnh giữ lỗi để đối soát; không tự gửi lại. Đổi kịch bản
khi đang chờ thì giữ kết quả cũ riêng, không áp nhầm. Sửa lời/chuyển động riêng
trong một ô sau chuẩn bị là chỉnh sửa thủ công có chủ đích, không bắt viết lại
cả kịch bản. Clip có nội dung cũ không được dùng cho bản mới.

Prepared intent được save/checkpoint trước POST. Tắt app/reload chỉ đọc biên
nhận đã có; không dispatch lại. Lượt unknown/missing/invalid giữ khóa ô cho tới
khi đối soát. Không tự tạo clip tiếp hoặc tự gửi lại khi không rõ kết quả.

Các clip đủ điều kiện vào bản ghép thử dù chưa accepted. Giao dịch dọn chỉ chạy
khi người dùng bấm chốt bản ghép. Preview giữ snapshot cố định; đổi clip/cài đặt
sau khi mở thì phải xem lại. Giọng/phụ đề/file thiếu chặn trước khi dọn. ACK mất
khi dọn vẫn dùng cơ chế phục hồi kho hiện có.

Nối khung cuối là tùy chọn nâng cao, mặc định tắt. Nếu bật, cần giữ clip trước
để lấy đuôi nối tiếp; thao tác giữ này không dọn các phiên bản cũ. Các nhịp không
nối không phải chờ nhau duyệt từng ô.

## Đã kiểm và giới hạn

`python -m local_engine.check_photo_story_production`: Chromium + backend,
SQLite và editor thật, dịch vụ AI giả lập ở transport. 9 cảnh, nhóm prompt 8+1,
ảnh gốc + một storyboard đủ độ phân giải, không POST trước xác nhận; reload
không replay; tự áp prompt/nhận clip, tạo lại đúng ô giữ bản cũ; không cần duyệt
lẻ để phát bản ghép; ô thiếu không trượt timeline; phụ đề lỗi chặn preflight;
chốt dọn rồi nhập timeline 36 giây vào editor thật. Có kiểm chỉnh chuyển động
riêng, snapshot đổi sau mở, kết quả script cũ, timeout sau gửi không replay.
Các kiểm kho, ACK, clip/legacy, planner và toolbar được chạy lại riêng.

Chưa gen online bằng tài khoản thật hoặc kiểm trên Windows. Không bảo đảm AI
hiểu đúng mọi panel/chuyển động/nhận diện; vẫn cần xem cả bản ghép. Không cài
model nặng hoặc tự đổi sang API có phí. Gemini Chat cần phiên đã kết nối.
Muse video hiện dùng adapter muse.ai, chưa xác minh Meta AI. Muse tạo storyboard
vẫn nhập tay; đường tự chuẩn bị prompt theo nhóm dùng Gemini Chat. Chọn Muse
không có nghĩa đã có automation cho dịch vụ Meta. Không được coi các bài thử
transport là xác nhận gen online thành công.
