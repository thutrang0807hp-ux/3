# SceneForge v46.33 — thử ảnh + prompt

Đóng SceneForge, chạy SceneForge-Update-20261102-v46.33-Flow-Detail-Pane.exe và chọn thư mục đang cài có SceneForge.exe cùng install-settings.json. Yêu cầu bản vá v46.7 trở lên.

Mở lại app, vào node Veo, chọn ảnh và nhập prompt rồi bấm **Thử ảnh + prompt trên Flow**. Bản thử áp dụng settings, gửi ảnh, điền prompt ngay và thử gắn ảnh. Không bắt buộc preview, không tự gửi lại khi timeout, không tạo video.

Kết quả giao tệp, prompt và gắn ảnh được báo riêng. Tải báo cáo lượt ảnh + prompt nếu lỗi. Chưa xác minh toàn luồng trên Flow thật hoặc chạy installer trên Windows.

Bản .28 báo riêng prompt_filled (đã điền) và prompt_verified (đọc lại khớp). Kết quả gửi đầu vào dựa trên delivered + prompt_filled. Báo cáo chứa prompt_expected và prompt_actual để đối chiếu. Việc này không sửa lỗi gắn ảnh và không bật tạo video.

Bản .29 thử upload trực tiếp qua dấu + trong composer → Upload media → giao tệp → điền prompt. Không tìm lại ảnh trong thư viện. Composer cần chưa có ảnh; chưa tự thay ảnh cũ. Chưa kiểm chứng trên Flow thật, chưa tạo video.

Bản .30 sửa TypeError do keyboard.press nhận tham số timeout không hợp lệ, ở cả bước điều phối sau settings và bước đóng menu trong uploader composer. Chưa xác minh upload trên Flow thật.

Bản .31 thử bấm Thêm vào câu lệnh / Add to prompt nếu có duy nhất hộp tài nguyên một ảnh, rồi chờ chip composer tối đa 10 giây. Không báo đã gắn chỉ vì click thành công. Hộp nhiều ảnh sẽ không được tự chọn. Chưa xác minh trên Flow thật.

Bản .32 bỏ yêu cầu bắt buộc role=dialog. Vùng chi tiết được chấp nhận khi có một ảnh và là dialog, hoặc vùng fixed/absolute có nút đóng. Không chứa editor, không là body/html. Chỉ bấm nút có tên khớp nguyên văn trong duy nhất vùng hợp lệ. Có detail_regions trong báo cáo để chẩn đoán. Vẫn chờ chip, chưa bật tạo video và chưa xác minh trên Flow thật.

Bản .33 nhận diện flow-add-menu-detail-pane theo báo cáo Flow thật: relative, một ảnh, không role dialog hoặc nút đóng. Giữ giới hạn một vùng, một ảnh, tên nút khớp nguyên văn và chờ chip sau click. Chưa xác minh thao tác thành công trên Flow thật; chưa bật tạo video.
