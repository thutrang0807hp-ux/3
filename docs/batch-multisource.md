# Tạo ảnh hàng loạt: nối nhiều nguồn

Bản cập nhật nối Flow, Grok Chat, ChatGPT Chat và Meta AI vào tab Tạo hàng loạt; giữ Gemini Chat và Gemini API riêng. Không tự chuyển nguồn, dùng API thay phiên chat hoặc chạy mô phỏng khi tạo thật lỗi.

## Dùng trong bản cục bộ

1. Mở Tạo hàng loạt → chọn Động cơ. Với ChatGPT/Grok/Meta bấm Tài khoản nguồn này → Kết nối → tự đăng nhập trong cửa sổ dịch vụ → Lưu phiên. Nếu thiếu Chromium, chạy `local_engine/install-chat-browser.bat`.
2. Chọn tài khoản trong Cài đặt. Dùng riêng hoặc Chia việc giữa nhiều tài khoản; một tài khoản chat mới chỉ chạy một ảnh tại một thời điểm, tối đa bốn việc toàn adapter. Tab mặc định một worker khi đổi nguồn; tăng Song song nếu cần.
3. Với Flow, kết nối engine cục bộ và đồng bộ tài khoản như trước; đọc/chọn model ảnh. Không nhập tài khoản Flow vào adapter ChatGPT/Meta.
4. Nhập prompt và ảnh → thêm hàng chờ → Chạy lượt tạo → rà số lượt/nguồn/model/tài khoản → xác nhận. Token tài khoản được kiểm lại sau checkpoint xuống ổ.
5. Nhận file ảnh vào gallery và kho cục bộ. Tải ZIP, thêm vào ảnh sản phẩm hoặc gửi khung vào Video mẫu. Phiên/account/source đi cùng từng request; đóng trang không tự gửi lại.

Ảnh tham chiếu tải từ máy và ảnh nối tiếp lấy từ file gốc, không gửi preview 768px. Ảnh sản phẩm cũ chưa có file gốc trong metadata vẫn dùng ảnh sản phẩm đang lưu. Tối đa tám ảnh, tổng 24 MB; output giữ file trả về, preview riêng.

## Đã kiểm và chưa kiểm

- Playwright thật trên trang dịch vụ bị intercept: đăng nhập khách bị chặn, lưu phiên mã hóa riêng, tải tham chiếu, click một lần, nhận ảnh mới và giữ PNG. **Đây không phải kiểm selector trên website thật.**
- HTTP/SQLite/kho thật + runner giả: account/source/request đúng, token cũ bị chặn, không gửi trùng, mất kết quả sau click thành unknown, job đang chạy được bảo vệ khi dọn/đổi kho/gỡ tài khoản; file vào kho theo hash và bỏ bản backend trùng.
- Trình duyệt app thật + provider giả: Flow/Grok/ChatGPT/Meta, model Flow, rà tài khoản đổi, PNG tham chiếu 1400px nguyên kích thước, nhận/tải file, mở lại và kiểm kết quả không gửi mới; tài khoản dùng chung bảng Cài đặt.
- **Chưa có bằng chứng gen bằng tài khoản online thật hoặc chạy Windows.** Selector chat mới có thể phải chỉnh theo UI/ngôn ngữ dịch vụ. Không tuyên bố “không giới hạn”; dịch vụ quyết định quota.
- Adapter chat mới không tự đối soát hội thoại sau khi trình duyệt đã đóng mà kết quả chưa rõ. Khi đó kiểm lịch sử dịch vụ, tải và nhập file thủ công; không tự gửi lại để tránh tốn thêm lượt.
- Meta AI ở đây là `meta.ai`, không phải `muse.ai`. Adapter Muse video cũ giữ riêng; không dùng cookie hai dịch vụ lẫn nhau.
- Tab này mới nối **ảnh**. Video từ prompt chưa được nối thêm qua những adapter này.
- Chưa triển khai lô riêng, nút Đóng & dọn lô, TTL 24h và quota theo lô trong đợt này; danh sách/kho ảnh vẫn theo cơ chế Batch cũ. Không coi việc tải ZIP là đã dọn file.

## Đối chiếu Phoma

Đã đọc tĩnh bộ cài Phoma 1.6.2 từ GitHub releases (SHA-256 `d5d58d77edac8ddb2318d27b79cd7272827a2ae19fcfa9be9850307ddf67d60d`), không chạy EXE. `package.json` cho thấy Electron + React + Express + Puppeteer Core. Có module profile/session theo tài khoản, job registry và xử lý image stream riêng. Nhánh ChatGPT có mã hội thoại/tải ảnh và ghi nguồn chatgpt2api; không thể gọi đó là cùng cơ chế đơn giản với Muse SDK.

SceneForge dùng mã adapter Playwright tự viết, tái sử dụng account pool, ledger, checkpoint và thư viện của chính app. Không nhúng app.asar, thành phần fingerprint/challenge, giấy phép hay bản cài Phoma vào gói. Việc đọc được Phoma không chứng minh adapter mới của SceneForge đã chạy thật trên các dịch vụ.
