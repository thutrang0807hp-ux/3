# Dịch bằng Gemini Chat — lựa chọn thủ công

Gemini Chat giữ làm lựa chọn sao chép/dán thủ công. Đường local hiện đã chuyển sang M2M100; Argos đã bỏ khỏi worker và bộ cài. M2M100 chưa tải được trọng số do proxy 403; xem `local-translation.md`. Không tự động hóa phiên đăng nhập Chat và không gọi Gemini API.

## Thao tác

Trong video mẫu, mở bảng Kịch bản → **Dịch Việt · Gemini Chat**:

1. Chuẩn bị lời để sao chép; mở Gemini Chat bằng tài khoản người dùng.
2. Dán prompt, lấy JSON phản hồi và dán lại SceneForge.
3. Xem bản dịch, đối chiếu rồi Áp dụng.

Prompt yêu cầu nhận ngôn ngữ từng câu, dịch tiếng Trung/Ý/ngôn ngữ khác về Việt; giữ ID, tên sản phẩm và con số, không tự thêm công dụng/lời quảng cáo. Không cần tải gói riêng từng ngôn ngữ để dùng đường chat này. Chất lượng phụ thuộc phản hồi Gemini và bản chép Whisper, không bảo đảm đúng mọi ngôn ngữ hoặc từ chuyên ngành.

App chỉ tạo văn bản sao chép, không mở phiên điều khiển browser, không nhập tài khoản, không gửi tin nhắn ngầm. Link Mở Gemini chỉ mở trang khi người dùng bấm. Hạn mức Chat theo tài khoản, không cam kết vô hạn hoặc không bao giờ phải chờ.

## Bảo toàn dữ liệu

- Mặc định chỉ lấy câu chưa có bản dịch; có lựa chọn dịch lại.
- Lưu yêu cầu đang chờ và phản hồi đã xem trong dự án để có thể quay lại; không ghi vào log hoạt động chung.
- JSON được kiểm tra số câu, ID đủ/không trùng, bản dịch không rỗng. Có thể nhận thứ tự khác nhưng ghép theo ID; không chấp nhận đổi ID hoặc tự sinh thêm câu.
- Chỉ cập nhật cột Dịch sát; lời gốc, mốc thời gian, lời mới nhập tay, clip và timeline giữ nguyên.
- Nguồn/lời/mốc hoặc bản dịch thay đổi lúc chờ thì không áp dụng phản hồi cũ. Không tự retry/gửi API khi JSON hỏng.
- Giới hạn 300 câu / 30.000 ký tự mỗi lượt; JSON tối đa 500.000 ký tự.

## Kiểm tra

`scripts/workflow/check_chat_translation.py`: trình duyệt thật, phản hồi dán giả lập tiếng Trung/Ý, xem trước, ghép ID, trùng/thiếu câu, giữ mốc/lời nhập tay, quay lại giữ JSON, chặn nguồn đã thay đổi; không gọi API hoặc Gemini Chat. Chưa kiểm thử chất lượng một phiên chat Gemini thực tế; người dùng thực hiện thao tác gửi/nhận.
