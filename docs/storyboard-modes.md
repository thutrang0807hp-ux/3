# Storyboard: ảnh tổng / ảnh đầu vào từng cảnh · 28/10/2026

Một node, hai tab giữ dữ liệu riêng khi chuyển. Ảnh tổng là một file gồm nhiều ô, dùng lập kế hoạch, không cắt ô để đưa vào video. Ảnh tổng có mô tả sửa được, các bản và xem ảnh gốc lớn; xem/chọn bản trong node không đổi nguồn đang dùng cho đến nút Dùng làm tham khảo. Có thể bỏ qua ảnh tổng để viết prompt từ ảnh nhận diện + kịch bản. Dữ liệu và prompt cũ không có keyframe được giữ nguyên signature để tránh gửi lại khi nâng cấp.

Ảnh từng cảnh gắn theo beatId + part: cảnh dài chia clip a/b có ảnh đầu/cuối riêng cho từng phần. Chọn cảnh, chỉ ảnh đầu hoặc đầu+cuối. Lưới tối đa hai hàng/6 phần rồi Xem tất cả; bấm ảnh mở inspector ảnh trái, prompt phải, phiên bản, nhập file, tạo lại đúng ảnh. Dùng tham chiếu nguồn; tạo cuối nhận thêm ảnh đầu đã xong nên cần lượt sau, không tự gửi lượt tiếp. Trước mỗi gửi có preflight số lượng, ảnh tham chiếu, prompt, token tài khoản và input signature. Đổi nguồn không tự thay adapter.

Job ảnh là Gemini Chat image job thật với productionRole=storyboard-keyframe, scene/part/edge/input/prompt lưu trước dispatch qua persistIntent. Hàng chờ dùng giới hạn có sẵn của backend. Kết quả được đọc qua endpoint job/file, giải mã ảnh và lưu file thật. Nhánh recovery cũ bỏ qua job mới để không nhập nhầm vào ảnh tổng/JSON prompt. Unknown/missing/invalid/done chưa nhập chỉ đối soát, không tạo lại. Dừng chỉ ngừng gửi job mới, không hứa hủy dịch vụ đã nhận. Ảnh xong giữ dù có ảnh khác lỗi; kết quả lỗi thời vẫn lưu lịch sử, chưa chọn dùng.

Chỉ nút Dùng cho Bộ cảnh video gắn applied start/end ids. Có thể dùng các phần sẵn sàng và để phần thiếu lại với xác nhận rõ; phần đã chọn nhưng chưa có applied được bỏ qua trong preflight video, không tự hạ sang text hoặc ảnh khác. Các phần không chọn ảnh riêng giữ đường tham chiếu/video hiện có. Có Bỏ liên kết ảnh để chủ động quay về cấu hình cũ. Tạo/chọn bản ảnh mới không đổi applied hoặc timeline cũ. Clip mới ký signature có applied binding; kết quả clip của binding cũ giữ trong lịch sử, không giả là kết quả mới.

Prompt video nhận ảnh theo thứ tự: đầu, cuối (nếu dùng), rồi ảnh nhận diện gốc. Không bỏ ảnh cuối hoặc cắt bớt tham chiếu để vừa giới hạn 8 ảnh: báo lỗi yêu cầu giảm nguồn rõ ràng. Nếu đang nối khung cuối của phần clip trước thì yêu cầu chọn một cơ chế, không trộn với keyframe riêng. Job/receipt giữ sceneId, part, start_id/end_id, slot và prompt thực.

Mốc/lời/tham chiếu hoặc prompt ảnh đổi chỉ làm ảnh liên quan lỗi thời. Ảnh cuối ghi nhận id ảnh đầu lúc tạo; chọn ảnh đầu khác làm cặp đang xem cần kiểm tra. Applied cặp trước vẫn dùng đúng cặp trước cho đến khi người dùng áp cặp mới; không âm thầm đổi clip đã ghép. Viết prompt nhận ảnh từng phần thực tế và metadata start/end; nhóm tự chia theo ngân sách 8 ảnh gồm identity/overview/keyframes. Một cảnh vượt ngân sách phải giảm tham chiếu hoặc dùng prompt thủ công, không lén bỏ ảnh. Không bẻ lời/timing của kịch bản.

## Khả năng model và giới hạn

Giao thức Flow hiện có nhận ảnh qua ordered image_url content. Chỉ bật Đầu+cuối khi model công bố schema dưới đây qua /v1/models; không đoán từ tên hoặc mô tả. Bridge lưu allowlist trong model_details, kiểm lại lúc submit và từ chối cặp thiếu ảnh hoặc lệch scene/part trước gửi. Giao thức này là hợp đồng adapter, không phải khẳng định Flow/Muse/tài khoản đang dùng đã được gen kiểm chứng.

```json
{"id":"model-id","sceneforge_inputs":{"transport":"ordered_images","first_image":"start","second_image":"end","text_to_video":false}}
```

Engine không có metadata trên: ảnh cuối bị khóa. Muse chưa có hợp đồng ảnh cuối nên chỉ ảnh đầu/nhập file theo đường hiện có. Không thêm giá Lite/Pro hay số credit giả; phí/hạn mức chưa xác minh. Không có tự kiểm mặt/nhãn AI mới. Giữ các phiên bản ảnh và file trong kho dự án; module này không tự xóa ảnh cũ hoặc ảnh đang được clip sử dụng.

## Kiểm

- check_storyboard_modes.py: Chromium + SQLite/kho thật; provider fixture. Hai tab giữ ảnh, khóa capability, ảnh PNG đầu/cuối đúng bytes/thứ tự, exact scene/part/frame id trong video preflight, partial apply, no-overview, paired versions, stale theo cảnh, recovery không replay/nhập nhầm ảnh tổng.
- check_storyboard_contract.py: adapter thật/MockTransport, mô tả model không bật pair, metadata rõ mới bật, thiếu cuối/lệch slot bị chặn, đúng bytes/order và idempotency.
- Hồi quy Flow, photo story production, clip flow và merge MP4/âm thanh thật trong artifacts/storyboard-*.log. Không gen bằng tài khoản online.
