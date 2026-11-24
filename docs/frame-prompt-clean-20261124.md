# SceneForge .169 — giữ key, làm sạch nội dung prompt ảnh

Đóng app → chạy cập nhật → mở lại cảnh. Bản này sửa bộ ghép prompt, không tự gửi lại ảnh hoặc xóa bản cũ. Không cần cài lại tiện ích hay đăng nhập lại.

## Cách dùng

Trong cảnh → tab Prompt → Dùng khung prompt sạch. Rà ảnh sản phẩm chính và yêu cầu, rồi chủ động tạo lại cảnh nếu muốn. Prompt tự động cũ được cập nhật khi chuẩn bị lượt mới; prompt bạn đã sửa tay được giữ nguyên và gửi nguyên văn. Khôi phục prompt trước giúp quay lại bản trước khi dùng khung sạch. Kích thước và ảnh tham chiếu vẫn theo các ô chọn hiện tại; khi sửa tay cần kiểm tra prompt phù hợp với lựa chọn đó.

## Giữ các key có vai trò rõ

- REFERENCE ROLES: số ảnh đính kèm đúng thứ tự.
- COMPOSITION: chỉ giữ góc máy/hành động/ánh sáng và phần không chọn thay của R1.
- PRODUCT LOCK: R2 (hoặc đúng mã ảnh sản phẩm) quyết định toàn bộ thiết kế, dáng, nắp, màu, vật liệu và nhãn; không lấy vỏ đồ nguồn.
- PERSON / OUTFIT LOCK, BACKGROUND: chỉ xuất hiện khi thực sự có lựa chọn tương ứng.
- PHYSICAL FACTS: chỉ số đo/khối lượng/dung tích trích theo cấu trúc, không nhặt cả câu có từ khóa.
- USER EDITS / KEEP: yêu cầu chung, riêng và các mục giữ nguyên theo ưu tiên đã chọn.
- OUTPUT: kích thước/tỉ lệ một lần.
- IMAGE QUALITY: độ rõ, chất liệu, ánh sáng/bóng tự nhiên; bỏ phụ đề quảng cáo nguồn, giữ chữ bao bì thật.

Mỗi key chỉ ghép một lần. Luồng tự động mới không thêm các khối IMAGE EDIT CONTRACT / FRAME IDENTITY / FINAL FRAME EDIT SETTINGS lên trên rồi nhắc lại nội dung. Không ép prompt phải ba dòng; mục tiêu là giữ key nhưng phần nội dung gọn và nhất quán. Với ví dụ đơn giản hai ảnh, prompt kiểm thử khoảng 900 ký tự thay vì khối hơn 6.600 byte cũ; yêu cầu riêng dài vẫn được giữ.

## Lỗi dữ kiện đã sửa

Đoạn NƯỚC HOA … 200G – CLOUD MOUNTAIN SERIES No.5 / Trọng lượng lớn 200g… / Khối lượng tịnh: 200g / Mở nắp sản phẩm. giờ chỉ trích Net weight: 200g. Tiêu đề có 200G và câu hướng dẫn mở nắp không thành chỉ dẫn tạo ảnh. Số đo như cao 9 cm/đường kính 7 cm chỉ xuất hiện nếu thật sự được nhập, không suy ra từ 200g. Hướng dẫn mở nắp do chính bạn nhập trong Yêu cầu riêng vẫn là yêu cầu chủ động và được giữ.

## Kiểm tra

Đã kiểm tra bộ lọc với đúng đoạn gây lỗi; thứ tự R1/R2; không trộn ảnh chính; prompt thực sự đi tới hàm gửi với các key duy nhất, không còn khối lặp/câu mở nắp/tên dòng quảng cáo; prompt sửa tay gửi nguyên văn; dùng khung sạch và khôi phục prompt kể cả bản đang gõ; kích thước/người/bối cảnh/yêu cầu chung theo cảnh và nhận ảnh tiếp tục chạy. Gemini và kết nối tiện ích trong kiểm thử là mô phỏng. Không tuyên bố chất lượng sản phẩm trên tài khoản Google thật đã được xác minh hoặc ảnh sẽ giống tuyệt đối.

Lượt cũ đang chờ được giữ nguyên prompt/chữ ký; chỉ lượt mới chuyển sang khung sạch. Giao diện xem ảnh lớn, tài khoản, backend và tiện ích giữ như .168. Gói gộp từ .62 trở lên.

Implementation: framePromptVersion169 opts only newly prepared scenes into a single keyed composer. The old composition function remains exclusively for legacy/pending signature compatibility; its generated strings are not layered onto new requests. The scalar whitelist returns normalized field/value pairs, not whole lines. Scene-specific and shared instructions are resolved by role and explicit precedence. Manual text and explicitly AI-optimized results bypass generic wrappers; reset archives the current draft and restores the local recipe without a text-generation call. Actual attachment packing is unchanged. The cumulative builder pins every non-workflow runtime file to .168.
