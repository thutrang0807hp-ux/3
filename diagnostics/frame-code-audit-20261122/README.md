Các chương trình này tái hiện các lỗi đã ghi trong ../../docs/frame-code-audit-20261122.md tại bản .151. Chúng đọc baseline commit `5a5a306` qua Git, không đọc bản sửa mới. Cần chạy trong repository có commit đó. Chúng cố ý kiểm tra hành vi lỗi hiện tại, không phải bộ kiểm tra chứng nhận đã sửa. Không kết nối Google, không dùng tài khoản thật, không gọi tạo ảnh.

- `node diagnostics/frame-code-audit-20261122/reproduce_state.js` đọc hàm từ workflow.html tại baseline .151.
- Chạy `reproduce_download.py` trong môi trường có SDK Gemini ghim revision 1ad0d4a93e505e77c79769d78ef2997641f973c8; nó dùng GeneratedImage thật với HTTP transport giả lập. Trong workspace kiểm tra: `PYTHONPATH=/tmp/sceneforge-gemini-sdk-deps python diagnostics/frame-code-audit-20261122/reproduce_download.py`.
