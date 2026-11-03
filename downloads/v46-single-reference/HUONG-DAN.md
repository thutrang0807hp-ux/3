# SceneForge .53 — một ảnh tham chiếu, một video mỗi lượt mới

Cập nhật từ bản .52 đang chạy được. Nhánh CLI không còn upload ảnh trước bằng
RPC; chỉ CLI r2v --ref thực hiện một lần upload, vẫn giữ --count 1 cho video.
Giữ nguyên tài khoản, dự án, prompt, model và phần nhận/tải lại video của .52.
Không sửa SDK gốc, không xóa ảnh hoặc video cũ trên Flow.

Nguyên nhân cũ: native prepare upload ảnh một lần, CLI R2V upload lại một lần.
SDK mặc định không tìm dùng lại ảnh theo filename cho đường video R2V.

Đã kiểm tra mã lấy từ EXE: chuẩn bị không gọi native.upload, tám kịch bản CLI,
submit/ledger, tải lại clip cũ và ffprobe/file endpoint. Các kiểm tra dùng fixture;
chưa xác minh lượt tạo thật trên Flow với thay đổi này.

SHA256 EXE: `bec703a815dfc65872268acc3d3234eb01cb4bb2041729d187a53618d4db59dd`
