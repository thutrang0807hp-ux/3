# SceneForge .187 — prompt video mặc định, Gemini tùy chọn

Nền .186 / 1c79be6. Sửa chuỗi lỗi đã tái hiện: makePrompt trả PROMPT CHƯA CHUẨN BỊ khi thiếu Gemini writer; draft bỏ chuỗi đó thành text rỗng; createReason chặn Rà prompt cho đúng ảnh hiện tại dù ảnh đã duyệt và tài khoản Flow sẵn sàng.

Prompt mặc định dựng tại máy từ khung video có sẵn: R1 là ảnh khung đã duyệt, làm chuẩn mọi diện mạo; chuyển động/camera/đầu/cuối từ scene.motion; lời newText hoặc dialogueParts của phần clip; giọng đọc và cửa sổ lời; thời lượng phần clip hoặc generationDuration nếu đã lập kế hoạch. Không lấy original/translation làm lời đọc. Không chép mô tả visual sản phẩm mẫu hay nguyên prompt sửa ảnh V6 vào prompt chuyển động. Dữ liệu motion nguồn chỉ mô tả hành động, không được thay diện mạo đang có trong R1. Nếu không có hành động, yêu cầu giữ tư thế, không tự bịa thao tác sản phẩm. Thời lượng thật của tệp vẫn do model/cấu hình Flow và bước dựng quyết định, không chứng nhận đúng chỉ bằng chữ trong prompt.

Không yêu cầu writer Gemini hoặc SDK Gemini để chuẩn bị video khi đã có dữ liệu cảnh/ảnh duyệt. Nhánh chuẩn bị video cục bộ và hàng đợi nhiều clip dùng prompt đó. Nút Gemini viết lại vẫn gọi writer khi người dùng chọn riêng; kết quả hợp lệ hiện hành được dùng theo luồng cũ. Bản ghi writer cũ được giữ lịch sử khi thay bằng recipe cục bộ; không tự hủy yêu cầu đã gửi.

Bản nháp rỗng cũ tự có nội dung mặc định. Bản mặc định sau khi gửi không bị đánh dấu nhầm thành sửa tay; đổi lời/motion sẽ cập nhật bản mặc định. Binding thêm lời, motion, giọng, extraRequest và thời lượng phần clip để bản sửa tay cũ phải rà khi dữ liệu thay đổi. Bản sửa tay không rỗng hoặc draft cũ không rõ nguồn được giữ, không tự ghi đè. Lời vượt ranh giới clip vẫn chặn và báo chia lời cụ thể, không dùng Gemini để che lỗi hoặc tự cắt lời.

Giữ node Ảnh khung .186, duyệt nhiều khung, template V6, browser/upstream sender, backend Flow, chống gửi trùng và đối soát lượt cũ. Chỉ sửa workflow và kiểm thử liên quan, không thay backend hoặc tài khoản.

Cách dùng: đóng app cập nhật .187, mở cảnh trong node Video. Ô prompt có sẵn nội dung nếu ảnh/lời/motion đủ. Kiểm tra rồi bấm Tạo 1 video trên Flow; không cần bấm Gemini viết lại. Nếu là bản sửa tay cũ hoặc ảnh/lời đổi, app vẫn yêu cầu rà đúng bản trước khi gửi.

Kiểm thử:
- Chromium workflow thật với API giả lập: duyệt đúng ảnh gốc, không có Gemini writer record và draft cũ text rỗng vẫn hiển thị prompt; đúng newText/motion/thời lượng cảnh; không lấy lời/visual mẫu. Chuẩn bị video không gọi Gemini. Một Flow POST chứa đúng prompt và một ảnh duyệt có byte khớp. Cập nhật mặc định khi sửa script; giữ sửa tay và chặn stale. Nút Gemini viết lại riêng phát một text request, không tự gửi Flow. Lời vượt clip bị chặn với lý do cụ thể.
- Hồi quy check_veo_redesign_ui.py: tiles/detail/chuyển cảnh/sửa prompt, nhận clip/idempotence, tiến độ, hàng đợi nhiều clip dùng 0 writer call, dừng khi kết quả chưa rõ, lịch sử/negative receipts và duyệt riêng. Fixture chuẩn bị project trước script node như các test hiện hành để tách race render khởi tạo sẵn có.
- Cú pháp toàn workflow và nội dung nhúng gói đã kiểm. Test Node cũ check_flow_config_create_ui.js không chạy được vì fixture thiếu SFVeoLifecycle; dùng kiểm thử Chromium ở trên làm bằng chứng đường gửi thật của UI.

Chưa gọi Flow/Gemini thật hoặc chạy trình cài Windows. Đây sửa điểm chặn trước gửi; không bảo đảm phía Flow luôn tạo video thành công hoặc không có lỗi khác sau đó. Cộng dồn từ .62 trở lên.
