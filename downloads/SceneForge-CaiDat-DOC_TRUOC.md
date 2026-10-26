# Code Cài đặt — SceneForge

Snapshot code ngày 26/10/2026, sau bản đa nguồn `1604948`.
Đây là gói ĐỌC/ĐÁNH GIÁ CODE, không phải bộ cài hay mô phỏng độc lập.
Không sửa runtime khi đóng gói. Mọi file nguồn giữ nguyên byte, có manifest hash.
Không chứa model, ảnh/video dự án, database, cookie, mật khẩu, API key thật,
node_modules, venv, app.asar hoặc code/bộ cài Phoma. Test có tài khoản/key GIẢ ghi rõ.

## Phạm vi

Toàn bộ giao diện Cài đặt: Tài khoản, Phân tích AI, giọng, thư mục/kho lưu,
đầu ra và các mục engine/chẩn đoán có trong `g5Tabs`.
Kèm backend nguyên module để theo đường import; có endpoint ngoài Cài đặt vì
chúng dùng chung server/kho/ledger. Consumer Batch/Video mẫu/Ảnh chỉ kèm file
liên quan để truy vết lựa chọn tài khoản, không kèm toàn bộ hai workflow.
Thiếu các file build/UI ngoài phạm vi là chủ đích; KHÔNG chạy build từ gói này.
Không chứa SDK Flow/Muse/Gemini web bên thứ ba đã cài ngoài repo; xem setup và
`docs/engine-audit` để biết nguồn/revision, không suy rằng SDK đã được kèm gói.

## Đọc theo thứ tự

1. `scripts/demo-web/build.py`: thứ tự nạp. Các hàm được bọc/định nghĩa lại ở file
   sau; phải đọc hết `package5` → `accounts-dashboard` → `analysis-v3-settings`
   → `account-dispatch` → `storage-actions`, không chỉ đọc định nghĩa đầu.
2. `scripts/app-shell/package5.js`: g5Tabs, g5Content, g5BindSettings, prefs,
   engineRequest, lưu key, kiểm máy, lưu cài đặt. `app.js/package4.js/package6.js`
   cung cấp nền shell, lưu prefs, mở phòng và truyền cài đặt.
3. `accounts-dashboard.js`: đọc trạng thái, chọn đúng service, kết nối/kiểm/gỡ,
   sửa tên/bật/tắt/sắp thứ tự, đăng nhập các nguồn mới. `account-dispatch.js`:
   chế độ dùng riêng/chia việc/dự phòng, model Gemini theo nhiệm vụ, giới hạn clip.
4. `local_engine/server.py`, `account_settings.py`, `account_pool.py`, `vault.py`,
   `policy.py`, `schema.py`: trạng thái/routes, cấu hình dùng chung, phiên mã hóa,
   tính sẵn sàng của tài khoản; `review/ROUTES.json` lấy từ app thật với kho rỗng.
5. `flow_accounts.py`, `flow_provider.py`, `flow_account_engine.py`: đồng bộ/pin
   tài khoản engine Flow. `gemini_chat.py/gemini_chat_worker.py`: Gemini Chat.
   `muse_provider.py`: Muse cũ (muse.ai). `web_images.py`: ChatGPT/Grok/Meta AI.
6. `batch-studio.js`, workflow `direct-providers.js`, photo `providers.js` và
   `gemini-chat.js`: lựa chọn trong Cài đặt có đến đúng công việc không.
7. `request_ledger.py`, `admission.py`, `storage_jobs.py`, `library*`,
   `runtime_safety.py`: request chống trùng, bảo vệ kho và file/kết quả.
8. `package5.py`, `machine_checks.py`, setup/install scripts: cài dependency,
   kiểm trạng thái, logging, giới hạn và chẩn đoán. Không chạy setup để đọc code.

## Đề bài cho bên đánh giá

- Tài khoản chọn trong Cài đặt có được ghim đúng vào job của từng nguồn không?
- Dùng riêng, chia việc, dự phòng có ý nghĩa nhất quán giữa UI và backend không?
- Đổi tài khoản, tắt tài khoản hoặc đổi kho sau khi rà/trước gửi có bị chặn đúng?
- Restart có giữ lựa chọn/phiên, xử lý job chưa rõ mà không gửi trùng không?
- Đăng nhập thành công, session_verified, configured, generation_verified có
  đang bị UI đánh đồng? Kiểm phiên có thực sự chứng minh khả năng tạo ảnh không?
- Key/cookie có bị lộ trong status/log/export, và file vault/permissions thế nào?
- Mỗi cài đặt (giọng, model theo role, chất lượng xuất, thư mục/quota, retry...)
  có consumer thực dùng hay chỉ lưu giá trị? Truy từ nút → API/prefs → consumer.
- Các giới hạn worker/tab/tài khoản/engine có khớp nhau, có gây kẹt hoặc gửi thừa?
- Đánh dấu lỗi tái hiện, rủi ro đọc code, và tính năng chưa triển khai riêng biệt.

## Chứng cứ và giới hạn

`review/EXISTING_CHECKS.json` và logs là kết quả đợt kiểm trước khi đóng gói,
KHÔNG phải toàn bộ test trong gói vừa được chạy lại. Playwright/HTTP/SQLite thật
nhưng trang/provider/runner giả. Flow account-engine test cần đúng venv engine;
không coi thiếu dependency khi chạy bằng Python khác là đã kiểm engine thật.
Đợt này chỉ tạo gói, kiểm manifest và đối chiếu file nguồn.

CHƯA kiểm tài khoản online thật hoặc Windows. Grok/ChatGPT/Meta có adapter
trình duyệt mới, selector chưa được xác nhận trên website thật. `muse.ai` cũ và
`meta.ai` mới là hai dịch vụ khác nhau. Không hứa không giới hạn/quota miễn phí.
Batch chưa có lô riêng, Đóng & dọn lô hoặc TTL 24h; không đánh đồng với cài đặt
lưu trữ chung. Bản web không thực hiện đăng nhập/cài engine local.

Kiểm gói an toàn: `python review/verify_package.py` — chỉ đọc file/hash,
không import app, đăng nhập, cài model hay gửi AI.
