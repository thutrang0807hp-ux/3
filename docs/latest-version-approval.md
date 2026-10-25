# Duyệt bản mới nhất và tự dọn bản cũ — 26/10/2026

## Hành vi

- Node ảnh: một ô cho một cảnh/prompt ảnh. Node video: một ô cho từng phần prompt clip (a, b… nếu cảnh dài). Ô và cửa sổ xem mặc định luôn lấy bản được nhập/tạo mới nhất, không quay về bản từng chọn trước đó.
- Trong cửa sổ, **Tạo lại bản mới** chuẩn bị đúng cảnh/phần đó qua nguồn đang dùng (Gemini Chat cho ảnh; Flow/Muse cho clip). Vẫn có bước rà yêu cầu tạo và tài khoản trước gửi; không tự gửi lại yêu cầu chưa rõ kết quả. Bản hiện tại giữ đến khi có kết quả mới nhập được.
- **Duyệt hết … đạt** hoặc duyệt riêng trong cửa sổ: lưu bản mới nhất được duyệt, rồi tự dọn những bản trước trong đúng các ô vừa duyệt. Không có nút dọn phụ hoặc hộp xác nhận xóa thứ hai. Clip được duyệt được ghi quyết định accepted/received. Khung vẫn qua điều kiện kiểm ảnh hiện có.
- Lượt đang tạo, lỗi, chưa rõ kết quả hoặc bị đánh dấu cần sửa không được duyệt hàng loạt. Clip phải khớp khung đã duyệt. Duyệt ảnh không dọn các clip; duyệt một phần video không dọn phần khác.
- Dọn ngay file đủ điều kiện khỏi kho và cache IndexedDB, không chuyển sang tab Lưu trữ hoặc thùng rác của hệ điều hành. Không hoàn credit. Giữ dấu vết nhẹ: ID phiên bản/yêu cầu, prompt, model và thông tin lỗi trong sổ job hiện có.

## Bảo vệ và tính bền

- Backend kiểm room, revision, ID bản mới nhất và trạng thái duyệt từ snapshot đã lưu, không tin đơn thuần danh sách hash do UI gửi.
- Chỉ xét hash vừa mất tham chiếu do bỏ các bản cũ thuộc ô được duyệt. Không gom mọi kết quả cũ trong dự án vào lượt dọn này.
- Giữ bản ghim, media trên timeline, tài nguyên/dự án khác và kết quả chưa nhận. Bản cũ chỉ nằm trong kho editor mà chưa dùng trên timeline, hoặc hàng chờ nhập, được gỡ khi xác định đúng workflow version ID. Không tự thay clip đã nằm trên timeline.
- Gỡ bản cũ khỏi lịch sử cấu trúc có thể trỏ tới media, giữ log chữ. Release theo room/hash cho phép sao lưu cũ bỏ qua media đã chủ động giải phóng, không làm media quay lại qua khôi phục. Các bản sao ngoài app không bị xóa.
- Dùng journal/quarantine sẵn có với hạn bằng 0: ghi ý định bền trước xóa, lỗi khóa file thì thử lại qua cơ chế resume. Số byte giải phóng chỉ cộng nếu file thực sự hiện hữu và unlink thành công trong lượt đó.
- Phải flush workflow/editor trước, chốt kho rồi mới dọn. Nạp lại cache cùng snapshot canonical sau thao tác; editor ẩn được đóng để không ghi trả danh sách bản thừa cũ. Yêu cầu dọn được lưu trong `approvalCleanupPending`; nếu tác vụ còn chạy thì đợi và thử lại khi phòng đang mở, hoặc khi mở lại phòng. Nếu bản mới hơn xuất hiện thì bỏ ý định dọn đã cũ.
- Nếu mất phản hồi sau lúc backend có thể đã chốt: tạm dừng ghi kho từ cache cũ, giữ dấu nạp lại; mở lại app lấy snapshot kho máy trước. Không tự gửi generation hoặc phát lại yêu cầu tạo.

## Phạm vi

Áp dụng cho luồng Video mẫu, hai node Ảnh khung và Video Veo/Flow/Muse. Bản GitHub Pages chỉ xem/duyệt trong browser; xóa file vật lý cần app local và kho đang kết nối. Node ảnh tĩnh/storyboard của luồng riêng không được đổi trong đợt này.

Không cài repo/model mới, không chạy tài khoản online, không xóa dữ liệu người dùng trong môi trường làm việc. Đợt sau đã bổ sung sửa claim/register, dự phòng ổ unknown và biên nhận checkpoint/dọn tổng quát; xem `docs/reference-flow-improvements.md` và báo cáo mới. Phép thử vẫn không thay cho kiểm tài khoản/Windows thật.

## Kiểm chứng

- `check_version_approval`: file/SQLite thật trong thư mục tạm. Tạo 5 bản clip và 3 ảnh; dọn đúng bản cũ, giữ phần chưa duyệt/timeline/hash dùng chung; bỏ alternative/pending không dùng; lịch sử và backup không làm hồi sinh media; từ chối duyệt ID cũ; mở lại thư viện.
- `check_approval_ui`: Chromium + backend thật, media fixture. Mở đúng bản mới nhất dù lựa chọn trước còn cũ; hai ô clip cho hai phần; duyệt không mở hộp dọn; HTTP file cũ trả 404, file mới vẫn tải được; tạo lại chuẩn bị đúng một phần và giữ candidate; mất phản hồi sau commit rồi mở lại vẫn nạp kho đúng. Không bấm gửi provider.
- Kiểm hồi quy `check_direct_workflow`, `check_storage_lifecycle`, `check_storage_jobs`, `check_storage_ui`.
- Chưa thử Windows thật hoặc gen qua tài khoản thật. Bản sao media bên ngoài, file legacy chưa đủ ownership, pin và các tham chiếu còn hợp lệ vẫn có thể giữ dung lượng.
