# Ảnh khung cho video HD TikTok

Theo yêu cầu: thêm chỉ dẫn chất lượng trong prompt, không cài hoặc chạy upscale local. Không bắt buộc 2K/4K/8K. Khuyến nghị video dọc 1080×1920; kiểm ảnh cho phép từ HD 720×1280 khi đạt các điều kiện độ nét/nhãn đang có. Kích thước và độ nét vẫn là hai tiêu chí riêng, không chứng nhận chất lượng video đầu ra hoặc độ nén sau khi nền tảng xử lý.

`scripts/shared/image-quality.js` là đoạn chỉ dẫn Việt/Anh dùng chung: giữ bố cục, độ sâu trường ảnh, ánh sáng, người và sản phẩm tham chiếu; nét tự nhiên, ít nhiễu/lỗi nén, không làm da nhựa hay đoán chữ nhãn. Không hứa phục hồi chi tiết hoặc xuất đúng độ phân giải chỉ bằng prompt. Đoạn được kèm lúc chép/chuẩn bị prompt, không sửa prompt gốc người dùng đã lưu.

- Workflow → Prompt khung → Chép prompt: chép đúng prompt ảnh, kèm tham chiếu, nhãn được chỉ định và yêu cầu HD. Trước đây nút chung này luôn chép prompt video dù đang xem tab ảnh; đã sửa theo tab đang mở.
- Kiểm ảnh → Chuẩn bị khung: cả hai bản prompt được kèm chỉ dẫn, bỏ câu yêu cầu tối thiểu 2K. Nút “Nâng 2K · chuẩn bị” đổi thành “Prompt ảnh rõ hơn · chuẩn bị”; không có engine upscale chạy phía sau.
- Từ ảnh → Bộ cảnh → có khung trước: việc ảnh có cùng đoạn chất lượng và version; việc video giữ prompt riêng. Không tự gửi yêu cầu hoặc tính credit.
- Phần kiểm ảnh cục bộ: báo cáo v2 dùng trạng thái hd/full_hd/below_hd; ngưỡng kích thước tối thiểu là cạnh ngắn 720 và cạnh dài 1280, Full HD là 1080/1920. Giữ kiểm độ nét/nhãn và file SHA gốc. Báo cáo cũ không bị sửa âm thầm; đo lại để nhận tiêu chí mới.

Kiểm tra: 720×1280 và 1080×1920 nét được chấp nhận, ảnh 360×640 vẫn báo thấp; helper không lặp đoạn; copy/prepare giữ raw prompt, frame/clip đã chọn; hàng chờ Từ ảnh chỉ thêm chỉ dẫn cho việc ảnh; không API trong demo. Hồi quy lời Flow vẫn giữ lời Việt và chia câu theo từng clip. `local_engine.check_analysis_v3` kiểm đo ảnh/chuyển động/nhãn và adapter đã có, provider chỉ mocked. Chưa chạy tạo ảnh thật hoặc đo đầu ra đăng TikTok bằng tài khoản người dùng.
