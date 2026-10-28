# Prompt và Chạy tự động · 28/10/2026

Gemini chịu trách nhiệm viết. Code chuẩn bị dữ liệu, gắn đúng file, kiểm định dạng và điều phối nguồn hiện có. Không cài model local, không thêm kho prompt hoặc màn chấm điểm. Đây là thay đổi cơ chế trong các node và thanh khung hiện có.

## Video mẫu

Một lần Chạy cho phép tiến tới điểm dừng đã chọn. Giữ phân tích đã chấp nhận; nếu thiếu, dùng pipeline cắt/đọc máy và nguồn phân tích trong Cài đặt, chỉ nhận kết quả đầy đủ, đúng phòng/nguồn/mốc và không có cảnh báo. Thiếu lời không được đoán: giữ quy tắc chép lời/không lời đã chọn trong node.

Ảnh khung: gửi bằng Gemini Chat ảnh bố cục nguồn cùng tham chiếu đích theo thứ tự R1…Rn. Tách dữ liệu hình học nguồn khỏi mô tả nhận dạng của vai được thay. Schema hai ngôn ngữ, danh sách mã ảnh đã dùng, cảnh báo. Code nối quy tắc chất lượng hiện có rồi gửi nguồn ảnh; file gốc được nhập lại và kiểm trước khi tiếp tục.

Video: Gemini Chat nhận **file khung đầu thực tế**, hoặc đuôi clip trước theo cấu hình nối khung, cùng tham chiếu đích và tối đa hai ảnh nguồn bổ sung. Mã E chỉ là bằng chứng phân tích, không đi vào prompt chạy. Viết chuyển động phù hợp trạng thái khung đầu, giữ ngữ cảnh cảnh liền trước/sau. Code bổ sung lời do dự án chọn, thời lượng, chế độ tiếng và quy tắc liên tục. Định dạng và mã ảnh được kiểm trước khi gửi Flow; model và account token phải khớp. Không tự dùng prompt mẫu thay cho kết quả còn thiếu.

Chỉ chọn khung/clip tự động khi đạt điều kiện kỹ thuật đang có, không có cảnh báo phải rà và không bị người dùng từ chối. Việc chọn này không chứng nhận mặt, nhãn hoặc hành động đúng bằng thị giác. Không chạy dọn phiên bản cũ, không tự mở Dựng hay xuất MP4. Xem bản ghép trước khi xuất.

## Từ ảnh & ý tưởng

Cùng nút Chạy và ba điểm dừng. Kịch bản giữ nguyên lời và ID cảnh. Dùng đúng chế độ Storyboard đã chọn: ảnh tổng, bỏ qua ảnh tổng, hoặc ảnh từng cảnh. Chế độ từng cảnh vẫn cần chọn cảnh; ảnh cuối chỉ tạo sau ảnh đầu và chỉ khi adapter/model công bố hỗ trợ. Không âm thầm đổi chế độ.

Tái dùng send/recovery đã có với quyền từ lần Chạy ban đầu, không click giả lên nút xác nhận. Ảnh dùng Gemini Chat hoặc Meta AI theo nguồn phòng; viết chỉ dẫn vẫn Gemini Chat, video Flow hoặc Muse theo nguồn phòng. Prompt viết nhận bảng R gắn đúng thứ tự file, ảnh đầu/cuối đã chọn, lời/mốc/phần clip và tóm tắt cảnh kề bên. Tạo clip và nhận vào bản ghép, giữ bước xem/chốt bản ghép cuối. Không gửi storyboard collage làm khung đầu.

Các đầu vào lưu để so prompt được rút gọn bằng mã ảnh/file và fingerprint, không lặp lại toàn bộ ảnh inline trong receipt viết prompt mới. File ảnh thật vẫn do kho hiện có quản lý.

## Thay đổi dữ liệu, lỗi và lưu trữ

- Video mẫu có fingerprint riêng cho prompt ảnh và từng phần video. Sửa lời chỉ làm cũ phần video liên quan. Lời thoại mới không khiến viết lại prompt ảnh. Đổi khung/model làm cũ prompt chuyển động.
- Ảnh tĩnh đánh dấu cảnh đổi lời/tham chiếu và chỉ viết lại cảnh cần cập nhật trong nhóm. Bộ dữ liệu viết còn kiểm storyboard, mốc và model. Thay đổi ngữ cảnh chung có thể làm cũ nhiều nhóm; không hứa mọi sửa đổi đều chỉ tác động một cảnh.
- Prompt sửa tay được giữ. Đầu vào thay đổi thì dừng ở ngoại lệ Giữ/Viết lại; kết quả AI đang chạy không ghi đè phần sửa tay. Sửa tay khi đang Chạy yêu cầu dừng gửi mới.
- Receipt được lưu trước POST. Lượt cũ đang chạy/chưa rõ chỉ được đọc lại, không tạo request ID mới. Lỗi định dạng có thể sửa kết quả đã nhận trong Các lượt đã gửi. Người dùng vẫn có thao tác bỏ lượt sau khi tự kiểm lịch sử; thao tác đó không hủy job dịch vụ.
- Không tự gửi lại khi failed/unknown, không tự retry bằng account/model khác. Dừng giữ các kết quả đã xong. Đổi phòng bị chặn trong lúc runner hoạt động. Nút Chạy hiện có thành Tạm dừng khi chạy.
- Lưu prompt hiện hành, fingerprint/template version, trạng thái run và receipt cần đối soát. Không thêm lịch sử prompt vô hạn, kho prompt, rating hay sao chép media để huấn luyện. Các phiên bản media và nhật ký dịch vụ có từ trước vẫn theo cơ chế cũ.

## Repo và phạm vi kiểm chứng

Đối chiếu thiết kế trong Wan2.2, CogVideo và ViMax; commit/license/file ở [prompt-repository-review.md](prompt-repository-review.md). Chỉ học cách tách nhiệm vụ, bind ảnh và chờ khung trước khi viết/chạy motion. Instruction và implementation là của SceneForge; không thêm dependency/model/runtime của các repo này, không dùng giới hạn Wan làm giới hạn Veo.

Kiểm thử Chromium trên app thật, IndexedDB/SQLite và file PNG/MP4 thật; transport tài khoản/model và kết quả kiểm chất lượng là fixture. Có kiểm gửi một lần đi hết scope, bấm lại không gửi trùng, sai mã ảnh/đầu vào cũ bị chặn, sửa JSON không gọi lại AI, giữ prompt thủ công, cả hai chế độ storyboard và các đường gửi thủ công cũ. Các test shell fallback cố ý tắt module mới để kiểm đường tương thích; test pipeline mới kiểm runner thật.

Chưa chạy bằng tài khoản Gemini/Flow/Meta/Muse thật. Kiểm máy chỉ xác nhận cấu trúc/điều kiện kỹ thuật, chưa chứng minh Gemini viết hay, claims đúng nghĩa hoặc mặt/sản phẩm đồng nhất. Schema chỉ phát hiện lỗi chắc chắn; cần chạy thật với sản phẩm của người dùng để đánh giá chất lượng. Không gắn cứng giá/giới hạn prompt chưa xác minh.
