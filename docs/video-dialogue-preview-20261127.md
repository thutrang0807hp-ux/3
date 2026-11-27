# SceneForge .188 — prompt video đầy đủ khi lời vắt mốc

Sửa thiếu sót .187: speechForPart.pending vẫn khiến bộ dựng prompt gốc ném lỗi trước khi trả cả phần hình/chuyển động. Ảnh đã duyệt đúng và prompt mặc định có khung, nhưng người dùng chỉ thấy ô trống và Chia lời cho clip 1a.

Bản xem trước luôn dựng đủ prompt: R1 ảnh duyệt và quy tắc nhận diện/bố cục; camera, initial/action/final từ cảnh; âm thanh/giọng và lời mới; cửa sổ lời, thời lượng theo phần clip; continuity; ràng buộc giữ nhãn/hình dạng, không khôi phục sản phẩm mẫu, không thêm chữ/nhạc ngoài kế hoạch. Không bê prompt chỉnh ảnh V6 sang video. Gemini vẫn là tùy chọn.

Khi câu vắt qua ranh giới clip, bản xem trước dùng nguyên lời mới liên quan và gắn DIALOGUE_REVIEW_REQUIRED; đây chưa phải lời được chọn để gửi. Không tự cắt từ theo tỉ lệ hoặc xóa phần còn lại. Giao diện hiện mục Lời thoại ngay trong cảnh, có các câu mới cùng mốc nguồn, ô nhập phần lời chính xác cho clip, Dùng lời này cho clip và lựa chọn rõ ràng Clip này không có lời. Chỉ cập nhật dialogueParts của clip, không sửa project.script hoặc các mốc. Prompt mặc định cập nhật sau lựa chọn. Prompt sửa tay không rỗng vẫn giữ; dữ liệu đổi cần rà binding trước khi gửi. Override rỗng cũ không che prompt mặc định.

Chặn ở các đường gửi (native Veo create, pair trial, hàng đợi, chuẩn bị video và legacy generate) nếu lời chưa được rà. Không coi việc hiện preview là cho phép gửi cả câu trùng qua nhiều clip. Sau khi chọn lời, một lượt Flow vẫn gửi đúng prompt hiện hành và một ảnh đã duyệt; không tự tạo video khi lưu lời và không gọi Gemini để chia lời.

Cách dùng: đóng app cập nhật .188, mở cảnh ở node Video. Ô Prompt chuyển động · đầy đủ luôn hiện; nếu có mục Lời thoại cho clip, chọn/nhập đúng phần lời và bấm Dùng lời này cho clip, hoặc chủ động chọn clip không lời. Rà prompt rồi tạo. Không cần ra node khác để xử lý phần lời này.

Kiểm thử Chromium/API giả lập đã qua: đủ visual/motion/audio/duration/camera khi lời vắt mốc; cả override rỗng lưu từ trước; prompt sửa tay giữ nguyên; gửi trực tiếp vẫn bị chặn khi lời chưa rà; chọn lời cập nhật prompt và mở nút tạo, gửi đúng image/prompt; lưu lời không gửi video; lựa chọn không lời không sửa kịch bản gốc; nút Gemini viết lại vẫn tùy chọn. Hồi quy node Veo: queue/receive/idempotence/legacy receipt/duyệt riêng đã qua. Cú pháp toàn workflow và nội dung nhúng gói đã kiểm. Chưa gọi Flow/Gemini thật hoặc chạy trình cài Windows. Backend và các thay đổi node ảnh/kho từ .187 được giữ. Cộng dồn .62 trở lên.
