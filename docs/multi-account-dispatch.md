# Tài khoản dùng chung và dự phòng

Bản này nối lựa chọn tài khoản Gemini Chat, Muse và Flow từ Cài đặt tới công việc AI. SDK đã cài trong môi trường phát triển; chưa đăng nhập hoặc tạo nội dung bằng tài khoản thật, chưa kiểm trên Windows.

## Cách dùng

1. Mở bản cục bộ → Cài đặt → Tài khoản → chọn dịch vụ. Đăng nhập từng tài khoản, kiểm phiên. Thêm B không thay A đang dùng.
2. Chọn **Dùng tài khoản đã chọn**, **Dự phòng theo thứ tự**, hoặc **Chia việc giữa tài khoản**. Thứ tự dự phòng bắt đầu với tài khoản đã chọn, rồi theo thứ tự danh sách.
3. Cài đặt → Phân tích (AI) → **Gemini Chat**. Model theo vai trò viết/phân tích/dịch/ảnh lấy từ tài khoản đã kiểm. Gemini API vẫn là lựa chọn riêng có thể tính phí; không tự chuyển sang API.
4. Rà nội dung trước khi gửi. Kiểm tra kết quả để nhận về đúng phòng/cảnh/nhịp. Ảnh không tự duyệt, các bản cũ được giữ.

## Những bước đã nối

- Gemini Chat: phân tích ảnh cảnh, phân loại tham khảo, viết kịch bản/công thức/prompt, dịch lời, tạo storyboard tổng, ảnh khung và ảnh hàng loạt. Dịch có rà và áp dụng, giữ lời nguồn/mốc thời gian/lời tự sửa.
- Ảnh & ý tưởng: thanh Gemini gửi/nhận prompt và storyboard tổng; clip chọn Flow hoặc Muse.
- Video mẫu: nút **AI trực tiếp** trên thanh canvas để tạo ảnh Gemini hoặc clip Flow/Muse; nhận về đúng cảnh/phần clip.
- Header và Cài đặt đọc chung lựa chọn. Đổi lựa chọn khi đang rà làm bảng rà cũ hết hiệu lực. Công việc đã nhận giữ kế hoạch lúc gửi.

## Chuyển tài khoản

Dự phòng chỉ sang B khi A bị từ chối rõ ràng trước khi nhận việc: SDK báo hết hạn mức hoặc phiên không hợp lệ. Generic HTTP 429, mất mạng, lỗi prompt, kết quả một phần và kết quả không rõ đều không tự gửi lại. Flow kiểm phiên/số dư trước khi tạo, chuyển khi xác minh số dư video bằng 0; không đoán giá khi số dư dương nhưng có thể thiếu. Lỗi sau khi Flow đã nhận yêu cầu không tự chuyển B.

Mỗi hồ sơ một việc; mỗi dịch vụ tối đa ba việc đồng thời. Chia việc phân các việc mới, không có nghĩa chạy vô hạn. ID bền vững chặn phát lại cùng lượt. Sau khi tiến trình chết, lượt chưa rõ không tự gửi lại.

## Cài và khởi động

- Chưa có SDK Gemini: chạy `local_engine/install-gemini-web.bat`. Nếu đã có revision đúng thì chỉ cập nhật app.
- Flow: chạy **bản mới** `local_engine/start-flow.bat`, vào Tài khoản → Flow → Đồng bộ từ engine, kiểm tra và chọn tài khoản. Wrapper ghim ID vào request thật, kiểm phản hồi xác nhận ID. Engine cũ không có cơ chế này bị chặn gửi từ app.
- Muse: dùng bộ cài hiện có. SDK trỏ `muse.ai`; chưa chứng minh dùng được tài khoản `meta.ai`.
- Không cần antidetect cho quản lý hồ sơ này. Gemini đăng nhập dùng context riêng; SDK dùng tệp phiên tạm riêng. Google có thể từ chối trình duyệt tự động; có tùy chọn nhập cookie phiên của người dùng.

## Lưu trữ và giới hạn

Phiên app lưu vault mã hóa, không trả cookie trong status/log. Flow có kho xác thực riêng upstream; không khẳng định toàn bộ DB engine đã mã hóa. Tệp tạm có thể còn nếu máy bị tắt cưỡng bức. Không triển khai chống phát hiện/fingerprint hoặc vượt hạn mức.

Gemini nhận diện hồ sơ bằng fingerprint cookie, chưa xác minh danh tính Google để gộp hai cookie khác nhau của cùng người. Chất lượng/model/hạn mức do dịch vụ quyết định. File tải về backend và file nhập dự án có thể cùng tồn tại; dọn thư viện chưa tự xóa mọi bản kết quả backend.

Kiểm thử: fixture SDK, endpoint thật của app, Chromium Cài đặt/toolbar/nhận ảnh và clip, video FFmpeg thật, kiểm ảnh Pillow. **Chưa xác nhận đăng nhập Google/Muse/Flow, credit, chất lượng hoặc tạo đồng thời trên dịch vụ thật.**
