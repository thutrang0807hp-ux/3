# Gemini Chat: SDK và adapter SceneForge

Repo https://github.com/HanaokaYuzu/Gemini-API, revision `1ad0d4a93e505e77c79769d78ef2997641f973c8`, AGPL-3.0. SDK cài riêng tại `/workspace/engines/gemini-web/venv` trên máy phát triển (~155 MiB gồm source/dependencies). Gói app chứa adapter và bộ cài, không chứa venv.

Đã nối đăng nhập trình duyệt/context riêng hoặc cookie JSON, kiểm phiên trước khi lưu mã hóa; chọn tài khoản dùng chung và ba chế độ chạy. Worker riêng từng thao tác, không tự đọc cookie trình duyệt khác, không nhận guest thay tài khoản, không dùng retry tự động của SDK khi tạo. Model theo vai trò lấy từ tài khoản đã kiểm. Không tự chuyển sang API trả phí.

Các bước phân tích, viết, dịch và tạo ảnh đã nối; xem [multi-account-dispatch.md](multi-account-dispatch.md). Storyboard tổng gửi làm ảnh tham khảo cùng bộ ảnh sản phẩm khi viết prompt video, không bắt buộc cắt thành ảnh lẻ.

Máy người dùng cần Python 3.11/3.12 và Git. Chạy `local_engine/install-gemini-web.bat` hoặc `python -m local_engine.setup_optional_repos gemini`; hỗ trợ `--directory`/`--source`. Mở Cài đặt → Tài khoản → Gemini Chat. Không cần model GB hoặc API key, vẫn chịu hạn mức/quyền Google. Video chọn Flow/Muse, adapter Gemini này không tạo video trực tiếp.

Đã kiểm dependencies, hợp đồng SDK, single-send, phân biệt quota/partial/network, endpoint app và UI Chromium bằng fixture. **Chưa đăng nhập hay tạo nội dung Google thật, chưa kiểm Windows.** SDK metadata từ checkout shallow là `0.0.post1`; revision Git mới là định danh đã ghim.

Source adapter nằm trong gói; installer giữ source upstream tại revision cùng LICENSE (bản LICENSE/dependencies trong `docs/engine-audit`). Phân phối/sửa SDK phải tuân thủ AGPL-3.0.
