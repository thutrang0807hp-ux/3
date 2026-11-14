# SceneForge .125 — lời mới theo sản phẩm, học nhịp video mẫu

Đóng SceneForge, chạy **SceneForge-Update-20261112-v46.125-Product-Script.exe**, chọn đúng thư mục app rồi mở lại. Bản gộp nhận từ .62 trở lên, gồm .119–.124.

Trong phòng **video mẫu**, mở node **Kịch bản & lời thoại**:

1. **Nhập / sửa thông tin**: tên và mô tả được nạp từ sản phẩm đang chọn khi chưa sửa riêng. Bổ sung dữ kiện có căn cứ, khách hàng, giá/ưu đãi, điều không được nói. Thông tin tự lưu theo phòng. Nút Nạp lại lấy tên/mô tả mới đã lưu; nếu đổi sản phẩm, app yêu cầu nạp lại để không dùng nhầm dữ kiện.
2. **AI viết lời theo sản phẩm**: gửi bản chữ, mốc, mô tả cấu trúc mẫu và thông tin sản phẩm tới nguồn AI đang chọn trong Cài đặt. Cần lời mẫu từ chép CPU hoặc bản chữ/SRT; không tự đoán lời từ ảnh. Chỉ viết chữ, không tạo ảnh/clip.
3. **Xem bản nháp → Áp dụng vào cột Lời mới**. Có thể sửa từng câu trước khi áp dụng. Lời gốc, dịch sát, ID và mốc giây giữ nguyên. Những cảnh đổi lời được bỏ lựa chọn clip/lời chia cũ, nhưng các phiên bản clip và lịch sử vẫn giữ; cần chọn hoặc tạo lại clip phù hợp với lời mới.

Video mẫu cung cấp nhịp/cách kể; tên, công dụng, giá và ưu đãi của sản phẩm mẫu không được coi là dữ kiện cho sản phẩm của bạn. Thiếu thông tin, AI có thể hỏi bổ sung. Mỗi lời mới có nhãn dữ kiện đã dùng và phần ghi chú để bạn rà. Đây không phải bảo đảm máy tự kiểm chứng sự thật hoặc độ dài phát âm.

Link sản phẩm hiện chỉ lưu để tham khảo, **chưa tự đọc trang**. Hãy dán mô tả/thông số thực tế vào phần thông tin. Ảnh sản phẩm vẫn dùng qua bộ tham chiếu, chưa tự đọc công dụng từ ảnh.

Nếu dữ kiện, nguồn hoặc lời thay đổi trong lúc chờ, bản cũ không được áp dụng. Khi lượt gửi chưa rõ kết quả, dùng Nhận lại lượt đã gửi; app đọc lại đúng lượt, không tự gửi mới hoặc đổi nguồn AI.

Đã kiểm API/ledger với AI mô phỏng, giao diện Chromium và lưu IndexedDB thật: nạp từ sản phẩm qua bridge, sửa/lưu thông tin, duyệt lời, giữ lời gốc/mốc và clip cũ, chặn kết quả lỗi thời, nhận lại không gửi mới, đổi sản phẩm không dùng nhầm facts. Kiểm tra Kho kịch bản cũ và tham chiếu khung đã qua. Chưa gọi Gemini thật hoặc chạy bộ cài Windows.
