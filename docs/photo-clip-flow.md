# Từ ảnh & ý tưởng — cập nhật 26/10/2026

Luồng: Bộ ảnh sản phẩm hoặc ảnh riêng từ máy → kịch bản tự viết / bản sao từ Kho → **một storyboard tổng** → Gemini Chat viết prompt từng phần → Flow hoặc Muse tạo clip → rà/duyệt → giọng, phụ đề, nhạc → Dựng → xuất.

## Cách dùng

1. Mở phòng **Từ ảnh & ý tưởng**. Ảnh đầu vào là bản sao của Bộ ảnh sản phẩm; có thể thêm file máy, chọn lại Bộ ảnh hoặc sửa riêng. File gốc được giữ trong kho, preview dùng để hiển thị.
2. Sửa/dán lời hoặc lấy kịch bản trong Kho. **Storyboard tổng** tạo hoặc nhập một ảnh duy nhất; không bắt cắt panel hoặc tạo ảnh khung từng cảnh. Ảnh khung riêng vẫn có trong mục tùy chọn.
3. Bấm **Chia clip** trên thanh công cụ. Nhịp mới dài hơn 8 giây được chia tối thiểu/cân đối bằng cùng bộ chia của Video mẫu. Có mốc hành động tự nhập, tùy chọn nối khung cuối và đuôi tĩnh tối đa 1,2 giây ở nhịp không lời. Mốc câu bên này là ước lượng từ kịch bản, không phải Whisper đã nghe người nói.
4. **Viết prompt video** gửi ảnh gốc đã chọn và storyboard tổng cho Gemini Chat trong một lượt, kèm kế hoạch từng phần. Không dùng Gemini API trả phí làm đường dự phòng. Rà kết quả trước khi áp dụng; JSON có rào Markdown/lời dẫn có thể đọc nếu chỉ có một object rõ ràng. Kết quả thiếu/sai cấu trúc bị chặn, không tự gọi AI lại.
5. Chọn **Flow / Muse** trên thanh. **Tạo clip còn thiếu** chỉ chuẩn bị việc đủ điều kiện; xem prompt/lời/tài khoản rồi bấm gửi. Backend dùng chung lựa chọn tài khoản, token, journal, giới hạn đồng thời và kiểm dung lượng. Việc chưa rõ không được tự gửi lại. **Các lượt đã gửi** cho đối soát hoặc chủ động bỏ theo dõi sau khi kiểm lịch sử; bỏ lượt không hủy trên dịch vụ hoặc hoàn credit.
6. Node clip có **một ô mỗi phần prompt**, luôn hiện bản nhập/gen mới nhất. Click để xem, sửa lời/chuyển động riêng, nhập clip máy, dùng clip trong Bộ cảnh hoặc tạo lại đúng ô. Bản mới chưa tự được duyệt. **Duyệt tất cả clip đạt** giữ bản mới nhất đủ điều kiện và tự dọn bản cũ không còn dùng, không mở thêm bảng dọn. Số phiên bản không bị giới hạn 5/10/15.
7. Nối khung cuối là tùy chọn: trong một nhịp, phần sau chỉ được chuẩn bị khi phần trước mới nhất đã duyệt và có khung cuối. Chạy tuần tự trong chuỗi đó; các nhịp độc lập vẫn có thể song song. Sửa phần sau không làm mất duyệt phần trước; đổi phần trước khiến phần phụ thuộc cần rà/nối lại.
8. Ghép chỉ dùng các bản mới nhất đã duyệt, đúng nội dung/mốc/ảnh đầu vào và đủ thời lượng. Giọng VieNeu/file hoặc tiếng clip, phụ đề riêng và nhạc vẫn dùng các node hiện có. Bản dựng nhận từng clip đúng mốc; đuôi tĩnh được nhập thành ảnh giữ khung cuối. Chữ/nhạc sửa riêng không cần gen lại video. Khi dùng tiếng clip, phụ đề tự lấy lời đã sửa riêng từng phần; dùng giọng riêng thì giữ kịch bản giọng đó.

## Lưu trữ và tính tương thích

- Duyệt dùng chung `/library/lifecycle/approve`, biên nhận thao tác và khôi phục khi mất phản hồi. Mở rộng `version_approval.py` cho `scope: photo`, không thay quy tắc Video mẫu. Chỉ dọn phiên bản cũ trong ô được duyệt.
- Giữ file đang dùng trên timeline, Bộ cảnh/dự án khác, bản ghim và ảnh đang được clip đã chọn tham chiếu. Những file được bảo vệ có thể chưa giải phóng ngay. File gốc bên ngoài kho app không bị xóa.
- Dọn “không dùng” giữ bản mới nhất và các bản được chọn của **mọi phần**, không chỉ `chosenClip` kiểu cũ. Thu gọn/xóa dự án sau xuất dùng chính sách hiện có; không tự bật tự dọn.
- Nhịp có clip/lượt gửi cũ giữ cách chia cũ để không gán nhầm file. Nếu đã khóa cách chia rồi đổi thời lượng nhịp, chặn tạo/duyệt/ghép theo mốc cũ; tạo nhịp mới để đổi cách chia. Dùng lại mẫu mới không mang theo tác vụ/tài khoản đã gửi của phòng cũ.
- Không cài thêm model, không thay Whisper/VieNeu hoặc số luồng Gemini. Không có tự chạy generation sau khi mở lại app.

## Giới hạn phải giữ rõ

- Muse adapter hiện vẫn là **muse.ai**; chưa phải Meta AI/Muse mà người dùng từng yêu cầu. Không coi nút Muse là bằng chứng Meta AI đã chạy.
- Không chứng nhận Windows hoặc vòng tạo bằng tài khoản thật. Provider trong bài kiểm là transport fixture; media/SQLite/file/browser/editor là thật.
- Thời lượng dựng không đồng nghĩa thời lượng dịch vụ tính credit. Không tuyên bố model hỗ trợ 4/6 giây hay giảm phí vì viết prompt ngắn. Trần chia cơ sở hiện là 8 giây.
- Lời từng phần/mốc câu là ước lượng, cần nghe và sửa; không bảo đảm model nói đúng, giữ nhận diện hoặc nối hình hoàn hảo. Storyboard chỉ là chỉ dẫn, không được đưa cả grid vào video như ảnh cảnh.
- Chỉ thêm chỉ dẫn đầu ra sạch trong prompt; không hứa xóa được mọi watermark/logo hoặc coi logo đóng gói sản phẩm là thứ cần xóa.

Kiểm chứng đợt này ở `review/PHOTO_CLIP_FLOW_CHECKS.json` trong gói code review; các báo cáo cũ vẫn ghi đúng phạm vi/lần chạy cũ của chúng.
