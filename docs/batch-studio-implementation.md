# SceneForge · Tạo hàng loạt · 23/10/2026

Tab Hàng loạt dùng chung sản phẩm, Bộ ảnh, Bộ cảnh và lưu trữ của SceneForge. Gallery theo prompt, form bên trái cuộn riêng; header / thanh công cụ giữ vị trí. Giữ board bốn cột, workflow node và Dựng. Các cơ chế tham khảo từ ảnh Phoma được tự triển khai; không dùng hoặc khẳng định đã đọc mã nguồn Phoma.

## Hai chế độ

**Mô phỏng trên máy:** dùng được trên web và cục bộ, không gửi prompt/ảnh tới provider. Canvas tạo PNG có nhãn minh họa, không suy luận prompt như mô hình AI. Job video chỉ tạo ảnh minh họa, chưa tạo MP4. Bấm Thử ngay 6 cảnh mẫu để thử hàng chờ.

**Gemini · API tạo ảnh:** adapter thực sự gửi `generateContent` và đọc ảnh inline trả về. Chỉ chạy ở localhost / 127.0.0.1 trong bản cục bộ; bản `?demo=1` khóa việc gửi. Dùng key Gemini được mã hóa trong Cài đặt → Phân tích (AI), không sử dụng phiên Flow hay tài khoản ChatGPT. Không có key/model được cung cấp để kiểm chứng một lượt tạo thật trong phiên triển khai này; toàn bộ kiểm thử provider dùng transport/HTTP fixture, không phát sinh phí.

Cách dùng: lưu key → chọn Gemini trong tab Hàng loạt → Đọc model từ key → chọn model → thêm prompt và ảnh → thêm vào hàng chờ → Chạy lượt tạo → rà số yêu cầu/model/thông báo có thể tính phí → bấm Gửi. Đọc model không gửi tạo ảnh; danh sách chỉ lấy model có tên chứa image và hỗ trợ generateContent từ chính key. Việc có tên trong danh sách chưa chứng minh quyền tạo, quota hay giá. Không đoán model, không fallback trả phí hoặc tự chuyển tài khoản.

Ảnh tham chiếu được chuẩn hóa PNG tối đa 1024px trước khi gửi; ảnh tham chiếu riêng đã có thumbnail tối đa 768px. Mỗi yêu cầu có đầy đủ ảnh được gán (tối đa tám ảnh); khi bật nối cảnh, dùng kết quả trước thay nhóm tham chiếu. Mô phỏng Canvas chỉ minh họa ảnh đầu tiên. Một yêu cầu ứng với một kết quả; 1–4 bản / prompt là nhiều yêu cầu riêng và có thể tính phí riêng.

## Hàng chờ và dữ liệu

- Nhập từng dòng hoặc JSON mảng chuỗi / object `{ "prompt": "…", "refs": [1,2] }`. Kiểm tra hết trước khi thêm, không tạo một phần khi JSON sai. Tối đa 60 prompt/lượt, 4.000 ký tự/prompt và 200 công việc trong bản hiện tại.
- Tham chiếu dùng chung / ghép 1–1 / tùy chỉnh refs trong JSON. 1–1 yêu cầu số ảnh được chọn bằng số prompt; số thứ tự JSON bắt đầu từ 1 theo danh sách ảnh. Tối đa tám file PNG/JPEG/WebP, 6 MB/file.
- Số việc đồng thời 1–4, số prompt/nhóm 1–60, giãn bắt đầu và nghỉ nhóm 0–60 giây. Nhóm sau đợi nhóm trước. Chọn Gemini mặc định về một việc; chọn nhiều hơn không chứng minh hạn mức dịch vụ cho phép.
- Tạm dừng ngăn nhận việc mới; việc đã gửi tiếp tục lấy kết quả và có thể vẫn tính phí. Không giả tiến độ phần trăm Gemini: hiển thị đang chờ dịch vụ. Lỗi / kết quả chưa rõ dừng hàng chờ, không tự gửi lại. Bản mô phỏng vẫn có hủy từng việc như trước.
- Tải lại trang luôn tạm dừng. Việc Gemini bị ngắt dùng nút **Kiểm tra kết quả API**: chỉ GET lại mã cũ và tải file nếu đã hoàn tất, không POST tạo lại. Không chuyển yêu cầu chưa rõ thành chờ để gửi lại.
- Tạo lại thêm job và phiên bản mới, giữ kết quả trước. Với Gemini phải bấm chạy và xác nhận gửi lại. Dù đổi sản phẩm trong form, job cũ giữ sản phẩm/tham chiếu đã chụp lúc thêm.
- Chọn / tải nhóm thành một ZIP chứa byte file và prompts.json, tối đa 256 MB/ZIP. File thiếu thì báo lỗi trước khi xuất; không bỏ qua âm thầm. Xuất danh sách JSON chỉ có metadata, không thay ZIP thư viện đầy đủ.
- Job và refs nằm trong prefs `batch-studio-v1`; file trong store files dưới key batch có phiên bản. Đọc được dữ liệu cũ, giữ file và mọi phiên bản. Record sai/phiên bản tương lai bị từ chối mà không ghi đè. Companion checkpoint SQLite/kho hash giữ metadata và byte file khi đổi profile trình duyệt.

## Đưa kết quả vào sản xuất

Trong hộp xem ảnh có **Thêm vào Bộ ảnh** cho ảnh nhập hoặc ảnh Gemini. Video nhập thật vẫn có **Thêm vào Bộ cảnh**. Bổ sung master, không đổi snapshot các phòng cũ; ảnh mô phỏng không được chuyển vào các bộ tạo thật.

**Đưa vào workflow…** cho phép chọn phòng từ video mẫu thuộc cùng sản phẩm và cảnh nhận. Mở workflow đó và thêm một phiên bản khung `pending`; không đổi khung đã duyệt, chosen clip, lời/kịch bản hoặc timeline. Cần người dùng duyệt khung trước khi tạo clip. Cùng resultKey/cảnh gửi lại được bỏ trùng. Payload nhiều ảnh được kiểm tra toàn bộ trước khi thay state. Hiện không đưa trực tiếp ảnh vào node của workspace ảnh mới; có thể thêm vào Bộ ảnh để dùng. Không tự gọi tạo clip hoặc tự xuất MP4.

## Phần phía sau

`local_engine/batch_images.py` dùng key trong Vault, endpoint loopback chịu cùng session/Host/Origin middleware. Gọi duy nhất endpoint Google cố định, không tải URL tùy ý từ phản hồi. Không retry mạng, 429, 5xx, không model fallback. Có giới hạn bốn kết nối provider, tối đa 16 yêu cầu đang giữ phía server; vượt giới hạn từ chối trước gửi.

`requests.sqlite` ghi claim và fingerprint trước network. Mã request cố định theo job, một request không gửi lại được, kể cả lỗi hoặc không rõ. Thành công cache metadata kết quả; sau restart các claim đang gửi chuyển unknown. Provider task chạy phía companion nên đóng tab không tự hủy; đóng companion chuyển sang unknown. File trả về được kiểm tra MIME, giải mã và giới hạn size rồi giữ nguyên byte trong DATA/batch-images; sau tải vào app được checkpoint vào thư viện hiện có. Không xóa file gốc/phiên bản. Nhật ký chỉ ghi metadata, không ghi key, prompt hoặc base64. Chưa biết phí thực tế thì cost=null.

## Kiểm thử

- `local_engine/check_batch_images.py`: mock transport chạy chính adapter: model discovery, xác nhận, payload tham chiếu, byte ảnh thật của fixture, duplicate claim, khôi phục restart, timeout/429 không retry, ảnh lỗi và log không chứa nội dung/key.
- `check_batch_provider.py`: UI bản cục bộ + HTTP fixtures: không gửi trước xác nhận, bấm để sau gửi zero, đúng model/tham chiếu/origin, recover và reload không POST thêm.
- `check_batch_workflow.py`: nhập PNG thực, chọn sản phẩm/phòng/cảnh, thêm khung pending, giữ approved/clip/chosen, bỏ trùng và từ chối payload lỗi không thêm một phần.
- `check_batch_studio.py`, `check_batch_gallery.py`, `check_batch_local.py`: concurrency/pause/chain, JSON và mapping, ZIP CRC/PNG, phiên bản bất biến, local SQLite/profile mới, responsive, không API trong demo.
- `check_workflow_navigation.py`, `check_runtime_safety.py`: hai workflow, dữ liệu cũ, header/iframe; bảo vệ session và duplicate/recovery.

Kiểm tra trên Linux/Chromium; không phải bằng chứng đăng nhập, hạn mức, chất lượng hoặc giá của tài khoản Gemini thật. Flow/Veo, Muse, GPT, Grok và tạo video từ prompt chưa được nối trong tab này.
