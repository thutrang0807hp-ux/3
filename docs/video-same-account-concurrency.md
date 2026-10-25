# Nhiều clip đồng thời trên một tài khoản

## Cách dùng

Bản cục bộ → Cài đặt → Tài khoản → Flow hoặc Muse → **Clip đồng thời / tài khoản**. Nhập 1–16, Lưu. Chỉ đổi khi hàng đợi dịch vụ đã kết thúc. Chọn **Dùng riêng tài khoản đã chọn** để các clip đều dùng A; chọn Chia việc nếu muốn phân nhiều tài khoản.

Ví dụ đặt 7: một tài khoản có thể được app gửi 7 clip độc lập, phần còn lại chờ slot trống. Đặt 12 cũng được. Đây là trần gửi ở app, không phải xác nhận hạn mức nhà cung cấp. Mặc định vẫn là 1; khuyên thử 2 rồi tăng dần sau khi kiểm tài khoản thật. Tổng dịch vụ tối đa max(3, số mỗi tài khoản), chặn nhiều tài khoản nhân số slot thành không giới hạn. Một lượt UI hiện tối đa 30 clip, có thể thêm lượt khác vào hàng đợi tới giới hạn backend hiện có.

Mỗi clip có request ID, room/scene/part và file kết quả riêng. Kết quả không được gán theo thứ tự hoàn tất. Không tự gửi lại khi timeout, CAPTCHA, lỗi hoặc kết quả chưa rõ. Việc đã gửi vẫn có thể tính phí; đổi số slot không tăng credit tài khoản. Gemini Chat không đổi, adapter hiện không tạo video Gemini trực tiếp.

## App và engine

- Muse: thay khóa độc quyền tài khoản bằng bộ cấp slot có giới hạn, mỗi tiến trình SDK có thư mục riêng. Khi chạy nhiều clip, không ghi đè phiên dùng chung bằng bản phiên trả về muộn từ một clip. Chỉ nhận session ID có trong phản hồi của chính request; không suy từ danh sách hội thoại chung. Nếu không có ID chắc chắn thì dừng unknown, không đoán clip khác.
- Flow: app cấp slot và ghim tài khoản; trước khi gửi đòi engine xác nhận đúng giới hạn. Wrapper cập nhật giới hạn token lưu DB và concurrency manager upstream. Reset limit giữ bộ đếm inflight, không reset số việc đang chạy về 0. Engine cũ không có endpoint sẽ bị chặn trước generation.
- Thay đổi số slot làm token bảng rà cũ hết hiệu lực. Giới hạn mới lưu vault cùng dữ liệu app, không thay gói tài khoản.

Flow cần đóng engine cũ rồi chạy `local_engine/start-flow.bat` từ gói mới. Không cần tải lại model/SDK đã có. App vẫn dùng cùng kho dữ liệu; không xóa dữ liệu người dùng khi cập nhật.

## Kiểm chứng

`check_video_concurrency`: hai adapter thật với transport/worker fixture, một tài khoản, bảy việc chồng nhau, hai việc chờ, chín file video FFmpeg và request ID riêng, không gửi trùng; có thể lưu mức 12. `check_flow_account_engine`: endpoint giới hạn cập nhật DB/manager qua fixture, từ chối ngoài phạm vi. Kiểm lại UI gửi/nhận cảnh và các bài Muse/Flow mặc định.

Chưa có tài khoản thật: **chưa xác nhận Flow/Muse cho một tài khoản tạo 7, 12 hay 16 video đồng thời**. Dịch vụ có thể tự xếp hàng hoặc từ chối. Muse SDK vẫn trỏ muse.ai; chưa chứng minh tương thích meta.ai. Không dùng cơ chế này để vượt giới hạn dịch vụ.
