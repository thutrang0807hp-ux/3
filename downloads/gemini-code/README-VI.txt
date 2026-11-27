# Mã gửi ảnh tham chiếu + prompt và nhận ảnh Gemini

Đây là mã nguồn để bên phát triển khác đối chiếu và tích hợp; không phải bộ cài.

## Mở các file này trước

1. `02-sceneforge-v46.179/scripts/browser-extension/frame-studio-tab.js`: bản gửi ảnh + prompt trong tab Gemini của SceneForge. Khối `request.references` tạo `File` từ base64 bằng `DataTransfer`, gán vào input và phát sự kiện `change`; sau đó chuyển sang gửi prompt. Payload ảnh có `mime_type` và `data` (base64 thuần). Các trường điều khiển gồm `operation`, `request_id`, `prompt`.
2. `02-sceneforge-v46.179/scripts/gemini-native/scene-send.js` và `gemini.mjs`: bản nối bước đính kèm SceneForge với bộ nhận ảnh của repo gốc ở v46.179. Đọc cả hai file để thấy cách gọi; không dùng riêng scene-send.js như một app độc lập.
3. `01-original-repo/runtime/gemini.mjs`: bộ gửi/nhận nguyên bản tại commit 75f43c9 của repo người dùng. Các hàm nhận và tải ảnh: `waitForImage`, `downloadFromGemini`, `downloadImage`, `copyImagePixels`, `saveResult`. Luồng: tải bằng nút Download → tải trong context đã đăng nhập → lấy pixel từ ảnh.
4. `01-original-repo/browser_bridge.py`: đăng nhập Chrome riêng, chạy Chrome nền và gọi Node qua JSON stdin. `create_image(prompt)` nhận bytes ảnh PNG; `write_prompt(prompt)` nhận văn bản.

## Ba thư mục không phải ba lớp cần ghép chồng

- `01-original-repo`: bản gốc không có ảnh tham chiếu của người dùng, được người dùng báo chạy được.
- `02-sceneforge-v46.179`: snapshot lịch sử của phần gửi/ghép SceneForge. Module Python còn phụ thuộc các module khác của SceneForge, không chạy độc lập bằng cách chép một file.
- `03-reference-attachments-v0.4.8`: bản sửa mới nhất, thêm upload theo Playwright/Chrome filechooser. `attachReferences(page, references)` nhận danh sách đường dẫn file theo thứ tự; bước gửi/nhận vẫn dùng hàm gốc. `create_image(prompt, references)` là đầu vào Python. Có các bài kiểm tra kèm theo.

## Điểm phải giữ khi ghép

- Ảnh gốc trước, các ảnh tham chiếu sau; prompt phải ghi đúng vai trò/thứ tự thực tế này.
- Upload đủ ảnh rồi mới gửi prompt; một lần gửi chứa cả prompt lẫn các ảnh đã đính kèm.
- Dùng cùng hồ sơ Chrome đã đăng nhập cho tải trang, gửi và lấy ảnh. Không tải URL ảnh bằng một HTTP client thiếu phiên đăng nhập.
- Chỉ đọc phản hồi mới của lượt vừa gửi; không tự gửi lại khi kết quả chưa rõ.
- Nếu dùng bản Playwright: cài Node và chạy `npm ci` trong thư mục runtime trước; Windows app còn cần Chrome và các gói Python trong requirements.txt.
- Cơ chế DOM/DataTransfer cũ và cơ chế Playwright/filechooser mới là hai phương án khác nhau; chọn một đường gửi thống nhất.

## Trạng thái xác minh

Mình chưa xác định chính xác commit khớp với lần người dùng từng gửi ảnh thành công. Snapshot v46.179 là mã lịch sử để đối chiếu, không phải bản được bảo đảm hoạt động hiện tại. Bản v0.4.8 đã qua kiểm tra với Chrome trên Windows và trang Gemini mô phỏng; chưa được xác nhận trên tài khoản Gemini thật. Không nên coi các bài kiểm tra mô phỏng là bằng chứng đã sửa mọi lỗi thực tế.

`MANIFEST.json` ghi repo, commit, đường dẫn gốc và SHA-256 cho từng file. Gói chỉ chứa mã nguồn và bài kiểm tra; không chứa tài khoản, cookie hoặc hồ sơ đăng nhập.
