# Bản sao lưu SceneForge — tiếp tục được ở chat/máy khác

Thời điểm: 27/10/2026 18:50:30 (Asia/Bangkok).

## Cách dùng
Giải nén toàn bộ. Đọc README.md về cách chạy động cơ local; frontend đã build ở dist/web-demo. Để sửa và dựng lại giao diện: python scripts/demo-web/build.py. Không cần dựng lại nếu chỉ muốn chạy bản frontend sẵn có.

Gói chứa code frontend/backend, trình cài phụ thuộc, các trang runtime đã build, tài liệu và log kiểm chứng. Chỉ bỏ các ảnh/bản thiết kế cũ trong thư mục design để giảm dung lượng. Không chứa tài khoản thật, cookie/key của người dùng, mô hình AI lớn hoặc dự án/video người dùng. Các thành phần ấy cần có riêng trên PC.

## Trạng thái đã hoàn thành
- Kho kịch bản v4: dán nguyên văn và lưu ngay, không bắt chia nhịp; Kịch bản và Công thức là hai loại riêng.
- Form dán ở cột phải; có bản nháp, sửa lời, gợi ý sản phẩm/chủ đề trên máy; Cài đặt Kho cho từ khóa.
- Chia nhịp trên máy hoặc Gemini theo nguồn đã chọn, chỉ gọi AI sau khi bấm và xác nhận. Kiểm đầy đủ đoạn nguồn bằng mã, giữ chữ/emoji, không tự fallback API trả tiền hoặc gửi lại lượt chưa rõ kết quả.
- Rút công thức thành bản riêng không có lời, liên kết về kịch bản gốc.
- Dùng cho video mới tạo snapshot riêng, mang lời và ghi chú cảnh sang phòng ảnh/ý tưởng; ghi chú cảnh được gửi vào storyboard/prompt, không đọc thành thoại. Mặc định tiếng clip (native). Sửa/xóa Kho không thay dự án đã dùng.
- Bộ nhập video chung cho Trang chủ, Video mẫu và Kho: file/link/video đã nhập. Nhánh Kho không tự gen ảnh/video.
- Các phần đã có trước: tài khoản/động cơ, hàng chờ/thông báo, lưu trữ/thùng rác chung, tạo hàng loạt; giới hạn ảnh đồng thời tùy chọn trên mỗi tài khoản.

## Tệp chính để tiếp tục code
- scripts/app-shell/recipe-v4.js và .css: giao diện và thao tác v4.
- scripts/shared/script-text.js và recipes.js: nguyên văn, nhịp, snapshot, phân biệt lời/chỉ dẫn.
- local_engine/script_library.py: API chia nhịp/gợi ý Gemini; server.py lắp route.
- scripts/photo-studio/providers.js, scripts/recovered/photos.js: nhận lời/chỉ dẫn vào luồng video.
- scripts/app-shell/video-intake.js, local_engine/video_import.py: nhập video chung.
- scripts/recovered/* và scripts/demo-web/rebuild_current.py: nguồn runtime và builder hiện tại. Các module mới được lắp qua patch_recipe_v4.py; không chỉ sửa trực tiếp dist rồi quên nguồn.
- docs/recipe-v4.md, docs/video-intake.md: hành vi và giới hạn.

## Kiểm chứng
Các log ở docs/checks/recipe-v4-*.log. Đã qua Chromium thật + local API/SQLite: lưu/mở lại ở profile mới, bản nháp, bộ lọc, nhịp giữ nguyên văn, công thức, thùng rác, snapshot độc lập và bàn giao phòng video. Đã kiểm prompt storyboard/video nhận được chỉ dẫn cảnh. Kiểm hồi quy storyboard → clip fixture → ghép → Dựng cũng đã qua.

Lệnh kiểm chính:
- node scripts/shared/check_script_text.cjs
- python -m local_engine.check_script_library
- python scripts/app-shell/check_recipe_v4.py
- python scripts/app-shell/check_recipe_workspace.py
- python scripts/app-shell/check_recipe_workspace_local.py

## Chưa được chứng minh
Chưa kiểm tài khoản Gemini/Flow/Muse online thật hoặc Windows trong đợt này. Phần AI dùng SDK/response fixtures khi kiểm; không coi đó là chứng nhận gen online. Tải link ngoài còn tùy nguồn, chưa xác minh đầy đủ thực tế. Không tự cài thêm model hoặc coi đề xuất cũ trong chat là thành phần đã cài.

## Yêu cầu gần nhất
Người dùng muốn một gói sao lưu tạm để tránh mất việc nếu chat đóng. Bản v4 đã triển khai; không có một hạng mục sửa mới nào khác được chốt sau đó.

File MANIFEST-SHA256.json ghi danh sách/kích thước/hash để kiểm toàn vẹn. Đây là snapshot cố định, không phụ thuộc lịch sử chat.


## Cập nhật node âm thanh và phụ đề
Đã triển khai Giọng đọc, Nhạc nền, Phụ đề cho cả Video mẫu và Từ ảnh & ý tưởng. Đọc docs/audio-nodes.md để biết thiết kế, cách chạy và giới hạn. Có kiểm tra Chromium và FFmpeg thật; TTS dùng fixture, chưa xác minh model VieNeu/Whisper thật hay Windows. Không tự gen ảnh/video khi thay âm thanh hoặc phụ đề.


## Cập nhật bốn node Video mẫu
Đã triển khai Phân tích, Các cảnh, Ảnh tham chiếu, Sang Dựng theo thiết kế v2. Đọc docs/reference-node-design.md. Có test giữ cảnh không đổi, ảnh đúng người, ghép thiếu cảnh đủ thời lượng, thay nguồn clip giữ chỉnh sửa timeline. Không tự gen hoặc xóa media. Ollama chỉ mô tả cảnh; nguồn Gemini phải khớp cấu hình hiện tại.


## Hậu kỳ tab Từ ảnh & ý tưởng
Đã đồng bộ node Giọng/Nhạc/Phụ đề và Sang Dựng. Có Ghép sẵn/Tự ghép, 3 công tắc bàn giao không đổi nguồn, ghép thiếu vẫn giữ thời lượng; bản mới thay đúng slot giữ timeline. Đọc docs/photo-post-design.md và kiểm trong docs/checks/photo-post-*.log.


## Ảnh khung và Video Veo gọn · 2026-10-28
Đã thay lưới và màn chi tiết hai cột cho hai node bên Video mẫu. Bên ảnh giữ nguyên luồng duyệt cả bản ghép. Đọc docs/reference-media-nodes.md và docs/checks/media-nodes-*.log. UI không giả model/giá/%/kết quả kiểm; runner hiện thiếu OpenCV nên nhánh báo thiếu đã được kiểm, không coi là đã đo nét/OCR thật. Các lần gửi dùng transport fixture; chưa gen online/Windows.

Đã thêm bảng nguồn dạng thẻ, lựa chọn nháp chỉ lưu bằng Xong, menu công cụ … riêng, và bản đồ chung kéo/resize theo node thật cho cả hai luồng. Đọc docs/workspace-source-cards.md; kiểm Chromium trong docs/checks/workspace-source-cards-check.log.
