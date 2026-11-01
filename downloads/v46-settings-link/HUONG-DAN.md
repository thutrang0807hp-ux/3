# SceneForge v46.30 — thử ảnh + prompt

Đóng SceneForge, chạy SceneForge-Update-20261102-v46.30-Composer-Hotfix.exe và chọn thư mục đang cài có SceneForge.exe cùng install-settings.json. Yêu cầu bản vá v46.7 trở lên.

Mở lại app, vào node Veo, chọn ảnh và nhập prompt rồi bấm **Thử ảnh + prompt trên Flow**. Bản thử áp dụng settings, gửi ảnh, điền prompt ngay và thử gắn ảnh. Không bắt buộc preview, không tự gửi lại khi timeout, không tạo video.

Kết quả giao tệp, prompt và gắn ảnh được báo riêng. Tải báo cáo lượt ảnh + prompt nếu lỗi. Chưa xác minh toàn luồng trên Flow thật hoặc chạy installer trên Windows.

Bản .28 báo riêng prompt_filled (đã điền) và prompt_verified (đọc lại khớp). Kết quả gửi đầu vào dựa trên delivered + prompt_filled. Báo cáo chứa prompt_expected và prompt_actual để đối chiếu. Việc này không sửa lỗi gắn ảnh và không bật tạo video.

Bản .29 thử upload trực tiếp qua dấu + trong composer → Upload media → giao tệp → điền prompt. Không tìm lại ảnh trong thư viện. Composer cần chưa có ảnh; chưa tự thay ảnh cũ. Chưa kiểm chứng trên Flow thật, chưa tạo video.

Bản .30 sửa TypeError do keyboard.press nhận tham số timeout không hợp lệ, ở cả bước điều phối sau settings và bước đóng menu trong uploader composer. Chưa xác minh upload trên Flow thật.
