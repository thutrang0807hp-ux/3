# Đánh giá gflow-cli cho SceneForge — 30/10/2026

Đã đọc mã và tài liệu tại commit db31ab724798ed0a96c42010c56bba1be5f140bf, phiên bản khai báo 0.92.0. Chỉ đọc repository và chạy code kiểm tra của SceneForge với trang mô phỏng; không chạy đăng nhập/generation của gflow-cli trên tài khoản Google.

## Kết luận

Repo có source thực cho Flow profile, hàng chờ và I2V trên giao diện migrated tại flow.google.com. Đáng tham khảo cho kiến trúc một ảnh đầu + prompt; không phải giải pháp đã kiểm chứng cho lỗi Google từ chối đăng nhập trên máy người dùng.

## Những điểm có bằng chứng

1. **Phải phân biệt giao diện Flow.** `src/gflow_cli/api/transports/migrated_composer.py` có `apply_video_settings` và `attach_start_frame`. `agent_only_composer.py::unported_video` chỉ nhận text-to-video, từ chối I2V/R2V. Không được diễn giải rằng repo chạy mọi loại video trên mọi giao diện.
2. **Gắn ảnh đầu được kiểm tra cụ thể.** Nhánh migrated chọn Frames cho I2V, upload ảnh, bind Start theo tên riêng của lượt, rồi kiểm tra ảnh được gắn với lượt tạo. Đây là mức kiểm chứng mạnh hơn việc chỉ nhìn thấy một thumbnail. Không lấy thumbnail thư viện làm bằng chứng ảnh đầu đúng.
3. **Bộ điều khiển và phiên bản Playwright đi cùng nhau.** `pyproject.toml` yêu cầu Python Playwright >=1.61.0,<1.62.0. Phần giải thích trong source ghi nhận 1.62.0 từng treo sau upload I2V. Đây là ghi nhận của tác giả, chưa tái hiện được trên Google thật ở phía SceneForge.
4. **Không đồng nhất phiên bản Python và Node.** Repo MCP Node được đọc trước dùng Playwright ^1.61.1, nhưng bản Python 1.61.1 không có trên index đã kiểm tra; nhánh Python gflow dùng 1.61.0. Không thể chép số phiên bản giữa hai hệ sinh thái.
5. **Đăng nhập Google và đăng nhập Flow không phải một kết luận.** `auth/verification.py` phân loại nhiều trạng thái. Tài liệu ghi endpoint labs cũ đã trả 410 trong rollout mới. Không nên thêm lại endpoint retired hoặc coi có cookie Google/địa chỉ email là đã xác minh toàn bộ khả năng tạo Flow.
6. **Tài liệu live verification có giới hạn.** Báo cáo v0.92.0 chủ yếu kiểm tra an toàn đường dẫn/tải file và một số lượt ảnh; bản đó ghi 0 Veo credits. Không thể nói release này vừa kiểm chứng lại toàn bộ I2V chỉ vì có file LIVE_VERIFICATION.

## Phần đã thực hiện trong SceneForge

- Tạo môi trường kiểm tra riêng, cài Python Playwright 1.61.0, không sửa môi trường chung 1.62.0.
- Chạy `check_flow_managed_browser`: profile và watcher nhận tài khoản fixture, giữ đúng account/project, một lần gửi, nhận video qua chunk/hash/ffprobe, duplicate ID không gửi lại, phản hồi signin/rejected thì dừng. Kết quả PASS.
- Chạy `check_flow_video_summary`: chuẩn bị một ảnh/prompt, chọn 9:16/x1, đọc 8 giây từ summary; sai thời lượng hoặc x1 không đổi thì dừng. Kết quả PASS.
- Sau các kiểm tra này, giới hạn requirements nguồn của SceneForge cho lần đóng gói đầy đủ tiếp theo thành Python Playwright >=1.61.0,<1.62.0.

Chưa nâng/hạ Playwright trên máy Windows người dùng. Updater mã v35 không chứa bộ driver Playwright mới, nên thay requirements trong source không được coi là thay runtime đã cài. Không phát v36 hoặc hướng dẫn người dùng đăng nhập lại chỉ để kiểm tra phỏng đoán này.

## Điều cần xác nhận trước khi thay runtime Windows

Cần biết `distributions.playwright` trong `BUNDLED-COMPONENTS.json` cạnh SceneForge.exe, hoặc phiên bản metadata từ chính Python runtime của app. Không dùng phiên bản trong venv Flow2API hoặc môi trường kiểm tra cloud để suy ra runtime app Windows. File inventory là lúc đóng gói; nếu runtime đã được sửa bằng tay thì cần đối chiếu metadata hiện tại.

Nếu phiên bản đã là 1.61.x, giả thuyết lệch minor không giải thích được lỗi đăng nhập và không nên đổi thư viện chỉ để thử. Nếu khác, đó là một khác biệt tương thích cần kiểm tra, vẫn chưa phải bằng chứng nguyên nhân Google từ chối.

## Giới hạn

Chưa kiểm chứng Google Flow thật hoặc Windows. Không nhập profile/cookie/token từ Phoma/gflow, không chạy nhánh giấu điều khiển trình duyệt để tránh lỗi bị từ chối, không thay xác minh Google. Những kiểm tra đã qua chỉ chứng minh luồng fixture và tương thích cục bộ, không chứng minh đăng nhập Google thành công.

Nguồn:
- https://github.com/ffroliva/gflow-cli/tree/db31ab724798ed0a96c42010c56bba1be5f140bf
- https://github.com/ffroliva/gflow-cli/blob/db31ab724798ed0a96c42010c56bba1be5f140bf/pyproject.toml
- https://github.com/ffroliva/gflow-cli/blob/db31ab724798ed0a96c42010c56bba1be5f140bf/KNOWN_ISSUES.md
- https://github.com/ffroliva/gflow-cli/blob/db31ab724798ed0a96c42010c56bba1be5f140bf/docs/LIVE_VERIFICATION_v0.92.0.md
