# Rà hai luồng SceneForge — code gọn

Đọc `docs/two-workflow-audit.md` trước: luồng thực, việc giữ/bỏ/gom, lỗi đã sửa và giới hạn.
Sau đó đọc `review/CHECKS.json`, `review/CHANGED_FILES.json`, `review/THAY_DOI.patch`.
Patch đã áp thử trên mã nguồn gói phát hành trước và so byte với từng file hiện tại.

`workflow`: Video mẫu. `photo-studio`: Ảnh & ý tưởng. `shared`: hợp đồng chung.
Theo đúng thứ tự nạp trong `scripts/demo-web/build.py` và `scripts/workflow/build.py`;
đọc toàn bộ override trước khi kết luận hàm đầu tiên là hàm đang chạy.
Backend giữ nguyên module để truy vết tài khoản/ledger/storage/editor. Không minify code.

Gói này để đọc/đánh giá, KHÔNG phải bộ cài. Không có media, model, venv, SDK, mật khẩu,
cookie hoặc dự án. File không kèm do bỏ tài nguyên không phải lỗi app đầy đủ.
Các tests đã chạy trên app đầy đủ, cần Chromium/media/backend khi chạy lại.
Không chứng nhận Windows hoặc tài khoản thật. Muse hiện là muse.ai, chưa phải Meta AI.

Đề nghị đánh giá: ưu tiên lỗi tái hiện gửi trùng, gen thừa, nhận sai cảnh/khung/prompt,
trạng thái chưa rõ và mất dữ liệu. Phân biệt thiếu tích hợp thật với vấn đề trình bày.
Báo rõ file/hàm, đầu vào và tác động. Không thêm node/model thay cho kiểm luồng.

Kiểm gói: `python review/verify_package.py` chỉ đọc file và tính SHA-256.
