# SceneForge .170 — UNIVERSAL REFERENCE IMAGE EDIT V5.1

Bản này thực hiện thay prompt tự động ảnh khung bằng đúng bản V5.1 người dùng cung cấp. Không nối V5.1 vào IMAGE EDIT CONTRACT V2 hoặc khung .169. Không đổi model, API, tài khoản, tiện ích, giao diện hay bộ đóng gói ảnh.

## Cài đặt và sử dụng

Đóng SceneForge → chạy cập nhật → chọn đúng thư mục đang dùng → mở lại một cảnh. Prompt tự động mới bắt đầu bằng `# UNIVERSAL REFERENCE IMAGE EDIT V5.1`.

Prompt V2/.169 do app tạo nhưng đã lưu vào ô sửa tay được lưu bản dự phòng và thay bằng mẫu mới khi chuẩn bị lượt mới. Prompt tự viết riêng vẫn giữ nguyên. Nếu cần chuyển bản tự sửa sang mặc định V5.1, dùng nút sẵn có Prompt → Dùng khung prompt sạch. Không thêm nút hoặc thay bố cục giao diện.

Không tự tạo lại ảnh hoặc gửi lại job. Lượt đã gửi và đang chờ giữ nguyên nội dung/chữ ký để nhận lại kết quả cũ; chỉ lượt mới chuyển mẫu. Ảnh và lịch sử cũ được giữ. Không cần cài lại tiện ích hoặc đăng nhập lại.

## Ánh xạ sáu biến

| Biến | Dữ liệu dùng |
| --- | --- |
| REFERENCE_BINDINGS | `SFPromptPipeline.imageBindings(scene)`, cùng thứ tự với `generationRefs`: R1 là khung gốc, R tiếp theo theo vai trò thực tế và ảnh đã chọn. Không mặc định sản phẩm luôn là R2. Vai trò sản phẩm chính, người, trang phục, bối cảnh và khung đồng nhất đều ghi rõ. |
| SCENE_DESCRIPTION | Bố cục/tư thế ban đầu có cấu trúc của R1 (`visual.composition`, `motion.initial`); yêu cầu chung theo phạm vi cảnh; `extraRequest`; `promptRevision.image`; mô tả vai trò không phải sản phẩm. Không lấy hướng dẫn sử dụng trong brief làm hành động. |
| PRODUCT_FACTS | Thông số định lượng từ `productScript.brief.facts` (mô tả sản phẩm tham chiếu là nguồn dự phòng), cộng số đo vật lý đã nhập trong Chỉnh chung. Không đưa tên dòng quảng cáo hay câu Mở nắp vào đây; khối lượng không tự thành số cm. |
| CONTINUITY_REFERENCE | Mã R của khung chuẩn đã duyệt cho các vai trò khớp từ `SFFrameIdentity`. Không có thì ghi rõ không đính kèm, không để token rỗng. |
| ASPECT_RATIO | `SFFrameSettings.output(scene).ratio` theo kích thước riêng / nhóm / mặc định video hiện có. |
| OUTPUT_RESOLUTION | Chiều rộng × cao từ cùng cấu hình đầu ra; mặc định 1080 × 1920. |

Dữ liệu thiếu được mô tả rõ là chưa có, không bịa. Kiểm tra trước dispatch chặn placeholder chưa điền như `[SCENE_DESCRIPTION]`, `[OUTPUT_RESOLUTION]`, `[MISSING_ROLE]`, `{{width}}` hoặc `${height}`. Tên khối keyword trong tiêu đề `## [TASK]`… vẫn được giữ vì là cấu trúc template. Nếu dán nguyên mẫu V5.1 chuẩn vào ô prompt, app nhận diện và điền các biến bằng dữ liệu cảnh; bản tùy chỉnh còn placeholder khác phải được sửa trước khi gửi.

## Các chức năng thay thế được giữ

Mẫu gốc lưu nguyên văn tại `scripts/prompts/universal_reference_image_edit_v5_1.md`. Các khối tĩnh được giữ đúng nội dung trong trường hợp thay sản phẩm thông thường. Runtime chỉ điền các slot và áp dụng các điều kiện vai trò cần thiết:

- Không chọn thay sản phẩm: các khối sản phẩm được ghi không áp dụng, không ép tạo một sản phẩm không có tham chiếu. Các keyword vẫn tồn tại.
- Chọn thay người: dùng mã R người thực tế. Cảnh chỉ có tay vẫn chỉ xử lý phần cơ thể đang thấy.
- Trang phục có ảnh riêng dùng ảnh đó; chế độ có sẵn lấy trang phục từ ảnh người ánh xạ cùng mã R người cho cả hai vai trò.
- Chọn thay bối cảnh: dùng ảnh/mô tả bối cảnh đã chọn, vẫn giữ góc máy R1. SCENE_LOCK bảo vệ phần không chọn thay.
- Yêu cầu đổi tay/người bằng mô tả được giữ trong SCENE_ACTION dù không có ảnh nhận diện riêng; các mục Giữ nguyên theo cảnh vẫn có ưu tiên.
- Khung đồng nhất chỉ hỗ trợ các vai trò khớp, không lấn ảnh sản phẩm/người gốc đã chọn.

AI tối ưu tùy chọn vẫn dùng API/schema hiện có, nhưng chỉ viết phần động SCENE_ACTION; các khối khóa V5.1 vẫn do template quản lý, không ghép thêm một prompt hoàn chỉnh khác. Không thêm lượt AI tối ưu bắt buộc.

## Bảo trì

- Mẫu nguồn: `scripts/prompts/universal_reference_image_edit_v5_1.md`.
- Ánh xạ/điều kiện và validation: `scripts/ui/frame_universal_v51.js`.
- Sau khi sửa mẫu nguồn, chạy `python scripts/sync_frame_universal_v51.py` để đồng bộ vào module và script slot HTML hiện tại.
- Kiểm tra: `node scripts/analysis/check_frame_universal_v51.js`, `python scripts/analysis/check_frame_studio_contract.py` và bài kiểm thử node/backend có Gemini mô phỏng.

## Xác minh

Đã kiểm tra mẫu nguồn khớp nội dung file người dùng; các khối tĩnh mặc định không bị viết lại; sáu slot được điền; thứ tự mã ảnh hỗn hợp người/trang phục/sản phẩm/bối cảnh; trường hợp chỉ đổi người hoặc trang phục; khung đồng nhất; thiếu dữ kiện; placeholder bị chặn trước tạo job; V2 được lưu dự phòng và thay thực sự; không có lớp V2/IDENTITY/FINAL SETTINGS nối kèm; ảnh gốc/tham chiếu và prompt V5.1 đi qua cùng backend/hàm gửi nguyên bản và trả ảnh về đúng cảnh.

Builder xác nhận mọi tệp runtime ngoài workflow.html giống .169; kiểm tra mã xác nhận file giao diện, backend, adapter và bộ đóng gói ảnh không đổi. Gemini và wire tiện ích trong bài kiểm thử được mô phỏng. Chưa xác minh chất lượng ảnh sản phẩm trên tài khoản Google thật hoặc chạy bộ cập nhật Windows trên máy bạn. Bản này chứng minh thay template/ánh xạ/luồng gửi đúng, không chứng minh ảnh đầu ra sẽ giống tuyệt đối.
